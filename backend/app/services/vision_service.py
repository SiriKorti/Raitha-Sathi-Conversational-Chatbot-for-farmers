"""
vision_service.py — Isolated Plant Disease & Crop Health Visual Diagnosis Service

WHAT IT DOES:
Provides visual diagnosis of plant diseases, pests, nutrient deficiencies,
and environmental stress from uploaded crop/leaf images using the Google GenAI SDK.

KEY GUARANTEES & ISOLATION:
- Strictly ISOLATED: Does NOT use or modify GeminiClient, ResponseGenerator, Retriever, FAISS, or /api/chat.
- In-memory processing: Uploaded image bytes are verified and transmitted transiently in-memory with zero disk persistence.
- Safe qualitative confidence: Returns only HIGH, MEDIUM, LOW, or UNCERTAIN (never fabricated percentages).
- Conservative agricultural guidance: Recommends label compliance and local KVK / agricultural officer verification.
"""

import io
import json
import re
from typing import Optional, Dict, Any, List
from PIL import Image

from app.config import settings
from app.utils.logger import logger

# Maximum allowed upload size: 10 MB
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

VALID_CATEGORIES = {"disease", "pest", "nutrient", "environmental", "other", "uncertain"}
VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW", "UNCERTAIN"}


class VisionValidationError(Exception):
    """Raised when uploaded image fails format, size, or header validation."""
    pass


class VisionServiceError(Exception):
    """Raised when visual diagnosis processing or model interaction fails."""
    pass


class VisionService:
    """
    Independent service for visual crop diagnosis using Google GenAI.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL

    def validate_image(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Validates image size, MIME type, and binary header/structure using PIL.
        
        Returns:
            Normalized MIME type (e.g. 'image/jpeg').
            
        Raises:
            VisionValidationError if image is invalid, unsupported, or exceeds size limit.
        """
        if not image_bytes:
            raise VisionValidationError("No image data provided.")

        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise VisionValidationError(
                f"Image size ({len(image_bytes)} bytes) exceeds the maximum limit of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        norm_mime = mime_type.lower().strip() if mime_type else ""
        if norm_mime not in ALLOWED_MIME_TYPES:
            raise VisionValidationError(
                f"Unsupported image type '{norm_mime}'. Allowed formats are JPEG, PNG, and WebP."
            )

        # Inspect actual image header & structure via PIL
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
                img_format = (img.format or "").upper()
                expected_format = ALLOWED_MIME_TYPES[norm_mime]
                if img_format != expected_format and not (img_format == "JPEG" and expected_format == "JPEG"):
                    raise VisionValidationError(
                        f"Image header format '{img_format}' does not match reported MIME type '{norm_mime}'."
                    )
        except Exception as e:
            if isinstance(e, VisionValidationError):
                raise
            raise VisionValidationError(f"Corrupt or invalid image content: {str(e)}")

        return "image/jpeg" if norm_mime == "image/jpg" else norm_mime

    def _build_prompt(
        self,
        crop_name: Optional[str],
        symptoms: Optional[str],
        language: str = "kn",
    ) -> str:
        """
        Builds the structured visual diagnosis instruction prompt for Gemini.
        Supports both Kannada ('kn') and English ('en').
        """
        crop_context = f"Reported Crop: {crop_name.strip()}" if crop_name and crop_name.strip() else "Reported Crop: Not specified"
        symptom_context = f"Reported Symptoms / Context: {symptoms.strip()}" if symptoms and symptoms.strip() else "Reported Symptoms: None provided"

        is_kannada = str(language or "kn").lower().strip().startswith("kn")

        if is_kannada:
            lang_instructions = """LANGUAGE REQUIREMENT (CRITICAL - HIGHEST PRIORITY):
The farmer is using the application in KANNADA (ಕನ್ನಡ).
You MUST write all descriptive textual fields ('problem', 'observations', 'possible_causes', 'management', and 'warning') entirely in natural, fluent, and accurate KANNADA (ಕನ್ನಡ ಲಿಪಿಯಲ್ಲಿ).
- 'problem': Provide the Kannada disease/pest/condition name first, with the common English/scientific name in brackets (e.g., 'ಕಡಲೆಕಾಯಿ ಟಿಕ್ಕಾ ರೋಗ / ಎಲೆ ಚುಕ್ಕೆ ರೋಗ (Tikka Leaf Spot / Early & Late Leaf Spot)').
- 'observations': Each bullet point MUST be written in clear Kannada describing the symptoms visible in the photograph (e.g. 'ಎಲೆಗಳ ಮೇಲೆ ಕಂದು ಅಥವಾ ಕಪ್ಪು ಬಣ್ಣದ ದುಂಡಗಿನ ಚುಕ್ಕೆಗಳು ಕಂಡುಬರುತ್ತಿವೆ.').
- 'possible_causes': Each bullet point MUST be written in Kannada explaining the pathogen (fungus/bacteria/pest) or environmental factor.
- 'management': Each practical action step, biological control, and chemical dosage MUST be written in Kannada (you may mention chemical names in brackets e.g., 'ಮ್ಯಾಂಕೋಜೆಬ್ (Mancozeb) ಅಥವಾ ಕಾರ್ಬೆಂಡಾಜಿಮ್ (Carbendazim)').
- 'warning': MUST be in Kannada: 'ಮುನ್ನೆಚ್ಚರಿಕೆ & ಸಲಹೆ: ಎಐ ಆಧಾರಿತ ರೋಗ ನಿರ್ಣಯವು ಕೇವಲ ಪ್ರಾಥಮಿಕ ಸಲಹೆಯಾಗಿದೆ. ಕೀಟನಾಶಕ ಅಥವಾ ಶಿಲೀಂಧ್ರನಾಶಕ ಸಿಂಪಡಿಸುವ ಮುನ್ನ ಸಮೀಪದ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರ ಅಥವಾ ಕೃಷಿ ಅಧಿಕಾರಿಯೊಂದಿಗೆ ದೃಢೀಕರಿಸಿ.'

NOTE: The JSON structure keys ('problem', 'category', 'confidence', 'observations', 'possible_causes', 'management', 'warning') MUST remain in English.
The values of 'category' MUST be one of: "disease", "pest", "nutrient", "environmental", "other", "uncertain".
The values of 'confidence' MUST be one of: "HIGH", "MEDIUM", "LOW", "UNCERTAIN".
All user-facing descriptive texts within the lists/strings MUST BE IN KANNADA."""
        else:
            lang_instructions = """LANGUAGE REQUIREMENT:
The user is using the application in ENGLISH.
Write all descriptive textual fields ('problem', 'observations', 'possible_causes', 'management', and 'warning') in clear, professional, and practical English."""

        return f"""You are an expert plant pathologist and agricultural diagnostic assistant for Indian farmers.
Analyze the provided crop/plant image carefully and generate a structured diagnosis.

Context Provided by Farmer:
- {crop_context}
- {symptom_context}

{lang_instructions}

Diagnostic Rules & Guidelines:
1. Examine visible symptoms on leaves, stems, fruits, or roots (e.g., lesions, discoloration, wilting, pest presence, chlorosis, necrosis).
2. Distinguish between disease, pest damage, nutrient deficiency, environmental stress, or other issues.
3. If the image is blurry, out of focus, poorly lit, distant, non-plant, or lacks clear diagnostic signs, you MUST set category to "uncertain" and confidence to "UNCERTAIN". Do NOT hallucinate or guess a diagnosis when visual evidence is insufficient.
4. Confidence must be strictly one of: "HIGH", "MEDIUM", "LOW", or "UNCERTAIN". Never use percentages or numbers.
5. Provide observable visual evidence under "observations" (what is directly seen in the image).
6. Provide likely causes under "possible_causes".
7. Provide safe, practical management advice under "management":
   - Emphasize cultural, sanitation, and biological practices first.
   - If chemical pesticides/fungicides are mentioned, explicitly state to follow product label guidelines and local safety norms.
   - State that severe or high-impact conditions should be confirmed with a local Agricultural Officer / Krishi Vigyan Kendra (KVK) expert before major chemical application.
8. Distinguish clearly between visual observation and diagnostic inference.

Return ONLY a valid JSON object matching this exact structure:
{{
  "problem": "{'ಕನ್ನಡದಲ್ಲಿ ರೋಗದ ಹೆಸರು (English Name)' if is_kannada else 'Name of likely disease / pest / nutrient deficiency'}",
  "category": "disease" | "pest" | "nutrient" | "environmental" | "other" | "uncertain",
  "confidence": "HIGH" | "MEDIUM" | "LOW" | "UNCERTAIN",
  "observations": [
    "{'ಫೋಟೋದಲ್ಲಿ ಕಂಡುಬರುವ ಸ್ಪಷ್ಟ ಲಕ್ಷಣ 1' if is_kannada else 'Observable symptom 1 seen directly on the plant'}",
    "{'ಲಕ್ಷಣ 2' if is_kannada else 'Observable symptom 2'}"
  ],
  "possible_causes": [
    "{'ಸಂಭಾವ್ಯ ಕಾರಣ ಅಥವಾ ಶಿಲೀಂಧ್ರ/ರೋಗಾಣು 1' if is_kannada else 'Potential pathogen / pest / physiological reason 1'}",
    "{'ಕಾರಣ 2' if is_kannada else 'Potential contributing factor 2'}"
  ],
  "management": [
    "{'ನಿರ್ವಹಣಾ ಕ್ರಮ 1' if is_kannada else 'Practical cultural or control step 1'}",
    "{'ಶಿಫಾರಸು ಮಾಡಿದ ನಿಯಂತ್ರಣ ಕ್ರಮ 2' if is_kannada else 'Recommended sanitation / organic / preventive step 2'}",
    "{'ಹೆಚ್ಚಿನ ವಿವರಕ್ಕೆ ಸಮೀಪದ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ' if is_kannada else 'Consult local KVK or agricultural extension officer for specific dosage recommendations'}"
  ],
  "warning": "{'ಮುನ್ನೆಚ್ಚರಿಕೆ & ಸಲಹೆ: ಎಐ ಆಧಾರಿತ ರೋಗ ನಿರ್ಣಯವು ಪ್ರಾಥಮಿಕ ಸಲಹೆಯಾಗಿದೆ. ರಾಸಾಯನಿಕ ಸಿಂಪಡಿಸುವ ಮುನ್ನ ಕೃಷಿ ಅಧಿಕಾರಿಯೊಂದಿಗೆ ದೃಢೀಕರಿಸಿ.' if is_kannada else 'Visual AI diagnosis is an advisory tool. Always verify with your local agricultural officer or KVK before purchasing or spraying chemicals.'}"
}}
"""

    def _parse_model_response(self, text: str) -> Dict[str, Any]:
        """
        Safely extracts and validates structured JSON diagnosis from model output.
        """
        if not text or not text.strip():
            raise VisionServiceError("Model returned an empty response.")

        clean_text = text.strip()
        # Remove Markdown JSON fences if present
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"\s*```$", "", clean_text)
            clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Attempt regex extraction if extra text surrounds JSON
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception as e:
                    raise VisionServiceError(f"Failed to parse diagnosis JSON: {str(e)}")
            else:
                raise VisionServiceError("Model response did not contain valid JSON.")

        if not isinstance(data, dict):
            raise VisionServiceError("Diagnosis response root is not an object.")

        # Normalize and validate fields (with defensive mapping for Kannada terms)
        category_raw = str(data.get("category", "uncertain")).lower().strip()
        category_map = {
            "disease": "disease",
            "fungal": "disease",
            "bacterial": "disease",
            "viral": "disease",
            "ರೋಗ": "disease",
            "ಶಿಲೀಂಧ್ರ": "disease",
            "ಬ್ಯಾಕ್ಟೀರಿಯಾ": "disease",
            "pest": "pest",
            "insect": "pest",
            "ಕೀಟ": "pest",
            "ಕೀಟ ಬಾಧೆ": "pest",
            "nutrient": "nutrient",
            "deficiency": "nutrient",
            "ಪೋಷಕಾಂಶ": "nutrient",
            "ಪೋಷಕಾಂಶ ಕೊರತೆ": "nutrient",
            "environmental": "environmental",
            "weather": "environmental",
            "ಪರಿಸರ": "environmental",
            "ಪರಿಸರ ಒತ್ತಡ": "environmental",
            "other": "other",
            "ಇತರೆ": "other",
            "uncertain": "uncertain",
            "ಅನಿಶ್ಚಿತ": "uncertain",
            "ಅಸ್ಪಷ್ಟ": "uncertain",
        }
        category = category_map.get(category_raw, category_raw if category_raw in VALID_CATEGORIES else "other")

        confidence_raw = str(data.get("confidence", "UNCERTAIN")).upper().strip()
        conf_map = {
            "HIGH": "HIGH", "ಹೆಚ್ಚು": "HIGH", "ಉನ್ನತ": "HIGH",
            "MEDIUM": "MEDIUM", "MODERATE": "MEDIUM", "ಮಧ್ಯಮ": "MEDIUM",
            "LOW": "LOW", "ಕಡಿಮೆ": "LOW",
            "UNCERTAIN": "UNCERTAIN", "ಅನಿಶ್ಚಿತ": "UNCERTAIN",
        }
        confidence = conf_map.get(confidence_raw, confidence_raw if confidence_raw in VALID_CONFIDENCE_LEVELS else "UNCERTAIN")

        observations = data.get("observations", [])
        if not isinstance(observations, list):
            observations = [str(observations)] if observations else []
        observations = [str(item).strip() for item in observations if str(item).strip()]

        possible_causes = data.get("possible_causes", [])
        if not isinstance(possible_causes, list):
            possible_causes = [str(possible_causes)] if possible_causes else []
        possible_causes = [str(item).strip() for item in possible_causes if str(item).strip()]

        management = data.get("management", [])
        if not isinstance(management, list):
            management = [str(management)] if management else []
        management = [str(item).strip() for item in management if str(item).strip()]

        problem = str(data.get("problem", "Diagnosis inconclusive")).strip()
        warning = str(
            data.get(
                "warning",
                "Visual AI diagnosis is an advisory tool. Always verify with your local agricultural officer or KVK before chemical application."
            )
        ).strip()

        return {
            "problem": problem or "Diagnosis inconclusive",
            "category": category,
            "confidence": confidence,
            "observations": observations,
            "possible_causes": possible_causes,
            "management": management,
            "warning": warning,
        }

    def diagnose_plant_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        crop_name: Optional[str] = None,
        symptoms: Optional[str] = None,
        language: str = "kn",
    ) -> Dict[str, Any]:
        """
        Executes end-to-end visual diagnosis for an uploaded image.
        
        Args:
            image_bytes: Raw binary image payload.
            mime_type: Uploaded content MIME type.
            crop_name: Optional farmer-provided crop name.
            symptoms: Optional farmer-provided symptom description.
            language: Target language ('kn' for Kannada, 'en' for English).
            
        Returns:
            Structured diagnosis response dict.
        """
        # 1. Validate image format, size, and header
        validated_mime = self.validate_image(image_bytes, mime_type)

        if not self._api_key:
            raise VisionServiceError("Gemini API key is not configured.")

        # 2. Call Google GenAI SDK
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)
            prompt = self._build_prompt(crop_name, symptoms, language=language)

            logger.info("Executing isolated visual diagnosis with model {model} (lang={lang})...", model=self._model, lang=language)

            response = client.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=validated_mime,
                    ),
                    prompt,
                ],
            )

            raw_text = response.text if response and response.text else ""
        except Exception as e:
            logger.error("Visual diagnosis API request failed: {e}", e=str(e))
            raise VisionServiceError(f"Diagnostic analysis failed: {str(e)}")

        # 3. Parse and structure response
        parsed_diagnosis = self._parse_model_response(raw_text)

        return {
            "success": True,
            "diagnosis": parsed_diagnosis,
            "crop": (crop_name or "").strip(),
            "provider": "gemini",
            "model": self._model,
        }


# Singleton instance for route injection
vision_service = VisionService()
