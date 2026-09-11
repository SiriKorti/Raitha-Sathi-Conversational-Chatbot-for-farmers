"""
diagnosis.py — Visual Crop Health Diagnosis API Route

WHAT IT DOES:
Exposes HTTP POST endpoint for plant disease and crop health visual diagnosis.
Receives multipart form image upload and optional context, delegates to isolated VisionService,
and returns structured diagnostic insights.

KEY GUARANTEES:
- Strictly ISOLATED from /api/chat, ResponseGenerator, GeminiClient, Retriever, FAISS.
- Zero permanent disk storage of uploaded farmer images.
- Validates MIME and image header integrity.
"""

from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from pydantic import BaseModel

from app.services.vision_service import (
    vision_service,
    VisionValidationError,
    VisionServiceError,
)
from app.utils.logger import logger

router = APIRouter()


@router.post(
    "/diagnose",
    summary="Diagnose plant disease / health from uploaded image",
    description="Accepts an image of a plant/leaf, performs AI visual inspection, and returns structured diagnosis.",
)
async def diagnose_crop_image(
    image: UploadFile = File(..., description="Crop/plant image (JPEG, PNG, or WebP)"),
    crop_name: Optional[str] = Form(None, description="Optional name of the crop"),
    symptoms: Optional[str] = Form(None, description="Optional description of symptoms or context"),
    language: Optional[str] = Form("kn", description="Target language ('kn' for Kannada, 'en' for English)"),
):
    """
    Diagnoses crop health/disease from an uploaded image in memory.
    """
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An image file is required for visual diagnosis.",
        )

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error("Failed to read uploaded image bytes: {e}", e=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded image file.",
        )

    content_type = image.content_type or ""

    try:
        result = vision_service.diagnose_plant_image(
            image_bytes=image_bytes,
            mime_type=content_type,
            crop_name=crop_name,
            symptoms=symptoms,
            language=language or "kn",
        )
        return result
    except VisionValidationError as ve:
        logger.warning("Visual diagnosis validation rejected: {e}", e=str(ve))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except VisionServiceError as se:
        logger.error("Visual diagnosis service error: {e}", e=str(se))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visual diagnosis failed: {str(se)}",
        )
    except Exception as e:
        logger.error("Unexpected error during visual diagnosis: {e}", e=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the image. Please try again.",
        )
