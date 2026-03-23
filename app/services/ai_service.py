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
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.core.insforge_client import insforge
from app.core.cache import cache
import pytesseract

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

from app.core.encryption import encrypt_value, decrypt_value, DecryptionError

def encrypt_data(data: str) -> str:
    """Helper for AI service to encrypt extracted PHI."""
    return encrypt_value(data)

def decrypt_data(encrypted_data_str: str) -> str:
    """Helper for AI service to decrypt PHI. Hard-fails on error."""
    return decrypt_value(encrypted_data_str)

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
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def optimize_image(self, image_path: str, max_size=(1024, 1024), quality=80) -> bytes:
        """Compress and resize image to reduce OCR processing time using non-blocking threads."""
        try:
            # Wrap blocking PIL calls in a thread
            def _sync_optimize():
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                return img_byte_arr.getvalue()

            return await asyncio.to_thread(_sync_optimize)
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

    async def _call_anthropic(self, model: str, prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
        if not self.anthropic_key: return ""
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        content = []
        if image_bytes:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode('utf-8')
                }
            })
        
        content.append({"type": "text", "text": prompt})
        
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": content}]
        }

        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return ""

    async def _call_sarvam(self, text: str, target_language: str) -> str:
        """Call Sarvam AI for regional language translation (Indian languages)."""
        if not self.sarvam_key: return text
        
        url = "https://api.sarvam.ai/translate"
        headers = {"api-subscription-key": self.sarvam_key, "Content-Type": "application/json"}
        payload = {
            "input": text,
            "source_language_code": "en-IN",
            "target_language_code": target_language,
            "speaker_gender": "Female"
        }
        
        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json().get("translated_text", text)
        except Exception as e:
            logger.error(f"Sarvam Translation failed: {e}")
            return text

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

    async def _call_insforge_ai(self, model: str, prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
        """Call InsForge's OpenAI-compatible AI endpoint."""
        url = f"{self.base_url}/api/ai/chat/completion"
        headers = {
            "Authorization": f"Bearer {self.anon_key}",
            "apikey": self.anon_key,
            "Content-Type": "application/json"
        }
        
        if image_bytes:
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"}}
            ]
        else:
            content = prompt

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1024,
            "stream": False
        }
        if force_json:
            payload["force_json"] = True

        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("text", "").strip()
            if not content and "choices" in data:
                content = data["choices"][0]["message"]["content"].strip()
            return content
        except Exception as e:
            logger.error(f"InsForge AI call failed: {e}")
            return ""

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        """Convert audio bytes to text using Groq's Whisper-3."""
        if not self.groq_key: return ""
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.groq_key}"}
        
        # Groq expects a multipart/form-data with the file
        files = {
            "file": ("speech.m4a", audio_bytes, "audio/m4a"),
            "model": (None, "whisper-large-v3"),
        }
        
        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, files=files)
            resp.raise_for_status()
            return resp.json().get("text", "").strip()
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return ""

    async def unified_ai_engine(self, prompt: str, image_bytes: bytes = None, force_json: bool = False, mime_type: str = "image/jpeg", language_code: str = "en") -> str:
        """
        AI Engine with multi-provider failover and Regional Language Support.
        Priority: InsForge (free, reliable) -> Anthropic -> Groq -> Gemini
        """
        if image_bytes:
            # Vision-capable models for image analysis
            providers = [
                ("InsForge Claude", self._call_insforge_ai, "anthropic/claude-sonnet-4.5"),
                ("InsForge GPT-4o-mini", self._call_insforge_ai, "openai/gpt-4o-mini"),
                ("Anthropic", self._call_anthropic, "claude-3-5-sonnet-20240620"),
                ("Groq", self._call_groq, "llama-3.2-11b-vision-preview"),
                ("Gemini", self._call_gemini, "gemini-1.5-flash")
            ]
        else:
            # Text-only models — prioritize speed and quality
            providers = [
                ("InsForge DeepSeek", self._call_insforge_ai, "deepseek/deepseek-v3.2"),
                ("InsForge GPT-4o-mini", self._call_insforge_ai, "openai/gpt-4o-mini"),
                ("InsForge Grok", self._call_insforge_ai, "x-ai/grok-4.1-fast"),
                ("Anthropic", self._call_anthropic, "claude-3-5-sonnet-20240620"),
                ("Groq", self._call_groq, "llama-3.3-70b-versatile"),
                ("Gemini", self._call_gemini, "gemini-1.5-flash")
            ]

        response_text = "SERVICE_UNAVAILABLE"
        for name, func, model in providers:
            try:
                res = await func(model, prompt, image_bytes, mime_type, force_json)
                if res and res not in ["ERROR", "SERVICE_UNAVAILABLE", "MISSING_KEY"] and len(res.strip()) > 5:
                    response_text = res.strip()
                    break # Success!
                logger.warning(f"PROVIDER_FAILURE: {name} returned invalid or empty response.")
            except Exception as e:
                logger.error(f"PROVIDER_CRASH: {name} attempt failed - {str(e)}")
            
            logger.info(f"FAILOVER: Attempting next provider after {name} failure.")

        # --- Regional Language Enhancement (Sarvam) ---
        if response_text != "SERVICE_UNAVAILABLE" and language_code not in ["en", "en-IN"]:
            logger.info(f"TRANSLATING: Response to {language_code} via Sarvam...")
            response_text = await self._call_sarvam(response_text, language_code)

        # 4. Demo Mode Fallback (Offline/No Keys)
        if response_text == "SERVICE_UNAVAILABLE" and os.getenv("DEMO_MODE", "False") == "True":
            logger.info("DEMO_MODE: Returning mock AI response.")
            if force_json:
                return json.dumps({
                    "conditions": [{"name": "Mild Viral Fever", "severity": "mild"}],
                    "medications": [{"name": "Paracetamol 500mg", "dosage": "Twice daily"}],
                    "lab_results": [{"test": "Hemoglobin", "result": "13.5 g/dL"}],
                    "answer": "I've analyzed your report. Everything looks stable."
                })
            return "CLINICAL SUMMARY: Patient presents with symptoms of a viral infection. Rest is recommended."

        return response_text

    async def _call_local_ocr(self, image_bytes: bytes) -> str:
        """Local Tesseract fallback for OCR when all cloud AI services are down."""
        try:
            def _sync_ocr():
                img = Image.open(io.BytesIO(image_bytes))
                return pytesseract.image_to_string(img)
            
            return await asyncio.to_thread(_sync_ocr)
        except Exception as e:
            logger.critical(f"LOCAL_OCR_FAILURE: Tesseract failed - {e}")
            return "OCR_SERVICE_FAILURE"

    async def extract_medical_entities(self, text: str, retries: int = 2) -> MedicalEntities:
        prompt = (
            "Extract medical entities (conditions, medications, lab results) from this text.\n"
            "Return EXCLUSIVELY this JSON:\n"
            "{\"conditions\": [{\"name\": \"...\"}], \"medications\": [{\"name\": \"...\"}], \"lab_results\": [{\"test\": \"...\"}]}\n\n"
            f"Content: {text}"
        )
        for attempt in range(retries):
            res = await self.unified_ai_engine(prompt, force_json=True)
            # Robust Markdown Cleaning
            clean_res = res.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[-1].split("```")[0]
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[-1].split("```")[0]
            clean_res = clean_res.strip()
            
            try:
                return MedicalEntities(**json.loads(clean_res))
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Medical entity parsing attempt {attempt + 1} failed: {e}")
                
        logger.error("Medical entity parsing failed completely after retries.")
        return MedicalEntities()

    async def generate_doctor_summary(self, entities: MedicalEntities, raw_text: str) -> str:
        prompt = (
            f"Write a clinical summary for a physician based on these findings: {entities.model_dump_json()}\n"
            f"Raw text: {raw_text[:1000]}\n"
            "Focus on clinical significance, potential diagnoses, and recommended next steps."
        )
        return await self.unified_ai_engine(prompt)

    async def explain_to_patient(self, entities: MedicalEntities, raw_text: str, language_code: str = "en") -> str:
        """解释给病人 (Explain to patient) - The CHITTI Persona."""
        prompt = (
            "You are 'CHITTI', a friendly, compassionate, and highly intelligent medical assistant for the AHP 2.0 platform.\n"
            f"Your goal is to explain the following medical findings to a patient in language: {language_code}.\n"
            "Guidelines:\n"
            "1. Be extremely warm, reassuring, and use simple language (no jargon).\n"
            "2. Address their medical doubts with empathy, like a caring family doctor.\n"
            "3. If the data shows something concerning, be gentle but advise seeing their doctor.\n"
            "4. If the data is normal, celebrate the good health with them!\n"
            f"Entities Found: {entities.model_dump_json()}\n"
            f"Raw Narrative: {raw_text[:500]}\n\n"
            "Return EXCLUSIVELY a JSON object: {\"answer\": \"your explanation here\"}"
        )
        res = await self.unified_ai_engine(prompt, force_json=True, language_code=language_code)
        try:
            # Handle potential JSON markdown wrap from AI
            clean_res = res.strip()
            if clean_res.startswith("```json"): clean_res = clean_res[7:-3]
            elif clean_res.startswith("```"): clean_res = clean_res[3:-3]
            
            return json.loads(clean_res.strip()).get("answer", "I've analyzed your results, and they're ready for your doctor to review.")
        except Exception as e:
            logger.error(f"CHITTI_PARSE_ERROR: {e} | Raw: {res}")
            # Fallback to direct text if translation/JSON failed
            return res if len(res) > 20 else "I'm Chitti! I've analyzed your reports. Please check with your doctor for the next steps."

    async def _get_file_bytes(self, source: str) -> bytes:
        """Helper to get file bytes from either a local path or an S3 object key."""
        # 1. Check if it's an S3 object key (no slashes, or specific pattern)
        if not os.path.isabs(source) and not source.startswith("./") and not source.startswith("../"):
            try:
                client = await self.get_client()
                from app.services.s3_service import INSFORGE_URL, INSFORGE_KEY, BUCKET_NAME
                url = f"{INSFORGE_URL}/api/storage/buckets/{BUCKET_NAME}/objects/{source}"
                
                logger.info(f"Fetching from S3: {url}")
                resp = await client.get(url, headers={"Authorization": f"Bearer {INSFORGE_KEY}"})
                if resp.status_code == 200:
                    return resp.content
                else:
                    logger.error(f"S3 Retrieval failed: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error fetching from S3: {e}")

        # 2. Fallback to local file (or if specifically local)
        try:
            return await asyncio.to_thread(lambda: open(source, "rb").read())
        except Exception as e:
            logger.error(f"Local file retrieval failed for {source}: {e}")
            raise AIServiceError(f"File not found: {source}")

    async def process_medical_document(self, file_source: str, language_code: str = "en") -> dict:
        """Full pipeline: OCR -> Extract Entities -> Parallel Summaries. Handles local paths or S3 keys."""
        logger.info(f"Starting pipeline for {file_source}")
        
        file_bytes = await self._get_file_bytes(file_source)
        
        if file_source.lower().endswith(".txt"):
            ocr_text = file_bytes.decode("utf-8")
            image_bytes = None
        else:
            def _optimize_from_bytes():
                img = Image.open(io.BytesIO(file_bytes))
                if img.mode != 'RGB': img = img.convert('RGB')
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=80)
                return buf.getvalue()

            image_bytes = await asyncio.to_thread(_optimize_from_bytes)
            ocr_text = await self.unified_ai_engine("Perform high-accuracy OCR on this clinical document. Extract all text exactly.", image_bytes)

        if not ocr_text or ocr_text == "SERVICE_UNAVAILABLE":
            logger.error(f"Extraction failed for {file_source}")
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
            "patient_summary": patient_summary,
            "doctor_summary": doctor_summary
        }

    async def get_chat_history(self, user_id: str, conversation_id: str, limit: int = 10, db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """Retrieve last N messages for context. Uses local DB if available, else InsForge."""
        # 1. Check Local DB first if session provided
        if db:
            from sqlalchemy import select
            from app.models import models
            stmt = select(models.Message).where(
                models.Message.user_id == int(user_id),
                models.Message.conversation_id == conversation_id
            ).order_by(models.Message.created_at.asc())
            result = await db.execute(stmt)
            records = result.scalars().all()
            return [{"role": r.role, "content": r.content} for r in records[-limit:]]

        # 2. Check Cache/InsForge (Original Cloud Logic)
        cache_key = f"chat_history:{conversation_id}"
        cached_history = await cache.get(cache_key)
        
        if cached_history:
            return cached_history[-limit:]

        try:
            records = await insforge.get_records("messages", user_id=user_id, conversation_id=conversation_id)
            records.sort(key=lambda x: x.get("created_at", ""), reverse=False)
            full_history = [{"role": m["role"], "content": m["content"]} for m in records]
            await cache.set(cache_key, full_history, expire=300)
            return full_history[-limit:]
        except Exception as e:
            logger.error(f"Failed to fetch chat history: {e}")
            return []

    async def save_chat_message(self, user_id: str, conversation_id: str, role: str, content: str, db: Optional[AsyncSession] = None):
        """Save a message turn to the database (Local or InsForge)."""
        try:
            # 1. Local DB Save
            if db:
                from app.models import models
                msg = models.Message(
                    user_id=int(user_id),
                    conversation_id=conversation_id,
                    role=role,
                    content=content
                )
                db.add(msg)
                await db.commit()

            # 2. InsForge Sync (Optional)
            if os.getenv("DEMO_MODE") != "True":
                data = {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "role": role,
                    "content": content
                }
                await insforge.create_record("messages", data)
            
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")

    async def get_medical_context(self, user_id: str, db: Optional[AsyncSession] = None) -> str:
        """Fetch a summary of the patient's record for AI awareness."""
        if not db:
            return "No clinical context available (DB Connection Missing)."
        
        try:
            from sqlalchemy import select
            from app.models.models import Patient, Condition, Medication, Allergy, MedicalRecord

            # 1. Fetch Patient Profile
            res = await db.execute(select(Patient).where(Patient.user_id == int(user_id)))
            patient = res.scalar_one_or_none()
            if not patient:
                return "No medical profile found for this user."

            # 2. Fetch Conditions, Meds, Allergies
            c_res = await db.execute(select(Condition).where(Condition.patient_id == patient.id))
            m_res = await db.execute(select(Medication).where(Medication.patient_id == patient.id))
            a_res = await db.execute(select(Allergy).where(Allergy.patient_id == patient.id))
            r_res = await db.execute(select(MedicalRecord).where(MedicalRecord.patient_id == patient.id).order_by(MedicalRecord.created_at.desc()).limit(3))

            conditions = [c.name for c in c_res.scalars().all()]
            medications = [f"{m.generic_name} ({m.dosage})" for m in m_res.scalars().all()]
            allergies = [a.allergen for a in a_res.scalars().all()]
            records = [f"{r.type}: {r.patient_summary or 'General'}" for r in r_res.scalars().all()]

            context = (
                f"PATIENT_PROFILE:\n"
                f"- Name/ID: {patient.ahp_id}\n"
                f"- Blood Group: {patient.blood_group}\n"
                f"- Conditions: {', '.join(conditions) or 'None listed'}\n"
                f"- Medications: {', '.join(medications) or 'None listed'}\n"
                f"- Allergies: {', '.join(allergies) or 'None listed'}\n"
                f"- Recent Records: {'; '.join(records) or 'None'}"
            )
            return context
        except Exception as e:
            logger.error(f"Failed to build medical context: {e}")
            return "Error retrieving clinical profile."
    async def chat_with_memory(self, user_id: str, conversation_id: str, user_message: str, image_bytes: bytes = None, audio_bytes: bytes = None, language_code: str = "en-IN", db: Optional[AsyncSession] = None) -> str:
        """Generate a response using clinical context AND conversational memory."""
        
        # 0. Handle Voice if present
        if audio_bytes:
            transcription = await self.speech_to_text(audio_bytes)
            if transcription:
                user_message = f"{user_message} (Transcription: {transcription})"
                logger.info(f"Voice Transcribed: {transcription}")

        # 1. Fetch Medical Context First
        clinical_context = await self.get_medical_context(user_id, db=db)

        # 2. Save the user's message
        await self.save_chat_message(user_id, conversation_id, "user", user_message, db=db)

        # 3. Get conversational history
        history = await self.get_chat_history(user_id, conversation_id, db=db)

        # 4. Premium Personality Prompt
        system_prompt = (
            "You are CHITTI, the High-End Personal Healthcare Companion for the AHP 2.0 Platform.\n\n"
            "YOUR UNIQUE IDENTITY:\n"
            "- You are NOT a generic AI. You are a dedicated partner in the patient's health journey.\n"
            "- You HAVE access to the patient's real-time medical profile provided below.\n"
            "- Your tone is empathetic, elite, and proactive.\n\n"
            f"- IMPORTANT: Please respond in the following language/dialect: {language_code}.\n"
            f"- If language is not English, ensure you maintain the warm 'Chitti' personality while speaking {language_code}.\n\n"
            "OPERATING GUIDELINES:\n"
            "1. CONTEXTUAL AWARENESS: Always check the 'PATIENT_PROFILE' section. If the user asks about their health, use THIS data.\n"
            "2. PROACTIVITY: Don't just answer; suggest health tips based on their profile.\n"
            "3. VISION: If an image is provided, analyze it clinically.\n"
            "4. ELITE STATUS: Introduce yourself as 'CHITTI, your Healthcare Companion' in your first turn or if asked who you are."
        )
        
        formatted_history = ""
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role_label}: {msg['content']}\n"
        
        full_prompt = (
            f"{system_prompt}\n\n"
            f"--- CLINICAL CONTEXT (REAL DATA) ---\n"
            f"{clinical_context}\n\n"
            f"--- CONVERSATION HISTORY ---\n"
            f"{formatted_history}\n"
            f"Assistant:"
        )

        # 5. Generate response
        response = await self.unified_ai_engine(full_prompt, image_bytes=image_bytes, language_code=language_code)

        # 6. Save and Return
        if response and response != "SERVICE_UNAVAILABLE":
            await self.save_chat_message(user_id, conversation_id, "assistant", response, db=db)
            return response
        
        return "I apologize, but I am having trouble connecting to my central medical memory right now."

_ai_service_instance = AsyncAIService()

async def get_ai_service() -> AsyncAIService:
    """Dependency injection wrapper for the AI Service allowing mock overrides during tests."""
    return _ai_service_instance
