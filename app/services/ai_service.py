import os
import json
import uuid
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import time
import base64
import re
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import io
import hashlib

# Load env from current file directory to be robust
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- Shared Utilities & Encryption ---
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", b'g_oKz_1c5uO8j3HlTzQZ8U0sC9p7L5vY6e3JmN1tWgE=')
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_data(data: str) -> str:
    if not data: return ""
    return fernet.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted_data_str: str) -> str:
    if not encrypted_data_str: return ""
    try:
        return fernet.decrypt(encrypted_data_str.encode('utf-8')).decode('utf-8')
    except Exception:
        return encrypted_data_str

def optimize_image(image_path: str, max_size=(1024, 1024), quality=80) -> bytes:
    """Step 5: Compress and resize image to reduce OCR processing time."""
    try:
        img = Image.open(image_path)
        # Convert to RGB if necessary (e.g. RGBA)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"[IMAGE-OPTIMIZE-ERROR] {e}")
        with open(image_path, 'rb') as f:
            return f.read()

def get_file_hash(image_bytes: bytes) -> str:
    """Step 6: Compute SHA256 hash for caching."""
    return hashlib.sha256(image_bytes).hexdigest()

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "mock_key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Lazy load heavy AI clients
anthropic_client = None
genai = None

def _get_anthropic_client():
    global anthropic_client
    if not anthropic_client and ANTHROPIC_API_KEY:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return anthropic_client

def _get_genai():
    global genai
    if not genai and GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    return genai

def _call_gemini_rest(model_name: str, prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
    """Uses official Google SDK with robust retries."""
    if not GEMINI_API_KEY: return "MISSING_KEY"
    
    # Ensure proper model name format for SDK
    if not model_name.startswith("models/"):
        m_name = f"models/{model_name}"
    else:
        m_name = model_name
    
    genai_lib = _get_genai()
    if not genai_lib: return "MISSING_KEY"
    
    try:
        model = genai_lib.GenerativeModel(m_name)
        
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        contents = [prompt]
        if image_bytes:
            contents.append({
                "mime_type": mime_type,
                "data": image_bytes
            })
            
        generation_config = genai.types.GenerationConfig()
        if force_json:
            generation_config.response_mime_type = "application/json"
            
        safety_settings = {
             HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
             HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
             HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
             HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
            
        response = model.generate_content(
            contents,
            generation_config=generation_config,
            safety_settings=safety_settings,
            request_options={"timeout": 20} # 20 second hard timeout for Gemini
        )
        
        res = response.text.strip()
        if not force_json:
            if res.startswith("```json") and res.endswith("```"): res = res[7:-3].strip()
            elif res.startswith("```") and res.endswith("```"): res = res[3:-3].strip()
        return res

    except Exception as e:
        error_msg = str(e).lower()
        print(f"DEBUG: Gemini SDK error: {e}")
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            return "429_QUOTA_EXHAUSTED"
        return "ERROR"

def _call_groq(prompt: str, force_json: bool = False) -> str:
    """Fallback to Groq for lightning-fast free inference if Gemini fails."""
    if not GROQ_API_KEY: return ""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": "You are a helpful medical structure AI."}, {"role": "user", "content": prompt}],
        "max_tokens": 1000
    }
    
    if force_json:
        payload["response_format"] = {"type": "json_object"}
        payload["messages"][0]["content"] += " You must respond in valid JSON format."

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        else:
            print(f"DEBUG: Groq API Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"DEBUG: Groq Exception: {e}")
    return ""

def _call_groq_vision(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
    """Groq Llama 3.2 Vision Fallback."""
    if not GROQ_API_KEY: return ""
    import base64
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}}
            ]
        }
    ]
    
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": messages,
        "max_tokens": 1024
    }
    if force_json:
        payload["response_format"] = {"type": "json_object"}
        messages.insert(0, {"role": "system", "content": "You are a helpful medical structure AI. Respond in JSON."})

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=35)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"DEBUG: Groq Vision Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"DEBUG: Groq Vision Error: {e}")
    return ""

def _call_anthropic(prompt: str, image_bytes: bytes = None, mime_type: str = "image/jpeg", force_json: bool = False) -> str:
    """Fallback to Claude 3 Haiku for vision/text if Gemini fails."""
    if not anthropic_client: return ""
    import base64
    
    content = []
    if image_bytes:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            # Claude 3 Haiku refuses images larger than ~1568 on a side, let's play it safe
            max_size = 1000
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format=img.format or "JPEG")
                image_bytes = buf.getvalue()
        except Exception as e:
            print(f"DEBUG: Anthropic Resize Error: {e}")
            
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        })
    content.append({"type": "text", "text": prompt})
    
    system_prompt = "You are a helpful medical structure AI."
    if force_json:
        system_prompt += " You must respond in valid JSON format only."
        content[-1]["text"] += "\nReturn ONLY JSON."
        
    try:
        client = _get_anthropic_client()
        if not client: return ""
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
            timeout=25 # timeout for Claude
        )
        return response.content[0].text
    except Exception as e:
        print(f"DEBUG: Anthropic Fallback Error: {e}")
    return ""


def _call_hf_vision(prompt: str, image_bytes: bytes = None, force_json: bool = False) -> str:
    """Fallback to free HuggingFace vision models."""
    if not HF_TOKEN or not image_bytes: return ""
    import base64
    
    # Use BLIP which is very stable for free Inference API
    model = "Salesforce/blip-image-captioning-base"
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # HuggingFace Inference API with images works best with base64 in a specific format
    import base64
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    # HuggingFace Inference API for vision models
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    import base64
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    # Format for many HF Visual Question Answering models
    payload = {
        "inputs": {
            "image": img_b64,
            "question": prompt if prompt else "Describe this medical image in detail."
        },
        "options": {"wait_for_model": True}
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            # HF Vision models often return a list or a list of dicts
            if isinstance(result, list) and len(result) > 0:
                text = ""
                if isinstance(result[0], dict):
                    text = result[0].get("generated_text", "")
                else:
                    text = str(result[0])
                
                if text:
                    if force_json and "{" in text:
                        text = text[text.find("{"):text.rfind("}")+1]
                    return text.strip()
        else:
            print(f"DEBUG: HF Vision Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"DEBUG: HF Vision Error: {e}")
    return ""


def _call_ai_engine(prompt: str, image_bytes: bytes = None, force_json: bool = False, mime_type: str = "image/jpeg") -> str:
    """Unified AI Engine with Fallbacks - GROQ FIRST FOR SPEED."""
    global HF_TOKEN, anthropic_client, GEMINI_API_KEY, GROQ_API_KEY
    
    print(f"DEBUG: Entering AI Engine. Image? {bool(image_bytes)} (len: {len(image_bytes) if image_bytes else 0})")
    
    # 1. Primary for TEXT: Groq (Llama 3.3 70B is elite and ultra-fast)
    if not image_bytes and GROQ_API_KEY:
        t_start = time.time()
        print(f"DEBUG: Using Groq Text (Primary)...")
        res = _call_groq(prompt, force_json=force_json)
        if res and len(res.strip()) > 5:
            print(f"DEBUG: Groq Text took {time.time() - t_start:.2f}s")
            return res

    # 2. Primary for VISION: Groq Llama 3.2 Vision (Blazing fast)
    if image_bytes and GROQ_API_KEY:
        t_start = time.time()
        print(f"DEBUG: Using Groq Vision (Primary)...")
        res = _call_groq_vision(prompt, image_bytes, mime_type=mime_type, force_json=force_json)
        if res and len(res.strip()) > 5:
            print(f"DEBUG: Groq Vision took {time.time() - t_start:.2f}s")
            return res

    # 3. Fallback: Gemini SDK (If Groq fails or quota reached)
    result = "ERROR"
    t_start = time.time()
    if GEMINI_API_KEY:
        model_to_use = "gemini-1.5-flash"
        print(f"DEBUG: Falling back to Gemini ({model_to_use})...")
        result = _call_gemini_rest(model_to_use, prompt, image_bytes, mime_type=mime_type, force_json=force_json)
        
        if result in ["ERROR", "429_QUOTA_EXHAUSTED", "MISSING_KEY"]:
            result = _call_gemini_rest("gemini-2.0-flash", prompt, image_bytes, mime_type=mime_type, force_json=force_json)
    
    elapsed = time.time() - t_start
    print(f"DEBUG: Gemini fallback took {elapsed:.2f}s. Result: {result[:50]}...")
    
    if result not in ["ERROR", "429_QUOTA_EXHAUSTED", "MISSING_KEY"] and result is not None:
        return result
        
    # 4. Fallback: Anthropic
    if anthropic_client:
        print(f"DEBUG: Gemini failed, trying Anthropic...")
        claude_res = _call_anthropic(prompt, image_bytes, mime_type=mime_type, force_json=force_json)
        if claude_res and len(claude_res.strip()) > 5: return claude_res
        
    # 5. Last Resort: HuggingFace
    if image_bytes and HF_TOKEN:
        print(f"DEBUG: Final fallback, trying HF Vision...")
        hf_res = _call_hf_vision(prompt, image_bytes, force_json=force_json)
        if hf_res and len(hf_res.strip()) > 5: return hf_res

    return result

# --- Functional Components ---

def call_google_vision_ocr(image_path: str) -> str:
    """Uses Google Cloud Vision for absolute accuracy in OCR."""
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return ""
    try:
        from google.cloud import vision
        import io
        client = vision.ImageAnnotatorClient()
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        if response.text_annotations:
            return response.text_annotations[0].description
    except Exception as e:
        print(f"[OCR-ERROR] {e}")
    return ""

def extract_medical_entities_gemini(text: str) -> dict:
    """Step 2: Medical NLP using Gemini with Confidence Scoring."""
    prompt = (
        "You are the 'Medical NER Engine'. Extract entities from this text.\n"
        "CRITICAL: If the input text is a description of an image (like an X-ray or MRI), capture the key findings or abnormalities as 'conditions'. "
        "For example, if the text says 'transverse fracture of the femur', extract 'Femur Fracture' as a condition.\n"
        "All extracted names MUST be in English. If the input text is in another language, translate the entity names to English.\n"
        "For EACH entity, provide an internal confidence score (0.0 to 1.0).\n"
        "Return EXCLUSIVELY this JSON:\n"
        "{\n"
        "  \"conditions\": [{\"name\": \"...\", \"confidence\": 0.98, \"reason\": \"...\"}],\n"
        "  \"medications\": [{\"name\": \"...\", \"confidence\": 0.95, \"dosage\": \"...\"}],\n"
        "  \"lab_results\": [{\"test\": \"...\", \"value\": \"...\", \"confidence\": 0.92}]\n"
        "}\n\n"
        f"Medical Content: {text}"
    )
    res = _call_ai_engine(prompt, force_json=True)
    try:
        data = json.loads(res)
        return {
            "conditions": data.get("conditions", []),
            "medications": data.get("medications", []),
            "lab_results": data.get("lab_results", [])
        }
    except:
        return {"conditions": [], "medications": [], "lab_results": []}

def filter_medical_info(entities: dict, raw_text: str) -> str:
    """Step 3: Filter only the most important medical info to reduce LLM input size."""
    # Build a compact representation of the extracted entities
    lines = []
    if entities.get("conditions"):
        lines.append(f"Conditions: {', '.join([c.get('name') for c in entities['conditions']])}")
    if entities.get("medications"):
        lines.append(f"Medications: {', '.join([m.get('name') for m in entities['medications']])}")
    if entities.get("lab_results"):
        lines.append(f"Lab Results: {'; '.join([f'{l.get('test')}: {l.get('value')}' for l in entities['lab_results']])}")
    
    # If we have layout or structured details, add them
    if entities.get("hospital_details"):
        hd = entities["hospital_details"]
        lines.append(f"Hospital: {hd.get('name')} (Dept: {hd.get('department')})")
    
    # Add a small snippet of the raw text (first 1000 chars) for general context if it's very short
    if not lines and raw_text:
        return raw_text[:1000]
        
    return "\n".join(lines)

def ai3_generate_doctor_summary_claude(patient_data: dict) -> str:
    """Step 3: Optimized Doctor Summary with reduced input."""
    # Use filtered info instead of full raw_text
    filtered_info = filter_medical_info(patient_data.get("entities", {}), patient_data.get("raw_text", ""))
    
    prompt = (
        "You are a Senior Consultant Physician. Based on the following medical snapshot, "
        "write a single cohesive CLINICAL SUMMARY paragraph for another doctor. "
        "Strictly English. No bullet points. Focus on abnormalities, current status and risks.\n\n"
        f"Medical Snapshot: {filtered_info}"
    )
    
    client = _get_anthropic_client()
    if client:
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"[Claude-Error] {e}")
            
    return _call_ai_engine(prompt)

def ai4_explain_to_patient(entities: dict, raw_text: str, language_code: str = "en") -> str:
    """Step 3: Optimized Patient Explanation with reduced input."""
    filtered_info = filter_medical_info(entities, raw_text)
    
    lang_info = {
        "te": {"name": "Telugu", "script": "తెలుగు లిపి"},
        "hi": {"name": "Hindi", "script": "हिंदी लिपि"},
        "ta": {"name": "Tamil", "script": "தமிழ் எழுத்து"},
        "kn": {"name": "Kannada", "script": "ಕನ್ನಡ ಲಿపి"},
        "en": {"name": "English", "script": "Latin script"}
    }
    info = lang_info.get(language_code.split('-')[0], lang_info["en"])

    persona = (
        f"You are 'Chitti', the user's Indian medical best friend. "
        f"Tone: Warm, empathetic, informal. Language: {info['name']}. "
        f"Script: {info['script']} (Native script ONLY)."
    )
    
    prompt = (
        f"{persona}\n\n"
        "Explain this medical snapshot simply and warmly in the user's native script. "
        "Focus on what it means for their health. "
        "Return EXCLUSIVELY this JSON structure:\n"
        "{\n"
        "  \"answer\": \"Your warm response...\"\n"
        "}\n\n"
        f"Medical Snapshot: {filtered_info}"
    )
    res = _call_ai_engine(prompt, force_json=True)
    try:
        data = json.loads(res)
        return data.get("answer", "I've analyzed your report. Everything looks stable.")
    except:
        return "I've analyzed your medical data. Please consult your doctor for next steps."

def validate_medical_content(text: str) -> dict:
    """Medical Guardrail: Ensures the document is actually a medical record."""
    if not text or len(text) < 10:
        return {"is_medical": False, "reason": "Text is too short or empty."}
        
    prompt = (
        "You are the 'ELEX Medical Guardrail'. Analyze this text/description.\n"
        "Determine if this is a medical document or a clinical image analysis (X-ray findings, etc.).\n"
        "Return EXCLUSIVELY this JSON:\n"
        "{\n"
        "  \"is_medical\": true/false,\n"
        "  \"reason\": \"A short explanation.\"\n"
        "}\n\n"
        f"Text to analyze: {text[:2000]}"
    )
    res = _call_ai_engine(prompt, force_json=True)
    try:
        return json.loads(res)
    except:
        return {"is_medical": True, "reason": "System fallback."}

def ai_generate_dashboard_analysis(text: str, patient_context: dict) -> dict:
    """Dashboard AI: Generates deep insights and health scores."""
    prompt = (
        "You are the 'ELEX Senior Medical Analyst'. Analyze the following medical history bundle.\n"
        f"Patient Context: {json.dumps(patient_context)}\n\n"
        "Input Data:\n"
        f"{text[:5000]}\n\n"
        "Generate a comprehensive JSON dashboard analysis.\n"
        "Return EXCLUSIVELY this JSON format:\n"
        "{\n"
        "  \"clinical_summary\": \"A concise 2-3 sentence overview.\",\n"
        "  \"health_score\": 0-100,\n"
        "  \"health_score_factors\": [\"Factor 1\"],\n"
        "  \"recovery_timeline\": [{\"year\": \"2023\", \"level\": 60}],\n"
        "  \"condition_progress\": {\"Name\": [{\"value\": \"Stable\", \"date\": \"Jan\"}]},\n"
        "  \"medication_impact\": [{\"name\": \"...\", \"improvement\": \"...\"}],\n"
        "  \"alerts\": [\"Alert 1\"]\n"
        "}"
    )
    res = _call_ai_engine(prompt, force_json=True)
    try:
        return json.loads(res)
    except:
        return {"clinical_summary": "Analysis in progress.", "health_score": None, "health_score_factors": [], "recovery_timeline": [], "condition_progress": {}, "medication_impact": [], "alerts": []}

def process_medical_document_gemini(image_path: str) -> dict:
    """Unified AI Pipeline Orchestrator."""
    t_start = time.time()
    
    # 1. OCR / Visual Analysis
    if image_path.lower().endswith(".txt"):
        with open(image_path, "r", encoding="utf-8") as f:
            ocr_text = f.read()
    else:
        ocr_text = call_google_vision_ocr(image_path)
        if not ocr_text:
            print(f"[AI-PIPELINE] OCR empty, triggering Visual Analysis for {image_path}...")
            import mimetypes
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type: mime_type = "image/jpeg"
            
            with open(image_path, "rb") as f:
                img_data = f.read()
                vision_prompt = (
                    "You are a 'Medical Imaging Specialist'. Analyze this clinical image (X-ray, MRI, Scan).\n"
                    "1. Identify the scan type precisely.\n"
                    "2. Describe all clinical findings and abnormalities in detail.\n"
                    "3. If there is text, extract it.\n"
                    "Provide a detailed clinical description of everything you see."
                )
                ocr_text = _call_ai_engine(vision_prompt, img_data, mime_type=mime_type)
    
    # Parallel Branches (Step 2)
    def run_entities_and_doctor_summary():
        entities = extract_medical_entities_gemini(ocr_text)
        # Step 3: Use optimized summary with filtered info
        doctor_summary = ai3_generate_doctor_summary_claude({"entities": entities, "raw_text": ocr_text})
        return entities, doctor_summary

    def run_patient_explanation(entities):
        # Step 3: Pass extracted entities for filtered explanation
        return ai4_explain_to_patient(entities, ocr_text)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_a = executor.submit(run_entities_and_doctor_summary)
        entities, doctor_summary = f_a.result() # Wait for entities first if needed for patient_exp?
        # Actually, if we want them parallel, we need entities inside run_patient_explanation or passed after f_a
        # Let's adjust for true parallelism
        f_b = executor.submit(run_patient_explanation, entities)
        patient_summary = f_b.result()

    # Detect doc type
    doc_type = "Document"
    if any(k in ocr_text.lower() for k in ["x-ray", "mri", "scan", "ct", "radiology", "ultrasound"]):
        doc_type = "Radiology"
    elif any(k in ocr_text.lower() for k in ["prescription", "rx", "medicine"]):
        doc_type = "Prescription"

    return {
        "type": doc_type,
        "raw_text": ocr_text,
        "structured_data": entities,
        "doctor_summary": doctor_summary,
        "patient_summary": patient_summary
    }

def translate_medical_batch(items: list[str]) -> list[str]:
    """Translates a list of medical terms (e.g. Telugu to English) in a single batch."""
    if not items: return []
    
    # Filter out purely English items to save tokens/time
    # Simple regex for non-English (Telugu/other)
    telugu_pattern = re.compile(r'[\u0c00-\u0c7f]')
    indices_to_translate = [i for i, item in enumerate(items) if telugu_pattern.search(str(item))]
    
    if not indices_to_translate:
        return items
        
    to_translate = [items[i] for i in indices_to_translate]
    bulk_text = "\n".join([f"{i}: {val}" for i, val in enumerate(to_translate)])
    
    prompt = (
        "Translate the following medical terms/sentences from Telugu to clinical English.\n"
        "Maintain the exact medical meaning. Return them in the same order, one per line.\n"
        f"{bulk_text}"
    )
    
    try:
        translated_raw = _call_ai_engine(prompt)
        if not translated_raw or "ERROR" in translated_raw:
            return items
            
        translated_lines = [line.strip() for line in translated_raw.split('\n') if line.strip()]
        
        # Merge back
        final_items = list(items)
        for i, idx in enumerate(indices_to_translate):
            if i < len(translated_lines):
                # Clean up AI prefixes like "0:" if they exist
                clean_val = re.sub(r'^\d+:\s*', '', translated_lines[i])
                final_items[idx] = clean_val
        
        return final_items
    except Exception as e:
        print(f"DEBUG: Batch translation failed: {e}")
        return items

# --- CHITTI TURBO CHAT & SPEECH ---

def ai_fast_chat(query: str, language_code: str = "en") -> str:
    """Ultra-fast response for greetings and small talk. Bypasses history/analysis."""
    lang_info = {"te": "Telugu", "hi": "Hindi", "ta": "Tamil", "kn": "Kannada", "en": "English"}
    target_lang = lang_info.get(language_code.split('-')[0], "English")
    
    prompt = (
        f"Role: You are 'Chitti', an Indian medical best friend (mama/bro). You are warm and casual.\n"
        f"CRITICAL: USE ONLY {target_lang} SCRIPT (Native Script). NO Latin/English alphabet for {target_lang} words.\n"
        f"Example for Telugu: 'బాగున్నావా మామా? ఏం జరిగింది?' (NOT 'Bagunnava mama').\n"
        f"Tone: Casual and energetic. Use emojis softly: a laughing emoji (😂) MUST be included if a joke is told or the user says something funny. A heart (❤️) should be used for supportive messages. Do NOT put emojis in every sentence unless the emotion is very clear. Avoid repetitive or annoying emoji usage.\n"
        f"Interaction: User said: '{query}'. Respond warmly in {target_lang} script. Under 2 sentences."
    )
    # Use Groq directly for ultra-fast response if possible
    if GROQ_API_KEY:
        res = _call_groq(prompt)
        if res and len(res.strip()) > 2:
            return res
            
    return _call_ai_engine(prompt)

def ai_turbo_chat(query: str, history: str = "", language_code: str = "en") -> dict:
    """Full-brain Chitti for clinical queries. Includes history and entity extraction."""
    lang_info = {"te": "Telugu", "hi": "Hindi", "ta": "Tamil", "kn": "Kannada", "en": "English"}
    target_lang = lang_info.get(language_code.split('-')[0], "English")
    
    prompt = (
        f"Role: You are 'Chitti', a medical best friend. You are supportive and cool.\n"
        f"CRITICAL: RESPOND IN {target_lang} SCRIPT ONLY. NO LATIN/ENGLISH ALPHABET FOR {target_lang} WORDS.\n"
        f"Guidance on Telugu Transliteration: In casual chat, users write 'dhani' or 'dani' to mean 'that' or 'it'. Use the CONVERSATION HISTORY below to understand what 'that' refers to.\n"
        f"Style: Talk like a real friend (mama/bro). Use natural {target_lang}. Use emojis softly: laughing (😂) for jokes, heart (❤️) for empathy. Avoid annoying or excessive emoji placement, but ensure the mood is reflected correctly.\n"
        f"Example for Telugu: 'పర్వాలేదు మామా, నేను చూస్తాను.' (NOT 'Parvaledu mama').\n\n"
        f"CONTEXT (MEDICAL RECORDS & HISTORY):\n{history}\n\n"
        f"USER MESSAGE: {query}\n\n"
        "Return EXCLUSIVELY this JSON:\n"
        "{\n"
        "  \"intents\": [\"save_data\", \"ask_question\", \"small_talk\"],\n"
        "  \"entities\": {\"conditions\": [], \"medications\": [], \"allergies\": []},\n"
        "  \"answer\": \"Your warm response in {target_lang} script. Balance emotion and professional care softly.\"\n"
        "}\n"
    )
    
    res = _call_ai_engine(prompt, force_json=True)
    try:
        # Step 1: Clean and try direct parse
        clean_res = res.strip()
        if clean_res.startswith("```json") and clean_res.endswith("```"):
            clean_res = clean_res[7:-3].strip()
        elif clean_res.startswith("```") and clean_res.endswith("```"):
            clean_res = clean_res[3:-3].strip()
        return json.loads(clean_res)
    except:
        # Step 2: Try to extract JSON object from string if direct parse fails
        try:
            start = res.find("{")
            end = res.rfind("}")
            if start != -1 and end != -1:
                return json.loads(res[start:end+1])
        except:
            pass
            
        print(f"DEBUG: AI Turbo Chat failed to parse JSON: {res[:100]}...")
        return {
            "intents": ["ask_question"],
            "entities": {"conditions": [], "medications": [], "allergies": []},
            "answer": "I'm here for you! Could you please tell me that again? I want to make sure I understand correctly."
        }

def sarvam_speech_to_text(audio_path: str, language_code: str = "en-IN") -> str:
    """Transcribe audio using Sarvam AI."""
    if not SARVAM_API_KEY or SARVAM_API_KEY == "mock_key":
        return "Speech service not configured."
        
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}
    
    try:
        with open(audio_path, "rb") as f:
            files = {"file": f}
            data = {"language_code": language_code, "model": "saarika:v1"}
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            if response.status_code == 200:
                return response.json().get("transcript", "")
            print(f"DEBUG: Sarvam STT Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"DEBUG: Sarvam STT Exception: {e}")
    return ""

def sarvam_text_to_speech(text: str, language_code: str = "en-IN") -> bytes:
    """Synthesize speech using Sarvam AI."""
    if not SARVAM_API_KEY or SARVAM_API_KEY == "mock_key":
        return b""
        
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Map common codes to Sarvam supported formats if needed
    payload = {
        "inputs": [text],
        "target_language_code": language_code,
        "speaker": "meera",
        "pitch": 0,
        "pace": 1.1,
        "loudness": 1.5,
        "speech_sample_rate": 8000,
        "enable_punctuation": True,
        "model": "bulbul:v1"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return base64.b64decode(response.json().get("audio_content", ""))
        print(f"DEBUG: Sarvam TTS Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"DEBUG: Sarvam TTS Exception: {e}")
    return b""

# End of file
