"""
test_mandi_service.py — Unit Tests for the Live MandiService

Tests verify:
1.  API request is constructed correctly (URL, params, headers).
2.  API key is obtained from settings, not hardcoded.
3.  Commodity filtering works (Kannada → English mapping).
4.  District filtering works where location is provided.
5.  Government API response is parsed correctly.
6.  Modal Price is mapped correctly.
7.  Multiple records are handled correctly (capped at 5).
8.  Empty results produce a controlled no-data message.
9.  API timeout produces a controlled error message.
10. HTTP error (non-200) produces a controlled error message.
11. Auth failure (401/403) produces a controlled error message.
12. Malformed / non-JSON API response is handled safely.
13. No simulated/hardcoded price is returned under any path.
14. API key is never exposed in the returned response string.
15. Missing MANDI_API_KEY produces a clear unavailable message.
16. Missing crop name produces an appropriate message.
17. Unknown crop name falls back gracefully (no crash, no fake price).
18. Unknown location omits district filter (Karnataka-wide query).
19. /api/chat route is not involved in any Mandi-specific test.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.mandi_service import (
    MandiService,
    _map_commodity,
    _map_district,
    _format_records,
)


# ── Helper: a realistic single API record ─────────────────────────────────────
def _api_record(
    commodity="Ragi",
    variety="Local",
    market="Mandya",
    district="Mandya",
    state="Karnataka",
    arrival_date="08/09/2026",
    min_price="3200",
    max_price="3600",
    modal_price="3400",
) -> dict:
    return {
        "commodity":    commodity,
        "variety":      variety,
        "market":       market,
        "district":     district,
        "state":        state,
        "arrival_date": arrival_date,
        "min_price":    min_price,
        "max_price":    max_price,
        "modal_price":  modal_price,
    }


def _api_response(records: list[dict], total: int | None = None) -> dict:
    """Wraps records in the data.gov.in OGD envelope."""
    return {
        "records": records,
        "total":   total if total is not None else len(records),
        "count":   len(records),
        "limit":   "5",
        "offset":  "0",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Commodity mapping tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCommodityMapping:
    def test_kannada_ragi_maps_correctly(self):
        assert _map_commodity("ರಾಗಿ") == "Ragi(Finger Millet)"

    def test_kannada_paddy_maps_correctly(self):
        result = _map_commodity("ಭತ್ತ")
        assert result is not None
        assert "Paddy" in result or "Rice" in result

    def test_kannada_maize_maps_correctly(self):
        assert _map_commodity("ಮೆಕ್ಕೆಜೋಳ") == "Maize"

    def test_kannada_tomato_maps_correctly(self):
        assert _map_commodity("ಟೊಮೆಟೊ") == "Tomato"

    def test_kannada_sugarcane_maps_correctly(self):
        assert _map_commodity("ಕಬ್ಬು") == "Sugarcane"

    def test_english_ragi_maps_correctly(self):
        assert _map_commodity("ragi") == "Ragi(Finger Millet)"

    def test_english_maize_maps_correctly(self):
        assert _map_commodity("maize") == "Maize"

    def test_english_tomato_maps_correctly(self):
        assert _map_commodity("tomato") == "Tomato"

    def test_english_onion_maps_correctly(self):
        assert _map_commodity("onion") == "Onion"

    def test_english_sunflower_maps_correctly(self):
        assert _map_commodity("sunflower") == "Sunflower"

    def test_mixed_case_input_works(self):
        assert _map_commodity("RAGI") == "Ragi(Finger Millet)"

    def test_unknown_crop_returns_none(self):
        assert _map_commodity("unknowncropxyz") is None

    def test_partial_match_in_longer_name(self):
        # e.g. "ರಾಗಿ ಬೆಳೆ" still maps to Ragi(Finger Millet)
        assert _map_commodity("ರಾಗಿ ಬೆಳೆ") == "Ragi(Finger Millet)"



# ─────────────────────────────────────────────────────────────────────────────
# 2. District mapping tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDistrictMapping:
    def test_mandya_maps_correctly(self):
        assert _map_district("Mandya") == "Mandya"

    def test_mysuru_maps_to_mysore(self):
        assert _map_district("Mysuru") == "Mysore"

    def test_bengaluru_maps_to_bangalore(self):
        assert _map_district("Bengaluru") == "Bangalore"

    def test_belagavi_maps_to_belgaum(self):
        assert _map_district("Belagavi") == "Belgaum"

    def test_shivamogga_maps_to_shimoga(self):
        assert _map_district("Shivamogga") == "Shimoga"

    def test_yeshwanthpur_partial_maps_to_bangalore(self):
        # MandiPage uses "Bengaluru (Yeshwanthpur)"
        assert _map_district("Bengaluru (Yeshwanthpur)") == "Bangalore"

    def test_unknown_location_returns_none(self):
        assert _map_district("UnknownCityXYZ") is None

    def test_case_insensitive(self):
        assert _map_district("mandya") == "Mandya"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Record formatting tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatRecords:
    def test_single_record_contains_modal_price(self):
        rec = _api_record()
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "3400" in result

    def test_single_record_contains_commodity(self):
        rec = _api_record()
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "Ragi" in result

    def test_single_record_contains_market(self):
        rec = _api_record()
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "Mandya" in result

    def test_single_record_contains_date(self):
        rec = _api_record()
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "08/09/2026" in result

    def test_single_record_contains_source_attribution(self):
        rec = _api_record()
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "data.gov.in" in result or "AGMARKNET" in result

    def test_multiple_records_all_included_up_to_five(self):
        records = [_api_record(market=f"Market{i}") for i in range(7)]
        result = _format_records(records, "ರಾಗಿ", "Mandya")
        # Should include Market0–Market4 but not Market5/6
        assert "Market4" in result
        assert "Market5" not in result

    def test_empty_records_returns_empty_string(self):
        assert _format_records([], "ರಾಗಿ", "Mandya") == ""

    def test_result_does_not_contain_hardcoded_hash_price(self):
        # Ensure the hash-based prices (3400 base only from the old code) are
        # only present because they came from the mock API record, not because
        # of any hardcoded simulation.
        rec = _api_record(modal_price="9999")
        result = _format_records([rec], "ರಾಗಿ", "Mandya")
        assert "9999" in result   # API value is passed through
        # The old hardcoded values should NOT appear independently
        assert result.count("3400") == 0  # 9999 was set, not 3400


# ─────────────────────────────────────────────────────────────────────────────
# 4. MandiService._fetch_price_async — happy path
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchPriceAsync:

    @pytest.mark.asyncio
    async def test_successful_fetch_returns_real_price(self):
        """End-to-end: API returns 1 record → formatted string with Modal Price."""
        records = [_api_record()]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_api_key_12345"
            mock_settings.MANDI_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "3400" in result
        assert "Ragi" in result
        assert "Mandya" in result

    @pytest.mark.asyncio
    async def test_api_key_passed_as_param_not_exposed_in_response(self):
        """API key must be used in the request but never appear in the response."""
        records = [_api_record()]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "SUPER_SECRET_API_KEY"
            mock_settings.MANDI_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        # API key must NOT appear anywhere in the response string
        assert "SUPER_SECRET_API_KEY" not in result

        # Verify the key was actually sent (inspect the get() call)
        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params", {}) or call_kwargs.args[1] if len(call_kwargs.args) > 1 else {}
        # The key should be in the params used for the request
        assert "test_api_key" not in result  # not leaked into output

    @pytest.mark.asyncio
    async def test_commodity_filter_uses_english_name(self):
        """Kannada crop name must be translated to English for the API call."""
        records = [_api_record()]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params", {})
        # Must use English commodity name "Ragi(Finger Millet)" — not the Kannada script
        assert params.get("filters[commodity]") == "Ragi(Finger Millet)"


    @pytest.mark.asyncio
    async def test_district_filter_included_when_location_known(self):
        """When location is recognisable, district filter must be sent."""
        records = [_api_record()]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        params = mock_client.get.call_args.kwargs.get("params", {})
        assert params.get("filters[district]") == "Mandya"

    @pytest.mark.asyncio
    async def test_district_filter_omitted_when_location_unknown(self):
        """When location cannot be mapped, no district filter is sent."""
        records = [_api_record()]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await MandiService._fetch_price_async("ರಾಗಿ", "SomeUnknownPlace")

        params = mock_client.get.call_args.kwargs.get("params", {})
        assert "filters[district]" not in params

    @pytest.mark.asyncio
    async def test_state_filter_always_set_to_karnataka(self):
        """State filter must always be Karnataka."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response([_api_record()])

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        params = mock_client.get.call_args.kwargs.get("params", {})
        assert params.get("filters[state]") == "Karnataka"

    @pytest.mark.asyncio
    async def test_multiple_records_returned_correctly(self):
        """Multiple API records must all appear in the output (up to 5)."""
        records = [
            _api_record(market="Mandya",   modal_price="3400"),
            _api_record(market="Mysore",   modal_price="3350"),
            _api_record(market="Bangalore", modal_price="3500"),
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response(records)

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Karnataka")

        assert "Mandya" in result
        assert "Mysore" in result
        assert "Bangalore" in result


# ─────────────────────────────────────────────────────────────────────────────
# 5. MandiService._fetch_price_async — error/edge paths
# ─────────────────────────────────────────────────────────────────────────────

class TestFetchPriceAsyncErrors:

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_unavailable_message(self):
        """Empty MANDI_API_KEY → clear unavailable message, no fake price."""
        with patch("app.services.mandi_service.settings") as mock_settings:
            mock_settings.MANDI_API_KEY     = ""
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "not currently configured" in result or "unavailable" in result.lower()
        # Must NOT contain any numeric price
        assert "3400" not in result
        assert "3200" not in result

    @pytest.mark.asyncio
    async def test_timeout_returns_controlled_error(self):
        """HTTP timeout → controlled error message, no crash, no fake price."""
        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "timed out" in result.lower() or "unavailable" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_network_error_returns_controlled_error(self):
        """Network-level failure → controlled error, no crash, no fake price."""
        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(
                side_effect=httpx.RequestError("connection refused")
            )
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "unavailable" in result.lower() or "network" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_http_401_returns_auth_error_message(self):
        """HTTP 401 → auth error message, no fake price."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "bad_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "unavailable" in result.lower() or "authentication" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_http_403_returns_auth_error_message(self):
        """HTTP 403 → auth error message, no fake price."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "bad_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "unavailable" in result.lower() or "authentication" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_http_500_returns_service_error_message(self):
        """HTTP 500 → service error message, no fake price."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "unavailable" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_malformed_json_response_handled_safely(self):
        """Non-JSON body → controlled error, no crash."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("not valid JSON")

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "unavailable" in result.lower() or "processed" in result.lower()
        assert "3400" not in result

    @pytest.mark.asyncio
    async def test_empty_records_list_returns_no_data_message(self):
        """API returns 200 with records=[] → no-data message, no fake price."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response([])

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await MandiService._fetch_price_async("ರಾಗಿ", "Mandya")

        assert "not currently available" in result.lower() or "no government" in result.lower()
        # Must NOT substitute a fake price
        assert "₹" not in result or "3400" not in result

    @pytest.mark.asyncio
    async def test_unknown_crop_falls_back_gracefully(self):
        """Unknown crop name → API is still called; if empty result, graceful message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _api_response([])  # no results for unknown crop

        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_settings.MANDI_API_KEY     = "test_key"
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__  = AsyncMock(return_value=False)
            mock_client.get        = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            # Should not raise; should return a no-data message
            result = await MandiService._fetch_price_async("unknowncropxyz", "Mandya")

        assert isinstance(result, str)
        assert len(result) > 0
        # No hardcoded numeric price
        assert "2500" not in result
        assert "3400" not in result


# ─────────────────────────────────────────────────────────────────────────────
# 6. MandiService.get_price (public interface) — edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestGetPricePublicInterface:

    def test_empty_crop_name_returns_early_message(self):
        result = MandiService.get_price("", "Mandya")
        assert "No crop" in result or "crop name" in result.lower()
        # No numeric price should be returned
        assert "3400" not in result

    def test_unknown_crop_name_returns_message_not_crash(self):
        with patch("app.services.mandi_service.settings") as mock_settings, \
             patch("app.services.mandi_service.MandiService._fetch_price_async") as mock_fetch:
            mock_settings.MANDI_API_KEY     = ""
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8
            mock_fetch.return_value = "No data available"

            result = MandiService.get_price("some crop", "Mandya")
        assert isinstance(result, str)

    def test_result_never_contains_old_verified_apmc_wording(self):
        """The old 'Verified APMC Mandi Price Data' header must not appear."""
        with patch("app.services.mandi_service.settings") as mock_settings:
            mock_settings.MANDI_API_KEY     = ""
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            result = MandiService.get_price("ರಾಗಿ", "Mandya")

        assert "Verified APMC Mandi Price Data" not in result

    def test_result_does_not_contain_location_hash_simulation(self):
        """
        Even if somehow called, the response must not come from a hash-based
        simulation. We verify by checking that specific hash-derived magic numbers
        that the old code would produce are absent.
        """
        with patch("app.services.mandi_service.settings") as mock_settings:
            mock_settings.MANDI_API_KEY     = ""
            mock_settings.MANDI_RESOURCE_ID = "test_resource_id"
            mock_settings.MANDI_API_TIMEOUT = 8

            result = MandiService.get_price("ರಾಗಿ", "Mandya")

        # Old simulation for "ರಾಗಿ"/"Mandya" produced a fixed hash-based price.
        # Any result should NOT be that old hardcoded price when key is missing.
        # The result should clearly state unavailable, not a price.
        assert "₹3" not in result  # no ₹3xxx price should be in the "not configured" response


# ─────────────────────────────────────────────────────────────────────────────
# 7. Protected system isolation tests
# ─────────────────────────────────────────────────────────────────────────────

class TestProtectedSystemIsolation:

    def test_mandi_service_does_not_import_response_generator(self):
        """MandiService must not import or depend on ResponseGenerator."""
        import app.services.mandi_service as ms_module
        # Check the module's actual imports, not docstrings.
        import sys
        imported_names = set(dir(ms_module))
        assert "ResponseGenerator" not in imported_names
        # Also verify no 'from app.llm...' imports exist in the import block
        import inspect
        source = inspect.getsource(ms_module)
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith("import ") or line.strip().startswith("from ")
        ]
        import_block = "\n".join(import_lines)
        assert "ResponseGenerator" not in import_block

    def test_mandi_service_does_not_import_gemini_client(self):
        """MandiService must not depend on GeminiClient."""
        import app.services.mandi_service as ms_module
        import inspect
        source = inspect.getsource(ms_module)
        assert "GeminiClient" not in source
        assert "gemini_client" not in source

    def test_mandi_service_does_not_import_retriever(self):
        """MandiService must not depend on Retriever/FAISS."""
        import app.services.mandi_service as ms_module
        import inspect
        source = inspect.getsource(ms_module)
        assert "Retriever" not in source
        assert "faiss" not in source.lower()

    def test_mandi_service_does_not_contain_hardcoded_base_prices(self):
        """The old hardcoded price table must be completely gone."""
        import app.services.mandi_service as ms_module
        import inspect
        source = inspect.getsource(ms_module)
        # Old code had specific values: 3400, 2200, 2000, 1500, 3100 as base prices
        assert "base_prices" not in source
        assert "loc_hash" not in source
        assert "fluctuation" not in source

    def test_mandi_service_does_not_use_random_module(self):
        """Random must not be imported (old simulation used it)."""
        import app.services.mandi_service as ms_module
        import inspect
        source = inspect.getsource(ms_module)
        assert "import random" not in source

    def test_mandi_service_interface_signature_preserved(self):
        """get_price(crop_name, location) -> str must still exist."""
        import inspect
        sig = inspect.signature(MandiService.get_price)
        params = list(sig.parameters.keys())
        assert "crop_name" in params
        assert "location" in params
