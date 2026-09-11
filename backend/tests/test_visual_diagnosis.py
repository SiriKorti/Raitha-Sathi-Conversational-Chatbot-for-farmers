"""
test_visual_diagnosis.py — Unit and Integration Tests for Visual Diagnosis

Tests:
1. Image validation (JPEG, PNG, WebP accepted; unsupported/corrupted/oversized rejected).
2. VisionService structured response parsing and prompt formatting.
3. Isolated FastAPI endpoint /api/vision/diagnose behavior.
4. Absolute isolation from /api/chat, ResponseGenerator, RAG, and FAISS.
"""

import io
import json
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.vision_service import (
    VisionService,
    VisionValidationError,
    VisionServiceError,
    MAX_IMAGE_SIZE_BYTES,
)

client = TestClient(app)


def _create_test_image_bytes(img_format: str = "JPEG", size=(50, 50), color="green") -> bytes:
    """Helper to generate valid image bytes in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=img_format)
    return buf.getvalue()


# ── 1. Image Validation Tests ──────────────────────────────────────────────────

def test_validate_image_valid_jpeg():
    service = VisionService(api_key="test_key")
    jpeg_bytes = _create_test_image_bytes("JPEG")
    validated_mime = service.validate_image(jpeg_bytes, "image/jpeg")
    assert validated_mime == "image/jpeg"


def test_validate_image_valid_png():
    service = VisionService(api_key="test_key")
    png_bytes = _create_test_image_bytes("PNG")
    validated_mime = service.validate_image(png_bytes, "image/png")
    assert validated_mime == "image/png"


def test_validate_image_valid_webp():
    service = VisionService(api_key="test_key")
    webp_bytes = _create_test_image_bytes("WEBP")
    validated_mime = service.validate_image(webp_bytes, "image/webp")
    assert validated_mime == "image/webp"


def test_validate_image_unsupported_mime():
    service = VisionService(api_key="test_key")
    jpeg_bytes = _create_test_image_bytes("JPEG")
    with pytest.raises(VisionValidationError) as exc:
        service.validate_image(jpeg_bytes, "image/gif")
    assert "Unsupported image type" in str(exc.value)


def test_validate_image_corrupt_content_rejected():
    service = VisionService(api_key="test_key")
    fake_bytes = b"NOT_A_REAL_IMAGE_HEADER_DATA"
    with pytest.raises(VisionValidationError) as exc:
        service.validate_image(fake_bytes, "image/jpeg")
    assert "Corrupt or invalid image content" in str(exc.value)


def test_validate_image_mismatched_mime_and_header():
    service = VisionService(api_key="test_key")
    png_bytes = _create_test_image_bytes("PNG")
    # Sending PNG bytes with image/jpeg header
    with pytest.raises(VisionValidationError) as exc:
        service.validate_image(png_bytes, "image/jpeg")
    assert "does not match reported MIME type" in str(exc.value)


def test_validate_image_oversized_rejected():
    service = VisionService(api_key="test_key")
    # Create mock oversized payload
    oversized_bytes = b"0" * (MAX_IMAGE_SIZE_BYTES + 1024)
    with pytest.raises(VisionValidationError) as exc:
        service.validate_image(oversized_bytes, "image/jpeg")
    assert "exceeds the maximum limit" in str(exc.value)


def test_validate_image_empty_rejected():
    service = VisionService(api_key="test_key")
    with pytest.raises(VisionValidationError) as exc:
        service.validate_image(b"", "image/jpeg")
    assert "No image data provided" in str(exc.value)


# ── 2. Response Parsing & Structuring Tests ────────────────────────────────────

def test_parse_model_response_valid_json():
    service = VisionService(api_key="test_key")
    model_output = json.dumps({
        "problem": "Early Blight",
        "category": "disease",
        "confidence": "HIGH",
        "observations": ["Concentric dark rings on lower leaves", "Yellow halo around spots"],
        "possible_causes": ["Alternaria solani fungal pathogen", "High humidity"],
        "management": ["Remove infected leaves", "Avoid overhead irrigation", "Consult KVK officer"],
        "warning": "Verify with agricultural officer before spraying."
    })
    parsed = service._parse_model_response(model_output)
    assert parsed["problem"] == "Early Blight"
    assert parsed["category"] == "disease"
    assert parsed["confidence"] == "HIGH"
    assert len(parsed["observations"]) == 2
    assert len(parsed["possible_causes"]) == 2
    assert len(parsed["management"]) == 3
    assert "Verify with agricultural officer" in parsed["warning"]


def test_parse_model_response_markdown_codeblock():
    service = VisionService(api_key="test_key")
    raw_markdown = """```json
{
  "problem": "Stem Borer Damage",
  "category": "pest",
  "confidence": "MEDIUM",
  "observations": ["Dead heart symptom in central shoot"],
  "possible_causes": ["Scirpophaga incertulas larvae"],
  "management": ["Install pheromone traps", "Clip leaf tips before transplanting"],
  "warning": "Follow product labels."
}
```"""
    parsed = service._parse_model_response(raw_markdown)
    assert parsed["problem"] == "Stem Borer Damage"
    assert parsed["category"] == "pest"
    assert parsed["confidence"] == "MEDIUM"
    assert len(parsed["observations"]) == 1


def test_parse_model_response_uncertain():
    service = VisionService(api_key="test_key")
    model_output = json.dumps({
        "problem": "Insufficient visual clarity",
        "category": "uncertain",
        "confidence": "UNCERTAIN",
        "observations": ["Image is blurry and distant"],
        "possible_causes": ["Cannot determine from current photo"],
        "management": ["Take a clearer close-up photograph of the leaf in daylight."],
        "warning": "AI cannot reliably diagnose this image."
    })
    parsed = service._parse_model_response(model_output)
    assert parsed["problem"] == "Insufficient visual clarity"
    assert parsed["category"] == "uncertain"
    assert parsed["confidence"] == "UNCERTAIN"


def test_parse_model_response_normalizes_unknown_values():
    service = VisionService(api_key="test_key")
    model_output = json.dumps({
        "problem": "Unknown Spot",
        "category": "alien_invasion",  # invalid category
        "confidence": "95%",           # invalid confidence string
        "observations": "Single string observation",
        "possible_causes": "Single cause",
        "management": "Single management step",
    })
    parsed = service._parse_model_response(model_output)
    assert parsed["category"] == "other"
    assert parsed["confidence"] == "UNCERTAIN"  # Fallback to UNCERTAIN when non-standard
    assert parsed["observations"] == ["Single string observation"]
    assert parsed["possible_causes"] == ["Single cause"]
    assert parsed["management"] == ["Single management step"]


def test_parse_model_response_empty_raises():
    service = VisionService(api_key="test_key")
    with pytest.raises(VisionServiceError):
        service._parse_model_response("")


# ── 3. API Endpoint Integration Tests (/api/vision/diagnose) ──────────────────

@patch("app.services.vision_service.VisionService.diagnose_plant_image")
def test_api_diagnose_success(mock_diagnose):
    mock_diagnose.return_value = {
        "success": True,
        "diagnosis": {
            "problem": "Leaf Blast",
            "category": "disease",
            "confidence": "HIGH",
            "observations": ["Spindle-shaped lesions with grey centers"],
            "possible_causes": ["Magnaporthe oryzae"],
            "management": ["Avoid excessive nitrogen", "Consult local KVK officer"],
            "warning": "Verify with agricultural officer before spraying."
        },
        "crop": "Paddy",
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite",
    }

    jpeg_bytes = _create_test_image_bytes("JPEG")
    files = {"image": ("leaf.jpg", jpeg_bytes, "image/jpeg")}
    data = {"crop_name": "Paddy", "symptoms": "Brown spots on leaf"}

    res = client.post("/api/vision/diagnose", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["crop"] == "Paddy"
    assert res_data["diagnosis"]["problem"] == "Leaf Blast"
    assert res_data["diagnosis"]["confidence"] == "HIGH"
    assert res_data["provider"] == "gemini"


def test_api_diagnose_unsupported_mime():
    jpeg_bytes = _create_test_image_bytes("JPEG")
    files = {"image": ("leaf.gif", jpeg_bytes, "image/gif")}
    res = client.post("/api/vision/diagnose", files=files)
    assert res.status_code == 400
    assert "Unsupported image type" in res.json()["detail"]


def test_api_diagnose_corrupted_file():
    files = {"image": ("leaf.jpg", b"INVALID_BYTES", "image/jpeg")}
    res = client.post("/api/vision/diagnose", files=files)
    assert res.status_code == 400
    assert "Corrupt or invalid image content" in res.json()["detail"]


@patch("app.services.vision_service.VisionService.diagnose_plant_image")
def test_api_diagnose_optional_context_missing_allowed(mock_diagnose):
    mock_diagnose.return_value = {
        "success": True,
        "diagnosis": {
            "problem": "Nitrogen Deficiency",
            "category": "nutrient",
            "confidence": "MEDIUM",
            "observations": ["General yellowing of older leaves"],
            "possible_causes": ["Low soil nitrogen"],
            "management": ["Apply balanced organic compost", "Soil test"],
            "warning": "Consult local extension officer."
        },
        "crop": "",
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite",
    }

    png_bytes = _create_test_image_bytes("PNG")
    files = {"image": ("plant.png", png_bytes, "image/png")}
    # No crop_name or symptoms provided
    res = client.post("/api/vision/diagnose", files=files)
    assert res.status_code == 200
    assert res.json()["diagnosis"]["category"] == "nutrient"


# ── 4. Isolation Tests ─────────────────────────────────────────────────────────

@patch("app.llm.response_generator.ResponseGenerator.generate")
@patch("app.rag.retriever.Retriever.retrieve")
@patch("app.services.vision_service.VisionService.diagnose_plant_image")
def test_diagnosis_does_not_invoke_chat_or_rag(mock_diagnose, mock_retrieve, mock_gen_response):
    """
    Guarantees that invoking the visual diagnosis endpoint NEVER interacts with
    ResponseGenerator, SemanticRetriever, or the chat RAG pipeline.
    """
    mock_diagnose.return_value = {
        "success": True,
        "diagnosis": {
            "problem": "Healthy Crop",
            "category": "other",
            "confidence": "HIGH",
            "observations": ["Green foliage, no spots"],
            "possible_causes": [],
            "management": ["Continue normal maintenance"],
            "warning": "Always verify with local experts."
        },
        "crop": "Tomato",
        "provider": "gemini",
        "model": "gemini-3.1-flash-lite",
    }

    jpeg_bytes = _create_test_image_bytes("JPEG")
    files = {"image": ("tomato.jpg", jpeg_bytes, "image/jpeg")}
    data = {"crop_name": "Tomato"}

    res = client.post("/api/vision/diagnose", files=files, data=data)
    assert res.status_code == 200

    # Verify RAG / Chat were untouched
    mock_retrieve.assert_not_called()
    mock_gen_response.assert_not_called()
