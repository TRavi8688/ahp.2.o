import os
import json
import asyncio
import base64
import hashlib
import io
from datetime import datetime
from typing import List, Optional, Dict, Any

import httpx
from PIL import Image
from pydantic import BaseModel, Field, ValidationError
from cryptography.fernet import Fernet
from app.core.config import settings
from app.core.logging import logger

# --- AI Specific Exceptions ---
class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass

class AIRateLimitError(AIServiceError):
    """Raised when an AI provider rate limits the request."""
    pass

class AIParseError(AIServiceError):
    """Raised when AI response cannot be parsed into the expected format."""
    pass

# --- Encryption Helper ---
# Initializing Fernet with a key from settings. In a real cloud env, this would be from Secret Manager.
try:
    fernet = Fernet(settings.ENCRYPTION_KEY.encode())
except Exception as e:
    logger.critical(f"Failed to initialize encryption: {e}")
    # Fallback to a development key only if explicitly allowed, otherwise fail fast
    if settings.DEBUG:
        fernet = Fernet(Fernet.generate_key())
    else:
        raise

def encrypt_data(data: str) -> str:
    if not data: return ""
    return fernet.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted_data_str: str) -> str:
    if not encrypted_data_str: return ""
    try:
        return fernet.decrypt(encrypted_data_str.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.debug(f"Decryption failed: {e}")
        return encrypted_data_str

# --- Pydantic Models for AI Output Validation ---
class MedicalEntities(BaseModel):
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    lab_results: List[Dict[str, Any]] = Field(default_factory=list)

class AsyncAIService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.hf_token = settings.HF_TOKEN
        self.sarvam_key = settings.SARVAM_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self._client

    async def optimize_image(self, image_path: str, max_size=(1024, 1024), quality=80) -> bytes:
        """Compress and resize image to reduce OCR processing time."""
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            return img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"Image optimization failed for {image_path}: {e}")
            with open(image_path, 'rb') as f:
                return f.read()

    async def _call_gemini(self, model_name: str, prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
        if not self.gemini_key: return "MISSING_KEY"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
        parts = [{"text": prompt}]
        if image_bytes:
            parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode('utf-8')}})
        
        payload = {"contents": [{"parts": parts}]}
        if force_json:
            payload["generationConfig"] = {"response_mime_type": "application/json"}

        client = await self.get_client()
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 429:
                raise AIRateLimitError("Gemini rate limit exceeded")
            resp.raise_for_status()
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return "ERROR"

    async def _call_groq(self, model: str, prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
        if not self.groq_key: return ""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_key}"}
        content = [{"type": "text", "text": prompt}]
        if image_bytes:
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}})
            
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1024
        }
        if force_json:
            payload["response_format"] = {"type": "json_object"}

        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 429:
                raise AIRateLimitError("Groq rate limit exceeded")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return ""

    async def unified_ai_engine(self, prompt: str, image_bytes: bytes = None, force_json: bool = False, mime_type: str = "image/jpeg") -> str:
        """AI Engine with structured fallback and automatic retry logic."""
        # 1. Attempt Groq (Fastest)
        if self.groq_key:
            model = "llama-3.2-11b-vision-preview" if image_bytes else "llama-3.3-70b-versatile"
            try:
                res = await self._call_groq(model, prompt, image_bytes, mime_type, force_json)
                if res and len(res) > 5: return res
            except AIRateLimitError:
                logger.warning("Groq rate limited, falling back to Gemini.")

        # 2. Attempt Gemini (Best Vision)
        if self.gemini_key:
            try:
                res = await self._call_gemini("gemini-1.5-flash", prompt, image_bytes, mime_type, force_json)
                if res not in ["ERROR", "MISSING_KEY"] and len(res) > 5: return res
            except Exception:
                logger.error("Gemini failed during fallback.")

        return "SERVICE_UNAVAILABLE"

    async def extract_medical_entities(self, text: str) -> MedicalEntities:
        prompt = (
            "Extract medical entities (conditions, medications, lab results) from this text.\n"
            "Return EXCLUSIVELY this JSON:\n"
            "{\"conditions\": [{\"name\": \"...\"}], \"medications\": [{\"name\": \"...\"}], \"lab_results\": [{\"test\": \"...\"}]}\n\n"
            f"Content: {text}"
        )
        res = await self.unified_ai_engine(prompt, force_json=True)
        try:
            return MedicalEntities(**json.loads(res))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Medical entity parsing failed: {e}")
            return MedicalEntities()

    async def generate_doctor_summary(self, entities: MedicalEntities, raw_text: str) -> str:
        prompt = (
            f"Write a clinical summary for a physician based on these findings: {entities.model_dump_json()}\n"
            f"Raw text: {raw_text[:1000]}\n"
            "Focus on clinical significance, potential diagnoses, and recommended next steps."
        )
        return await self.unified_ai_engine(prompt)

    async def explain_to_patient(self, entities: MedicalEntities, raw_text: str, language_code: str = "en") -> str:
        prompt = (
            f"Explain these medical findings warmly to a patient in {language_code}.\n"
            f"Entities: {entities.model_dump_json()}\n"
            "Avoid medical jargon and provide reassurance. Return JSON: {\"answer\": \"...\"}"
        )
        res = await self.unified_ai_engine(prompt, force_json=True)
        try:
            return json.loads(res).get("answer", "I've analyzed your results and they are ready for your doctor to review.")
        except Exception:
            return "Analysis complete. Please consult your physician for a full explanation."

    async def process_medical_document(self, file_path: str, language_code: str = "en") -> dict:
        """Full pipeline: OCR -> Extract Entities -> Parallel Summaries."""
        logger.info(f"Starting pipeline for {file_path}")
        
        if file_path.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                ocr_text = f.read()
            image_bytes = None
        else:
            image_bytes = await self.optimize_image(file_path)
            ocr_text = await self.unified_ai_engine("Perform high-accuracy OCR on this clinical document. Extract all text exactly.", image_bytes)

        if not ocr_text or ocr_text == "SERVICE_UNAVAILABLE":
            logger.error(f"Extraction failed for {file_path}")
            return {"error": "OCR failed"}

        entities = await self.extract_medical_entities(ocr_text)
        
        # Parallel generation of summaries
        doctor_task = self.generate_doctor_summary(entities, ocr_text)
        patient_task = self.explain_to_patient(entities, ocr_text, language_code)
        
        doctor_summary, patient_summary = await asyncio.gather(doctor_task, patient_task)
        
        return {
            "type": "Document",
            "raw_text": ocr_text,
            "structured_data": entities.model_dump(),
            "doctor_summary": doctor_summary,
            "patient_summary": patient_summary,
            "processed_at": datetime.now().isoformat()
        }

ai_service = AsyncAIService()
