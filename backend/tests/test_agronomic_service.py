"""
test_agronomic_service.py — Unit Tests for Isolated AgronomicService

Tests all edge cases, structured parsing, numeric validation, range preservation,
and failure modes with mocked GeminiClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.agronomic_service import (
    AgronomicService,
    AgronomicServiceError,
    AgronomicReference,
    GrowthStage,
)
from app.utils.exceptions import LLMConnectionError


@pytest.fixture
def mock_gemini_client():
    client = MagicMock()
    client.generate = AsyncMock()
    return client


# 1. Test Valid Structured Response
@pytest.mark.asyncio
async def test_valid_structured_response(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Ragi",
      "duration_days_min": 105,
      "duration_days_max": 120,
      "growth_stages": [
        {"name": "Germination & Seedling", "start_day": 0, "end_day": 15, "description": "Emergence stage"},
        {"name": "Tillering & Vegetative", "start_day": 16, "end_day": 45, "description": "Stem elongation"},
        {"name": "Flowering & Grain Formation", "start_day": 46, "end_day": 90, "description": "Panicle emergence"},
        {"name": "Maturity & Ripening", "start_day": 91, "end_day": 120, "description": "Grains turn brown"}
      ],
      "source": "UAS Bangalore Package of Practices",
      "notes": "Varies by Kharif vs Rabi season",
      "confidence": "high"
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    result = await service.get_crop_agronomy("Ragi")

    assert isinstance(result, AgronomicReference)
    assert result.crop_name == "Ragi"
    assert result.duration_days_min == 105
    assert result.duration_days_max == 120
    assert len(result.growth_stages) == 4
    assert result.growth_stages[0].name == "Germination & Seedling"
    assert result.growth_stages[0].start_day == 0
    assert result.growth_stages[0].end_day == 15
    assert result.source == "UAS Bangalore Package of Practices"
    assert result.confidence == "high"


# 2. Test Missing Duration (Null values)
@pytest.mark.asyncio
async def test_missing_duration_null_values(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Exotic Crop",
      "duration_days_min": null,
      "duration_days_max": null,
      "growth_stages": [],
      "source": null,
      "notes": "Insufficient regional data",
      "confidence": "low"
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    result = await service.get_crop_agronomy("Exotic Crop")

    assert result.crop_name == "Exotic Crop"
    assert result.duration_days_min is None
    assert result.duration_days_max is None
    assert result.growth_stages == []
    assert result.notes == "Insufficient regional data"


# 3. Test Duration Range (Min and Max preserved separately without averaging)
@pytest.mark.asyncio
async def test_duration_range_preservation(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Paddy",
      "duration_days_min": 90,
      "duration_days_max": 150,
      "growth_stages": [
        {"name": "Nursery", "start_day": 0, "end_day": 25},
        {"name": "Tillering", "start_day": 26, "end_day": 60},
        {"name": "Heading", "start_day": 61, "end_day": 100},
        {"name": "Ripening", "start_day": 101, "end_day": 150}
      ],
      "source": null,
      "notes": "Short-duration vs long-duration varieties",
      "confidence": "medium"
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    result = await service.get_crop_agronomy("Paddy")

    # Min and max must be preserved as distinct values, not averaged to 120
    assert result.duration_days_min == 90
    assert result.duration_days_max == 150
    assert result.duration_days_min != result.duration_days_max


# 4. Test Invalid Duration (Min <= 0 or Max < Min)
@pytest.mark.asyncio
async def test_invalid_duration_negative(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Maize",
      "duration_days_min": -10,
      "duration_days_max": 100,
      "growth_stages": []
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(AgronomicServiceError) as exc_info:
        await service.get_crop_agronomy("Maize")
    assert "duration_days_min must be greater than 0" in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_duration_max_less_than_min(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Maize",
      "duration_days_min": 120,
      "duration_days_max": 90,
      "growth_stages": []
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(AgronomicServiceError) as exc_info:
        await service.get_crop_agronomy("Maize")
    assert "cannot be less than duration_days_min" in str(exc_info.value)


# 5. Test Invalid Stage Boundaries
@pytest.mark.asyncio
async def test_invalid_stage_boundaries(mock_gemini_client):
    mock_gemini_client.generate.return_value = """
    {
      "crop_name": "Cotton",
      "duration_days_min": 150,
      "duration_days_max": 180,
      "growth_stages": [
        {"name": "Stage 1", "start_day": 50, "end_day": 20}
      ]
    }
    """
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(AgronomicServiceError) as exc_info:
        await service.get_crop_agronomy("Cotton")
    assert "'end_day' must be an integer >= start_day" in str(exc_info.value)


# 6. Test Malformed JSON
@pytest.mark.asyncio
async def test_malformed_json(mock_gemini_client):
    mock_gemini_client.generate.return_value = "This is not json at all {broken"
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(AgronomicServiceError):
        await service.get_crop_agronomy("Tomato")


# 7. Test Gemini / API Failure
@pytest.mark.asyncio
async def test_gemini_api_failure(mock_gemini_client):
    mock_gemini_client.generate.side_effect = LLMConnectionError("Network timeout connecting to Gemini API")
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(LLMConnectionError):
        await service.get_crop_agronomy("Wheat")


# 8. Test Missing API Key / Client Unavailable
@pytest.mark.asyncio
async def test_missing_api_key():
    service = AgronomicService(gemini_client=None)
    # Force _client to None as if ConfigurationError occurred
    service._client = None
    with pytest.raises(LLMConnectionError) as exc_info:
        await service.get_crop_agronomy("Sugarcane")
    assert "Gemini client is not available" in str(exc_info.value)


# 9. Test Null / Unknown Agronomic Values (Handles markdown code fences + missing fields)
@pytest.mark.asyncio
async def test_markdown_wrapped_json_response(mock_gemini_client):
    mock_gemini_client.generate.return_value = """```json
    {
      "crop_name": "UnknownWildGrass",
      "duration_days_min": null,
      "duration_days_max": null,
      "growth_stages": [],
      "source": null,
      "notes": "No agronomic data available for wild species",
      "confidence": "unknown"
    }
    ```"""
    service = AgronomicService(gemini_client=mock_gemini_client)
    result = await service.get_crop_agronomy("UnknownWildGrass")

    assert result.crop_name == "UnknownWildGrass"
    assert result.duration_days_min is None
    assert result.duration_days_max is None
    assert result.growth_stages == []
    assert result.confidence == "unknown"


# 10. Test Empty Crop Name
@pytest.mark.asyncio
async def test_empty_crop_name(mock_gemini_client):
    service = AgronomicService(gemini_client=mock_gemini_client)
    with pytest.raises(AgronomicServiceError) as exc_info:
        await service.get_crop_agronomy("   ")
    assert "Crop name must not be empty" in str(exc_info.value)
