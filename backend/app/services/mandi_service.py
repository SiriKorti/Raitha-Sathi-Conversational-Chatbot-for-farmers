"""
mandi_service.py — Live Government Mandi Price Service

WHAT IT DOES:
Fetches real agricultural commodity price data from the Official
Government of India Open Data API (data.gov.in), which sources its
mandi data from AGMARKNET (Directorate of Marketing & Inspection).

API source:
    https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
    Dataset: "Current Daily Price of Various Commodities from Various
              Markets Across India"

Price fields returned by the API per record:
    state, district, market, commodity, variety, grade,
    arrival_date, min_price, max_price, modal_price

Price unit: rupees per quintal (as published by AGMARKNET)

CALLER:
    ResponseGenerator.generate() — called when intent == "market_price"
    Interface: MandiService.get_price(crop_name: str, location: str) -> str

CONFIGURATION REQUIRED (.env):
    MANDI_API_KEY      — free key from https://data.gov.in (register once)
    MANDI_RESOURCE_ID  — pre-set to the correct dataset resource ID
    MANDI_API_TIMEOUT  — request timeout in seconds (default: 8)

ERROR BEHAVIOUR:
    If the API key is missing, times out, or returns no results,
    a clear human-readable "unavailable" message is returned.
    The simulation is NOT reinstated as a fallback under any circumstance.
"""

import asyncio
import httpx
from typing import Optional

from app.config import settings
from app.utils.logger import logger


# ── Commodity name translation table (Kannada / common English → API English) ──
# data.gov.in uses English commodity names as they appear in AGMARKNET records.
# Entries are checked in lowercase; order matters (more specific first).
_COMMODITY_MAP: list[tuple[str, str]] = [
    # Kannada script
    ("ರಾಗಿ",           "Ragi(Finger Millet)"),
    ("ಭತ್ತ",            "Paddy(Common)"),
    ("ಅಕ್ಕಿ",            "Rice"),
    ("ಮೆಕ್ಕೆಜೋಳ",      "Maize"),
    ("ಟೊಮೆಟೊ",         "Tomato"),
    ("ಟೊಮ್ಯಾಟೊ",       "Tomato"),
    ("ಕಬ್ಬು",           "Sugarcane"),
    ("ಅರಿಶಿನ",          "Turmeric"),
    ("ಸೂರ್ಯಕಾಂತಿ",     "Sunflower"),
    ("ಶೇಂಗಾ",           "Groundnut"),
    ("ತೊಗರಿ",           "Tur"),
    ("ಕಡಲೆ",            "Bengal Gram(Gram)(Whole)"),
    ("ಹತ್ತಿ",            "Cotton"),
    ("ಈರುಳ್ಳಿ",          "Onion"),
    ("ಬೆಳ್ಳುಳ್ಳಿ",         "Garlic"),
    ("ಮೆಣಸಿನಕಾಯಿ",     "Green Chilli"),
    ("ಅಡಿಕೆ",            "Arecanut"),
    ("ತೆಂಗು",            "Coconut"),
    ("ಬಾಳೆ",             "Banana"),
    ("ಮಾವು",             "Mango"),
    # Transliterated / English-script Kannada
    ("finger millet",    "Ragi(Finger Millet)"),
    ("ragi",             "Ragi(Finger Millet)"),
    ("bhatta",           "Paddy(Common)"),
    ("paddy",            "Paddy(Common)"),
    ("bhatt",            "Paddy(Common)"),
    ("rice",             "Rice"),
    ("maize",            "Maize"),
    ("mekke joola",      "Maize"),
    ("tomato",           "Tomato"),
    ("sugarcane",        "Sugarcane"),
    ("kabbu",            "Sugarcane"),
    ("turmeric",         "Turmeric"),
    ("arishina",         "Turmeric"),
    ("sunflower",        "Sunflower"),
    ("suryakanthi",      "Sunflower"),
    ("groundnut",        "Groundnut"),
    ("shenga",           "Groundnut"),
    ("tur",              "Tur"),
    ("togari",           "Tur"),
    ("cotton",           "Cotton"),
    ("hatti",            "Cotton"),
    ("onion",            "Onion"),
    ("eerulli",          "Onion"),
    ("garlic",           "Garlic"),
    ("green chilli",     "Green Chilli"),
    ("chilli",           "Green Chilli"),
    ("arecanut",         "Arecanut"),
    ("areca",            "Arecanut"),
    ("adike",            "Arecanut"),
    ("coconut",          "Coconut"),
    ("tengu",            "Coconut"),
    ("banana",           "Banana"),
    ("bale",             "Banana"),
    ("mango",            "Mango"),
    ("maavu",            "Mango"),
    ("wheat",            "Wheat"),
    ("jowar",            "Jowar(Sorghum)"),
    ("joola",            "Jowar(Sorghum)"),
    ("bajra",            "Bajra(Pearl Millet/Cumbu)"),
    ("sajje",            "Bajra(Pearl Millet/Cumbu)"),
]


# ── Karnataka district names as they appear in AGMARKNET records ───────────────
# Normalises common user-facing names to the government's canonical spellings.
_DISTRICT_MAP: dict[str, str] = {
    # English & transliterations
    "mandya":              "Mandya",
    "mysuru":              "Mysore",
    "mysore":              "Mysore",
    "bengaluru":           "Bangalore",
    "bangalore":           "Bangalore",
    "bengaluru urban":     "Bangalore",
    "yeshwanthpur":        "Bangalore",
    "bandipalya":          "Mysore",
    "belagavi":            "Belgaum",
    "belgaum":             "Belgaum",
    "davangere":           "Davangere",
    "davanagere":          "Davangere",
    "hassan":              "Hassan",
    "shivamogga":          "Shimoga",
    "shimoga":             "Shimoga",
    "ballari":             "Bellary",
    "bellary":             "Bellary",
    "kolar":               "Kolar",
    "tumkur":              "Tumkur",
    "tumakuru":            "Tumkur",
    "dharwad":             "Dharwad",
    "hubli":               "Dharwad",
    "bagalkot":            "Bagalkot",
    "raichur":             "Raichur",
    "gadag":               "Gadag",
    "bidar":               "Bidar",
    "vijayapura":          "Bijapur",
    "bijapur":             "Bijapur",
    "chitradurga":         "Chitradurga",
    "chikkamagaluru":      "Chikmagalur",
    "chikmagalur":         "Chikmagalur",
    "kodagu":              "Coorg",
    "coorg":               "Coorg",
    "udupi":               "Udupi",
    "mangaluru":           "Mangalore",
    "mangalore":           "Mangalore",
    "dakshina kannada":    "Dakshina Kannada",
    "uttara kannada":      "Uttar Kannad",
    # Kannada script
    "ಮಂಡ್ಯ":              "Mandya",
    "ಮೈಸೂರು":             "Mysore",
    "ಬೆಂಗಳೂರು":           "Bangalore",
    "ಬೆಳಗಾವಿ":            "Belgaum",
    "ದಾವಣಗೆರೆ":           "Davangere",
    "ಹಾಸನ":               "Hassan",
    "ಶಿವಮೊಗ್ಗ":           "Shimoga",
    "ಬಳ್ಳಾರಿ":             "Bellary",
    "ಕೋಲಾರ":              "Kolar",
    "ತುಮಕೂರು":            "Tumkur",
    "ಧಾರವಾಡ":             "Dharwad",
    "ಹುಬ್ಬಳ್ಳಿ":            "Dharwad",
    "ಬಾಗಲಕೋಟೆ":           "Bagalkot",
    "ರಾಯಚೂರು":            "Raichur",
    "ಗದಗ":                "Gadag",
    "ಬೀದರ್":               "Bidar",
    "ವಿಜಯಪುರ":            "Bijapur",
    "ಚಿತ್ರದುರ್ಗ":          "Chitradurga",
    "ಚಿಕ್ಕಮಗಳೂರು":        "Chikmagalur",
    "ಕೊಡಗು":              "Coorg",
    "ಉಡುಪಿ":              "Udupi",
    "ಮಂಗಳೂರು":            "Mangalore",
}


# ── API base URL ───────────────────────────────────────────────────────────────
_BASE_URL = "https://api.data.gov.in/resource"


def _map_commodity(crop_name: str) -> Optional[str]:
    """
    Translate a crop name (Kannada script, transliterated, or English) to the
    English commodity name used by AGMARKNET / data.gov.in.

    Returns None if no mapping is found.
    """
    lower = crop_name.lower()
    for key, api_name in _COMMODITY_MAP:
        if key.lower() in lower:
            return api_name
    return None


def _map_district(location: str) -> Optional[str]:
    """
    Normalise a user-supplied location string to the AGMARKNET district name.

    Returns None if the location cannot be confidently mapped.
    """
    lower = location.lower().strip()
    # Direct lookup
    if lower in _DISTRICT_MAP:
        return _DISTRICT_MAP[lower]
    # Partial match (e.g. "Mysuru (Bandipalya)" → "Mysore")
    for key, canonical in _DISTRICT_MAP.items():
        if key in lower:
            return canonical
    return None


def _format_records(records: list[dict], crop_name: str, location: str) -> str:
    """
    Format a list of API result records into a readable text block.

    Selection rule: when multiple records are returned, use the Modal Price
    of the first record (typically today's most recent entry for the requested
    commodity/district). All returned records are listed so the LLM formatter
    can present accurate information.
    """
    if not records:
        return ""

    lines = ["Government APMC Market Price Data (Source: data.gov.in / AGMARKNET):"]
    for rec in records[:5]:  # cap at 5 records to keep the response concise
        commodity  = rec.get("commodity", crop_name)
        variety    = rec.get("variety", "")
        market     = rec.get("market", "")
        district   = rec.get("district", location)
        state      = rec.get("state", "Karnataka")
        date       = rec.get("arrival_date", "")
        min_p      = rec.get("min_price", "")
        max_p      = rec.get("max_price", "")
        modal_p    = rec.get("modal_price", "")

        variety_str = f" ({variety})" if variety else ""
        lines.append(
            f"- Commodity: {commodity}{variety_str}"
        )
        lines.append(f"  Market: {market}, {district}, {state}")
        if date:
            lines.append(f"  Arrival Date: {date}")
        if modal_p:
            lines.append(f"  Modal Price: ₹{modal_p} per Quintal")
        if min_p and max_p:
            lines.append(f"  Price Range: ₹{min_p} – ₹{max_p} per Quintal")
        lines.append("")  # blank line between records

    lines.append("(Prices are wholesale rates in Indian Rupees per Quintal as reported by APMCs.)")
    return "\n".join(lines).strip()


class MandiService:
    """
    Live APMC mandi price service backed by the data.gov.in OGD API.

    The caller interface (get_price) is intentionally kept synchronous-compatible
    via asyncio.run(), so the existing ResponseGenerator call site does not need
    to be changed.  However, the internal HTTP call uses httpx for async support.
    """

    # ------------------------------------------------------------------
    # Public interface (preserves the existing call signature)
    # ------------------------------------------------------------------

    @staticmethod
    def get_price(crop_name: str, location: str) -> str:
        """
        Fetch live mandi price from the government API.

        Args:
            crop_name: Crop name (may be Kannada script, transliterated, or English).
            location:  District / market / city name supplied by the user or dialogue state.

        Returns:
            A formatted text block with real price data, or a clear
            "unavailable" message. NEVER returns simulated/fabricated prices.
        """
        if not crop_name or crop_name.strip().lower() in ("", "unknown crop"):
            return (
                "No crop name was provided. Please specify which crop's "
                "mandi price you'd like to know."
            )

        try:
            # Run the async fetcher in the current event loop if one exists,
            # otherwise create a new loop (handles both async and sync callers).
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We are already inside an async context (FastAPI endpoint).
                    # Use asyncio.ensure_future / run_coroutine_threadsafe is not
                    # needed here because ResponseGenerator already awaits us via
                    # the synchronous wrapper. Schedule as a task on the loop.
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(
                            asyncio.run,
                            MandiService._fetch_price_async(crop_name, location),
                        )
                        return future.result(timeout=settings.MANDI_API_TIMEOUT + 2)
                else:
                    return loop.run_until_complete(
                        MandiService._fetch_price_async(crop_name, location)
                    )
            except RuntimeError:
                return asyncio.run(
                    MandiService._fetch_price_async(crop_name, location)
                )
        except Exception as exc:
            logger.error(
                "MandiService.get_price unexpected error | crop={c} | loc={l} | err={e}",
                c=crop_name, l=location, e=str(exc)
            )
            return (
                "Mandi price information is currently unavailable. "
                "Please check with your nearest APMC office or visit agmarknet.gov.in."
            )

    # ------------------------------------------------------------------
    # Internal async fetcher
    # ------------------------------------------------------------------

    @staticmethod
    async def _fetch_price_async(crop_name: str, location: str) -> str:
        """
        Internal coroutine that performs the HTTP request to data.gov.in.
        All error paths return a human-readable string; none return simulated prices.
        """
        # ── 1. Configuration check ─────────────────────────────────────────────
        api_key     = settings.MANDI_API_KEY
        resource_id = settings.MANDI_RESOURCE_ID

        if not api_key:
            logger.warning(
                "MandiService: MANDI_API_KEY is not configured. "
                "Set it in .env to enable live price lookups."
            )
            return (
                "Live mandi price data is not currently configured for this system. "
                "Please check with your nearest APMC office or visit agmarknet.gov.in "
                "for current market prices."
            )

        if not resource_id:
            logger.error("MandiService: MANDI_RESOURCE_ID is missing from configuration.")
            return (
                "Mandi price data service is misconfigured. "
                "Please contact the system administrator."
            )

        # ── 2. Commodity translation ───────────────────────────────────────────
        api_commodity = _map_commodity(crop_name)
        if not api_commodity:
            logger.warning(
                "MandiService: No commodity mapping for '{c}'. "
                "Attempting lookup with original name.",
                c=crop_name
            )
            # Fall back to the raw name — the API may still find a match.
            api_commodity = crop_name.strip()

        # ── 3. Build request parameters ────────────────────────────────────────
        params: dict = {
            "api-key":    api_key,
            "format":     "json",
            "limit":      "5",
            "filters[commodity]": api_commodity,
            "filters[state]":    "Karnataka",
        }

        # Add district filter only when we can confidently map the location.
        api_district = _map_district(location) if location else None
        if api_district:
            params["filters[district]"] = api_district
            logger.info(
                "MandiService: location='{l}' → district='{d}'",
                l=location, d=api_district
            )
        else:
            logger.info(
                "MandiService: location='{l}' could not be mapped to a district. "
                "Querying Karnataka-wide.",
                l=location
            )

        url = f"{_BASE_URL}/{resource_id}"

        # ── 4. HTTP request ────────────────────────────────────────────────────
        logger.info(
            "MandiService: fetching price | commodity='{c}' | district='{d}'",
            c=api_commodity,
            d=api_district or "Karnataka (all districts)",
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=settings.MANDI_API_TIMEOUT) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException:
            logger.warning(
                "MandiService: request timed out after {t}s | commodity={c}",
                t=settings.MANDI_API_TIMEOUT, c=api_commodity
            )
            return (
                "Mandi price data could not be fetched right now (request timed out). "
                "Please try again in a moment or check agmarknet.gov.in directly."
            )
        except httpx.RequestError as exc:
            logger.error(
                "MandiService: network error | err={e}", e=str(exc)
            )
            return (
                "Mandi price data is temporarily unavailable due to a network issue. "
                "Please try again or check agmarknet.gov.in."
            )

        # ── 5. HTTP response validation ────────────────────────────────────────
        if response.status_code == 401 or response.status_code == 403:
            logger.error(
                "MandiService: API authentication failed (HTTP {s}). "
                "Check that MANDI_API_KEY is valid.",
                s=response.status_code
            )
            return (
                "Mandi price data is currently unavailable (API authentication issue). "
                "Please check agmarknet.gov.in for current market prices."
            )

        if response.status_code != 200:
            logger.error(
                "MandiService: API returned HTTP {s} | commodity={c}",
                s=response.status_code, c=api_commodity
            )
            return (
                "Mandi price data is temporarily unavailable (service error). "
                "Please try again later or check agmarknet.gov.in."
            )

        # ── 6. JSON parsing ────────────────────────────────────────────────────
        try:
            body = response.json()
        except Exception:
            logger.error(
                "MandiService: API returned non-JSON response | commodity={c}",
                c=api_commodity
            )
            return (
                "Mandi price data could not be processed (unexpected response format). "
                "Please check agmarknet.gov.in for current market prices."
            )

        # ── 7. Extract records ─────────────────────────────────────────────────
        records: list[dict] = body.get("records", [])

        # If district-specific search returned no records, fall back to Karnataka-wide
        if not records and api_district:
            logger.info(
                "MandiService: no records for district '{d}'. Trying Karnataka-wide fallback.",
                d=api_district
            )
            state_params = {
                "api-key":    api_key,
                "format":     "json",
                "limit":      "5",
                "filters[commodity]": api_commodity,
                "filters[state]":    "Karnataka",
            }
            try:
                async with httpx.AsyncClient(headers=headers, timeout=settings.MANDI_API_TIMEOUT) as client:
                    fb_resp = await client.get(url, params=state_params)
                    if fb_resp.status_code == 200:
                        records = fb_resp.json().get("records", [])
            except Exception as fb_exc:
                logger.warning("MandiService: Karnataka-wide fallback failed: {e}", e=str(fb_exc))


        if not records:
            loc_str = api_district or "Karnataka"
            logger.info(
                "MandiService: no records found | commodity={c} | district={d}",
                c=api_commodity, d=loc_str
            )
            return (
                f"No government mandi price data is currently available for "
                f"{crop_name} in {loc_str}. "
                f"Data may not have been reported yet for today. "
                f"Please check agmarknet.gov.in or visit your nearest APMC office."
            )

        # ── 8. Format and return ───────────────────────────────────────────────
        formatted = _format_records(records, crop_name, location)
        logger.info(
            "MandiService: successfully fetched {n} record(s) | commodity={c} | district={d}",
            n=len(records), c=api_commodity, d=api_district or "Karnataka-wide"
        )
        return formatted

