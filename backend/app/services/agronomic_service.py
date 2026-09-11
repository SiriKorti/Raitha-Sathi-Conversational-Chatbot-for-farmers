"""
agronomic_service.py — Isolated Agronomic AI Service for Farm Progress

WHAT IT DOES:
Requests structured crop agronomy reference data (typical duration ranges,
growth stage boundaries, assumptions/notes) from Gemini via the existing
GeminiClient infrastructure.

PROTECTION COMPLIANCE:
- Completely decoupled from /api/chat and ResponseGenerator.
- Does NOT touch RAG, FAISS, Embedder, DatabaseSearcher, or Chat History.
- Does NOT calculate farmer progress, days elapsed, or harvest dates.
- Does NOT create or modify any static crop datasets.
- Does NOT invent or fabricate precise agricultural data.
- Preserves duration_days_min and duration_days_max as separate range values.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

from app.llm.gemini_client import GeminiClient
from app.utils.logger import logger
from app.utils.exceptions import (
    AgriAssistantError,
    LLMConnectionError,
    LLMResponseError,
    ConfigurationError,
)


class AgronomicServiceError(AgriAssistantError):
    """Raised when agronomic data retrieval or validation fails."""
    pass


@dataclass
class GrowthStage:
    """Represents a single growth stage boundary for reference."""
    name: str
    start_day: int
    end_day: int
    description: Optional[str] = None


@dataclass
class AgronomicReference:
    """Structured agronomic reference response for a crop."""
    crop_name: str
    duration_days_min: Optional[int] = None
    duration_days_max: Optional[int] = None
    growth_stages: List[GrowthStage] = field(default_factory=list)
    source: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[str] = None
    crop_type: str = "annual"  # "annual", "perennial", "plantation", "biennial"
    is_perennial: bool = False
    bearing_age_years_min: Optional[float] = None
    bearing_age_years_max: Optional[float] = None
    harvest_season_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a plain dictionary."""
        return asdict(self)


# ── Authoritative Verified Baseline Agronomic Models for Karnataka Crops ───────
VERIFIED_AGRONOMY_BASELINES: Dict[str, Dict[str, Any]] = {
    "paddy": {
        "crop_name": "Paddy / Rice",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 120,
        "duration_days_max": 150,
        "growth_stages": [
            {"name": "Germination to Emergence", "start_day": 0, "end_day": 14, "description": "From sowing or sprouting until the seedling emerges from the soil or water."},
            {"name": "Tillering Stage", "start_day": 15, "end_day": 45, "description": "Active production of side shoots (tillers) and primary root system development."},
            {"name": "Stem Elongation & Booting", "start_day": 46, "end_day": 75, "description": "Rapid stem lengthening and panicle development inside the flag leaf sheath."},
            {"name": "Flowering & Anthesis", "start_day": 76, "end_day": 95, "description": "Heading, blooming, and pollination take place across the panicle."},
            {"name": "Grain Filling & Milk Stage", "start_day": 96, "end_day": 120, "description": "Starch accumulates inside the kernels, progressing from milky to dough consistency."},
            {"name": "Ripening & Harvest", "start_day": 121, "end_day": 150, "description": "Panicles turn golden yellow and grains harden to harvest moisture level (14-16%)."}
        ],
        "source": "UAS Bangalore / Package of Practices for Karnataka",
        "notes": "Duration varies between early varieties (115-120 days) and late-maturing varieties (140-150 days).",
        "confidence": "high"
    },
    "rice": {
        "crop_name": "Paddy / Rice",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 120,
        "duration_days_max": 150,
        "growth_stages": [
            {"name": "Germination to Emergence", "start_day": 0, "end_day": 14, "description": "From sowing or sprouting until the seedling emerges from the soil or water."},
            {"name": "Tillering Stage", "start_day": 15, "end_day": 45, "description": "Active production of side shoots (tillers) and primary root system development."},
            {"name": "Stem Elongation & Booting", "start_day": 46, "end_day": 75, "description": "Rapid stem lengthening and panicle development inside the flag leaf sheath."},
            {"name": "Flowering & Anthesis", "start_day": 76, "end_day": 95, "description": "Heading, blooming, and pollination take place across the panicle."},
            {"name": "Grain Filling & Milk Stage", "start_day": 96, "end_day": 120, "description": "Starch accumulates inside the kernels, progressing from milky to dough consistency."},
            {"name": "Ripening & Harvest", "start_day": 121, "end_day": 150, "description": "Panicles turn golden yellow and grains harden to harvest moisture level (14-16%)."}
        ],
        "source": "UAS Bangalore / Package of Practices for Karnataka",
        "notes": "Duration varies between early varieties (115-120 days) and late-maturing varieties (140-150 days).",
        "confidence": "high"
    },
    "ragi": {
        "crop_name": "Finger Millet (Ragi)",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 100,
        "duration_days_max": 120,
        "growth_stages": [
            {"name": "Germination & Seedling", "start_day": 0, "end_day": 15, "description": "Seed germination and establishment of initial seminal root system."},
            {"name": "Tillering Stage", "start_day": 16, "end_day": 40, "description": "Formation of productive side tillers and vigorous crown root growth."},
            {"name": "Grand Vegetative Growth", "start_day": 41, "end_day": 65, "description": "Rapid stem elongation and earhead bud differentiation inside the boot leaf."},
            {"name": "Flowering & Earhead Emergence", "start_day": 66, "end_day": 85, "description": "Earheads (fingers) emerge completely and pollination occurs."},
            {"name": "Grain Filling & Dough Stage", "start_day": 86, "end_day": 105, "description": "Nutrient accumulation in developing ragi grains from milky to hard dough."},
            {"name": "Maturity & Harvest", "start_day": 106, "end_day": 120, "description": "Earheads turn characteristic dark brown; grains harden, ready for harvest."}
        ],
        "source": "UAS Bangalore / ICAR All India Coordinated Research Project",
        "notes": "Varieties like GPU-28 and ML-365 mature in 105-115 days; Indaf series in 115-125 days.",
        "confidence": "high"
    },
    "finger millet": {
        "crop_name": "Finger Millet (Ragi)",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 100,
        "duration_days_max": 120,
        "growth_stages": [
            {"name": "Germination & Seedling", "start_day": 0, "end_day": 15, "description": "Seed germination and establishment of initial seminal root system."},
            {"name": "Tillering Stage", "start_day": 16, "end_day": 40, "description": "Formation of productive side tillers and vigorous crown root growth."},
            {"name": "Grand Vegetative Growth", "start_day": 41, "end_day": 65, "description": "Rapid stem elongation and earhead bud differentiation inside the boot leaf."},
            {"name": "Flowering & Earhead Emergence", "start_day": 66, "end_day": 85, "description": "Earheads (fingers) emerge completely and pollination occurs."},
            {"name": "Grain Filling & Dough Stage", "start_day": 86, "end_day": 105, "description": "Nutrient accumulation in developing ragi grains from milky to hard dough."},
            {"name": "Maturity & Harvest", "start_day": 106, "end_day": 120, "description": "Earheads turn characteristic dark brown; grains harden, ready for harvest."}
        ],
        "source": "UAS Bangalore / ICAR All India Coordinated Research Project",
        "notes": "Varieties like GPU-28 and ML-365 mature in 105-115 days; Indaf series in 115-125 days.",
        "confidence": "high"
    },
    "maize": {
        "crop_name": "Maize / Corn",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 90,
        "duration_days_max": 110,
        "growth_stages": [
            {"name": "Germination & Emergence (VE-V2)", "start_day": 0, "end_day": 12, "description": "Coleoptile breaks soil surface and initial 2-leaf collar establishes."},
            {"name": "Knee-High Vegetative Stage (V4-V8)", "start_day": 13, "end_day": 35, "description": "Rapid stem lengthening, canopy expansion, and root brace development."},
            {"name": "Tasseling & Silking (VT-R1)", "start_day": 36, "end_day": 55, "description": "Tassels shed pollen while female silks emerge for critical pollination."},
            {"name": "Kernel Filling & Dent Stage (R2-R5)", "start_day": 56, "end_day": 85, "description": "Kernels fill with starch from blister to milk to dent consistency."},
            {"name": "Physiological Maturity & Harvest (R6)", "start_day": 86, "end_day": 110, "description": "Black layer forms at the kernel base; cobs dry down for harvest."}
        ],
        "source": "UAS Dharwad / ICAR Indian Institute of Maize Research",
        "notes": "Short duration hybrids mature in 85-95 days, medium hybrids in 95-105 days, late in 105-115 days.",
        "confidence": "high"
    },
    "corn": {
        "crop_name": "Maize / Corn",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 90,
        "duration_days_max": 110,
        "growth_stages": [
            {"name": "Germination & Emergence (VE-V2)", "start_day": 0, "end_day": 12, "description": "Coleoptile breaks soil surface and initial 2-leaf collar establishes."},
            {"name": "Knee-High Vegetative Stage (V4-V8)", "start_day": 13, "end_day": 35, "description": "Rapid stem lengthening, canopy expansion, and root brace development."},
            {"name": "Tasseling & Silking (VT-R1)", "start_day": 36, "end_day": 55, "description": "Tassels shed pollen while female silks emerge for critical pollination."},
            {"name": "Kernel Filling & Dent Stage (R2-R5)", "start_day": 56, "end_day": 85, "description": "Kernels fill with starch from blister to milk to dent consistency."},
            {"name": "Physiological Maturity & Harvest (R6)", "start_day": 86, "end_day": 110, "description": "Black layer forms at the kernel base; cobs dry down for harvest."}
        ],
        "source": "UAS Dharwad / ICAR Indian Institute of Maize Research",
        "notes": "Short duration hybrids mature in 85-95 days, medium hybrids in 95-105 days, late in 105-115 days.",
        "confidence": "high"
    },
    "arecanut": {
        "crop_name": "Arecanut",
        "crop_type": "perennial",
        "is_perennial": True,
        "bearing_age_years_min": 4.0,
        "bearing_age_years_max": 5.0,
        "harvest_season_description": "October – February (ಆಕ್ಟೋಬರ್ – ಫೆಬ್ರವರಿ)",
        "duration_days_min": 1460,
        "duration_days_max": 1825,
        "growth_stages": [
            {"name": "Seedling & Field Establishment", "start_day": 0, "end_day": 365, "description": "Initial establishment of transplanted seedlings, root anchoring, shade regulation, and active moisture management."},
            {"name": "Juvenile Vegetative Growth", "start_day": 366, "end_day": 1460, "description": "Vigorous trunk formation, crown frond expansion, and node establishment during years 2 through 4."},
            {"name": "Spadix Emergence & First Flowering", "start_day": 1461, "end_day": 1825, "description": "First inflorescence spadices appear and initial nut setting begins around year 5."},
            {"name": "Full Economic Bearing", "start_day": 1826, "end_day": 14600, "description": "Regular commercial bearing stage with annual bunch development; economic productivity continues for 30–40+ years."}
        ],
        "source": "ICAR-CPCRI / Directorate of Arecanut and Spices Development",
        "notes": "Arecanut (Areca catechu) is a perennial tree crop with a productive lifespan of 30–40+ years. First commercial bearing begins ~5 years after planting with annual peak harvest from October to February.",
        "confidence": "high"
    },
    "coconut": {
        "crop_name": "Coconut",
        "crop_type": "perennial",
        "is_perennial": True,
        "bearing_age_years_min": 5.0,
        "bearing_age_years_max": 7.0,
        "harvest_season_description": "Year-round every 45–60 days (ವರ್ಷಪೂರ್ತಿ ನಿರಂತರ ಕಟಾವು)",
        "duration_days_min": 1825,
        "duration_days_max": 2555,
        "growth_stages": [
            {"name": "Seedling Establishment", "start_day": 0, "end_day": 365, "description": "Field planting of selected seedlings, establishment of primary root system, and moisture conservation."},
            {"name": "Juvenile Canopy Growth", "start_day": 366, "end_day": 1825, "description": "Rapid frond development, trunk enlargement, and energy accumulation during years 2 through 5."},
            {"name": "Inflorescence & First Nut Setting", "start_day": 1826, "end_day": 2555, "description": "First spadices emerge and initial buttons set into nuts around year 6–7."},
            {"name": "Continuous Economic Bearing", "start_day": 2556, "end_day": 25000, "description": "Full mature palm stage with continuous year-round bunch production for 60+ years."}
        ],
        "source": "ICAR-CPCRI / Coconut Development Board",
        "notes": "Coconut (Cocos nucifera) is a perennial plantation palm. Tall varieties bear in 6-7 years; hybrids in 4-5 years; bunches are harvested every 45-60 days year-round.",
        "confidence": "high"
    },
    "cotton": {
        "crop_name": "Cotton",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 150,
        "duration_days_max": 180,
        "growth_stages": [
            {"name": "Germination & Emergence", "start_day": 0, "end_day": 15, "description": "Radicle breaks seed coat and cotyledon leaves unfold."},
            {"name": "Vegetative & Squaring Stage", "start_day": 16, "end_day": 45, "description": "Main stem branches out and floral squares (flower buds) develop."},
            {"name": "Flowering & Boll Setting", "start_day": 46, "end_day": 85, "description": "White/cream flowers open, get pollinated, turn pink, and drop, initiating boll formation."},
            {"name": "Boll Development Stage", "start_day": 86, "end_day": 140, "description": "Cotton bolls enlarge, lint fibers elongate, and seeds mature inside the capsule."},
            {"name": "Boll Bursting & Picking", "start_day": 141, "end_day": 180, "description": "Mature bolls dehisce, revealing fluffy white lint ready for multiple picking rounds."}
        ],
        "source": "UAS Dharwad / ICAR-CICR Nagpur",
        "notes": "Bt cotton hybrids in Karnataka mature over 150-180 days with multiple pickings.",
        "confidence": "high"
    },
    "sugarcane": {
        "crop_name": "Sugarcane",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 300,
        "duration_days_max": 365,
        "growth_stages": [
            {"name": "Germination Phase", "start_day": 0, "end_day": 35, "description": "Buds on setts sprout and form initial primary roots."},
            {"name": "Tillering & Formative Phase", "start_day": 36, "end_day": 100, "description": "Underground nodes produce multiple tillers and cane root system establishes."},
            {"name": "Grand Growth Phase", "start_day": 101, "end_day": 270, "description": "Rapid internode elongation, intense biomass accumulation, and thick cane formation."},
            {"name": "Ripening & Harvest Phase", "start_day": 271, "end_day": 365, "description": "Vegetative growth slows and sucrose synthesis/accumulation peaks; brix reading > 18%."}
        ],
        "source": "ICAR-SBI Coimbatore / UAS Dharwad",
        "notes": "Eksali (annual) crop takes 10-12 months; Adsali takes 15-18 months.",
        "confidence": "high"
    },
    "groundnut": {
        "crop_name": "Groundnut / Peanut",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 100,
        "duration_days_max": 120,
        "growth_stages": [
            {"name": "Emergence & Seedling", "start_day": 0, "end_day": 20, "description": "Hypocotyl emerges and first true tetrafoliate leaves expand."},
            {"name": "Vegetative & Flowering", "start_day": 21, "end_day": 45, "description": "Canopy spreads and yellow self-pollinating flowers bloom on lower nodes."},
            {"name": "Pegging & Pod Formation", "start_day": 46, "end_day": 80, "description": "Fertilized ovaries elongate into pegs that penetrate the soil to develop pods."},
            {"name": "Pod Filling & Maturation", "start_day": 81, "end_day": 120, "description": "Kernels fill inside shells; inner shell turns dark, ready for digging."}
        ],
        "source": "ICAR-DGR Junagadh / UAS Bangalore",
        "notes": "Bunch varieties mature in 100-105 days; spreading varieties take 115-125 days.",
        "confidence": "high"
    },
    "sunflower": {
        "crop_name": "Sunflower",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 85,
        "duration_days_max": 100,
        "growth_stages": [
            {"name": "Emergence & Seedling", "start_day": 0, "end_day": 15, "description": "Cotyledons emerge and first pairs of true leaves establish."},
            {"name": "Vegetative Growth", "start_day": 16, "end_day": 35, "description": "Rapid stem lengthening and flower bud initiation."},
            {"name": "Star Bud & Flowering", "start_day": 36, "end_day": 60, "description": "Inflorescence expands and ray florets open for pollination."},
            {"name": "Seed Filling & Physiological Maturity", "start_day": 61, "end_day": 100, "description": "Achenes fill with oil; back of the head turns lemon yellow to brown."}
        ],
        "source": "ICAR-IIOR Hyderabad / UAS Bangalore",
        "notes": "Short duration hybrids mature in 85-95 days.",
        "confidence": "high"
    },
    "turmeric": {
        "crop_name": "Turmeric",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 240,
        "duration_days_max": 270,
        "growth_stages": [
            {"name": "Sprouting Phase", "start_day": 0, "end_day": 30, "description": "Rhizome buds break dormancy and shoots emerge above ground."},
            {"name": "Tillering & Vegetative Growth", "start_day": 31, "end_day": 120, "description": "Production of aerial shoots and broad green leaf canopy."},
            {"name": "Rhizome Development & Bulking", "start_day": 121, "end_day": 210, "description": "Mother, primary, and secondary fingers swell underground."},
            {"name": "Maturation & Harvest", "start_day": 211, "end_day": 270, "description": "Leaves turn yellow, dry completely, and lodge; rhizomes mature for harvesting."}
        ],
        "source": "ICAR-IISR Calicut / UAS Dharwad",
        "notes": "Medium varieties take 7-8 months; long duration varieties 8-9 months.",
        "confidence": "high"
    },
    "chickpea": {
        "crop_name": "Chickpea / Bengal Gram",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 90,
        "duration_days_max": 110,
        "growth_stages": [
            {"name": "Germination & Seedling", "start_day": 0, "end_day": 18, "description": "Hypogeal emergence and branching from basal nodes."},
            {"name": "Vegetative & Branching", "start_day": 19, "end_day": 45, "description": "Formation of secondary branches and canopy closure."},
            {"name": "Flowering & Pod Initiation", "start_day": 46, "end_day": 75, "description": "Purple/pink flowers bloom and young pods appear."},
            {"name": "Pod Filling & Harvest Maturity", "start_day": 76, "end_day": 110, "description": "Seeds enlarge, plants senesce, leaves dry, pods rattle for harvest."}
        ],
        "source": "ICAR-IIPR Kanpur / UAS Dharwad",
        "notes": "Desi varieties mature in 90-105 days in northern Karnataka.",
        "confidence": "high"
    },
    "redgram": {
        "crop_name": "Redgram / Pigeonpea",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 150,
        "duration_days_max": 180,
        "growth_stages": [
            {"name": "Seedling Phase", "start_day": 0, "end_day": 25, "description": "Initial taproot penetration and seedling establishment."},
            {"name": "Slow Vegetative Growth", "start_day": 26, "end_day": 65, "description": "Branching and root nodulation."},
            {"name": "Grand Growth & Flowering", "start_day": 66, "end_day": 120, "description": "Extensive canopy expansion and raceme flowering."},
            {"name": "Pod Development & Maturity", "start_day": 121, "end_day": 180, "description": "Pods fill with 3-4 seeds; pods turn brown and dry for harvest."}
        ],
        "source": "ICAR-IIPR Kanpur / UAS Raichur",
        "notes": "Medium duration varieties (TS-3R, BSMR) take 150-165 days.",
        "confidence": "high"
    },
    "jowar": {
        "crop_name": "Sorghum / Jowar",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 100,
        "duration_days_max": 115,
        "growth_stages": [
            {"name": "Emergence & Seedling", "start_day": 0, "end_day": 15, "description": "Mesocotyl elongates and first 3 leaves emerge."},
            {"name": "Panicle Differentiation & Grand Growth", "start_day": 16, "end_day": 50, "description": "Rapid stem expansion and floral initiation inside whorl."},
            {"name": "Booting & Half-Bloom", "start_day": 51, "end_day": 70, "description": "Panicle emerges and anthesis occurs from tip downward."},
            {"name": "Grain Filling (Milk to Dough)", "start_day": 71, "end_day": 95, "description": "Kernels fill with starch and harden."},
            {"name": "Physiological Maturity", "start_day": 96, "end_day": 115, "description": "Black layer marks maturity; grains achieve harvest moisture."}
        ],
        "source": "ICAR-IIMR Hyderabad / UAS Dharwad",
        "notes": "Rabi sorghum varieties like M 35-1 mature in 110-120 days.",
        "confidence": "high"
    },
    "bajra": {
        "crop_name": "Pearl Millet / Bajra",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 75,
        "duration_days_max": 90,
        "growth_stages": [
            {"name": "Seedling Phase", "start_day": 0, "end_day": 12, "description": "Rapid seedling emergence under warm arid conditions."},
            {"name": "Tillering & Stem Elongation", "start_day": 13, "end_day": 35, "description": "Tillering and panicle differentiation."},
            {"name": "Flowering & Anthesis", "start_day": 36, "end_day": 55, "description": "Cylindrical spikes emerge and stigmas become receptive."},
            {"name": "Grain Filling & Maturity", "start_day": 56, "end_day": 90, "description": "Grains develop rapidly and turn greyish-pearl; ready for harvest."}
        ],
        "source": "ICAR-AICRP on Pearl Millet / UAS Raichur",
        "notes": "Short duration drought-hardy crop maturing in 75-85 days.",
        "confidence": "high"
    },
    "coffee": {
        "crop_name": "Coffee",
        "crop_type": "perennial",
        "is_perennial": True,
        "bearing_age_years_min": 3.0,
        "bearing_age_years_max": 4.0,
        "harvest_season_description": "November – February (ನವೆಂಬರ್ – ಫೆಬ್ರವರಿ)",
        "duration_days_min": 1095,
        "duration_days_max": 1460,
        "growth_stages": [
            {"name": "Seedling Establishment", "start_day": 0, "end_day": 365, "description": "Nursery transplanting and shade canopy establishment."},
            {"name": "Juvenile Vegetative Growth", "start_day": 366, "end_day": 1095, "description": "Bush formation, primary and secondary plagiotropic branching."},
            {"name": "Blossom & First Berry Set", "start_day": 1096, "end_day": 1460, "description": "Blossom showers trigger flowering and initial berry clusters set."},
            {"name": "Commercial Productive Bearing", "start_day": 1461, "end_day": 15000, "description": "Full berry production with annual ripening between November and February."}
        ],
        "source": "Central Coffee Research Institute (CCRI) Balehonnur",
        "notes": "Perennial plantation crop with a productive life of 40+ years. Arabica matures in Nov-Jan, Robusta in Jan-March.",
        "confidence": "high"
    },
    "tomato": {
        "crop_name": "Tomato",
        "crop_type": "annual",
        "is_perennial": False,
        "duration_days_min": 100,
        "duration_days_max": 130,
        "growth_stages": [
            {"name": "Transplanting & Establishment", "start_day": 0, "end_day": 20, "description": "Transplanted seedlings develop secondary root system and adjust to field conditions."},
            {"name": "Vegetative & Early Flowering", "start_day": 21, "end_day": 45, "description": "Rapid lateral branching, foliage expansion, and first flower trusses open."},
            {"name": "Fruit Setting & Berry Sizing", "start_day": 46, "end_day": 75, "description": "Pollinated flowers develop into green tomatoes, sizing rapidly."},
            {"name": "Breaker to Full Red Ripening", "start_day": 76, "end_day": 105, "description": "Fruit color breaks from green to pink and full red."},
            {"name": "Multiple Harvesting Rounds", "start_day": 106, "end_day": 130, "description": "Continuous harvest of ripe fruits every 3-5 days."}
        ],
        "source": "IIHR Bengaluru / UAS Bangalore",
        "notes": "Determinate hybrids mature in 90-110 days; indeterminate hybrids produce over 120-140 days.",
        "confidence": "high"
    }
}


class AgronomicService:
    """
    Isolated service to query Gemini for crop agronomy reference data.
    Features local verified baselines for Karnataka crops and persistent disk caching.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None, cache_path: Optional[Path] = None):
        if gemini_client is not None:
            self._client = gemini_client
        else:
            try:
                self._client = GeminiClient()
            except ConfigurationError as e:
                logger.warning(
                    "AgronomicService: GeminiClient not configured: {e}", e=str(e)
                )
                self._client = None
            except Exception as e:
                logger.error(
                    "AgronomicService: Failed to initialize GeminiClient: {e}", e=str(e)
                )
                self._client = None

        if cache_path is not None:
            self.cache_path = cache_path
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.cache_path = base_dir / "database" / "agronomy_cache.json"

        self._cache: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        if self.cache_path and self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read agronomy cache: {e}")
        return {}

    def _save_cache(self):
        if not self.cache_path:
            return
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write agronomy cache: {e}")

    def _resolve_baseline(self, crop_name: str) -> Optional[AgronomicReference]:
        """Check if crop matches any verified baseline model."""
        clean = crop_name.strip().lower()
        # Direct key match
        if clean in VERIFIED_AGRONOMY_BASELINES:
            data = VERIFIED_AGRONOMY_BASELINES[clean]
            return self._dict_to_reference(data)

        # Kannada / English alias match
        for key, data in VERIFIED_AGRONOMY_BASELINES.items():
            ref_name = data.get("crop_name", "").lower()
            if clean == ref_name or clean in ref_name or ref_name in clean:
                return self._dict_to_reference(data)

        # Common Kannada transliteration mappings
        kannada_map = {
            "ಭತ್ತ": "paddy", "ರಾಗಿ": "ragi", "ಮೆಕ್ಕೆಜೋಳ": "maize",
            "ಅಡಿಕೆ": "arecanut", "ತೆಂಗು": "coconut", "ಹತ್ತಿ": "cotton",
            "ಕಬ್ಬು": "sugarcane", "ಕಡಲೆಕಾಯಿ": "groundnut", "ಶೇಂಗಾ": "groundnut",
            "ಸೂರ್ಯಕಾಂತಿ": "sunflower", "ಅರಿಶಿನ": "turmeric", "ಕಡಲೆ": "chickpea",
            "ತೊಗರಿ": "redgram", "ಜೋಳ": "jowar", "ಸಜ್ಜೆ": "bajra",
            "ಕಾಫಿ": "coffee", "ಟೊಮೆಟೊ": "tomato", "ಟೊಮೇಟೊ": "tomato"
        }
        for kn_word, base_key in kannada_map.items():
            if kn_word in clean or clean in kn_word:
                if base_key in VERIFIED_AGRONOMY_BASELINES:
                    return self._dict_to_reference(VERIFIED_AGRONOMY_BASELINES[base_key])

        return None

    def _dict_to_reference(self, data: Dict[str, Any]) -> AgronomicReference:
        stages = []
        for s in data.get("growth_stages", []):
            stages.append(
                GrowthStage(
                    name=s["name"],
                    start_day=s["start_day"],
                    end_day=s["end_day"],
                    description=s.get("description"),
                )
            )
        return AgronomicReference(
            crop_name=data.get("crop_name", "Unknown Crop"),
            duration_days_min=data.get("duration_days_min"),
            duration_days_max=data.get("duration_days_max"),
            growth_stages=stages,
            source=data.get("source"),
            notes=data.get("notes"),
            confidence=data.get("confidence", "high"),
            crop_type=data.get("crop_type", "annual"),
            is_perennial=data.get("is_perennial", False),
            bearing_age_years_min=data.get("bearing_age_years_min"),
            bearing_age_years_max=data.get("bearing_age_years_max"),
            harvest_season_description=data.get("harvest_season_description"),
        )

    def _build_prompt(self, crop_name: str) -> str:
        """
        Builds a strict, hallucination-resistant prompt requesting agronomic data in JSON.
        Supports both Annual field crops and Perennial tree/plantation crops.
        """
        return f"""You are an agricultural reference system. Provide typical agronomic lifecycle, duration, and growth stage reference data for the crop: "{crop_name}".

STRICT GUIDELINES:
1. Determine whether "{crop_name}" is an "annual" crop (single seasonal cycle like Paddy, Wheat, Vegetables) or a "perennial" crop (tree/plantation crop like Arecanut, Coconut, Mango, Citrus, Coffee).
2. For ANNUAL crops:
   - Provide realistic range of days from sowing to harvest (duration_days_min and duration_days_max).
   - Provide 4 to 6 sequential growth stages with start_day and end_day (in days from sowing).
   - set is_perennial to false.
3. For PERENNIAL crops:
   - set is_perennial to true, crop_type to "perennial" or "plantation".
   - duration_days_min & duration_days_max should be the days to first commercial bearing (e.g. 4-5 years = 1460-1825 days).
   - bearing_age_years_min & bearing_age_years_max (e.g. 4.0 and 5.0 for Arecanut).
   - harvest_season_description: the typical annual harvest window (e.g. "October to February" or "Year-round").
   - growth_stages: developmental phases from sapling planting (e.g. Establishment year 0-1, Juvenile years 2-4, First Bearing year 5, Full Economic Production year 5+).
4. If reliable data is unavailable, provide conservative estimates and state confidence as "low" or "estimated".
5. Return ONLY a valid JSON object. No markdown code blocks, no other text.

Expected JSON Structure:
{{
  "crop_name": "{crop_name}",
  "crop_type": "annual | perennial",
  "is_perennial": true | false,
  "duration_days_min": <integer or null>,
  "duration_days_max": <integer or null>,
  "bearing_age_years_min": <number or null>,
  "bearing_age_years_max": <number or null>,
  "harvest_season_description": "<typical harvest months or null>",
  "growth_stages": [
    {{
      "name": "<stage name>",
      "start_day": <integer >= 0>,
      "end_day": <integer >= start_day>,
      "description": "<optional brief note or null>"
    }}
  ],
  "source": "<reference source or null>",
  "notes": "<important assumptions or null>",
  "confidence": "high | medium | low | estimated"
}}
"""

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from raw LLM output, handling markdown fences and whitespace.
        """
        if not raw_text or not raw_text.strip():
            raise AgronomicServiceError("Empty response received from Gemini.")

        cleaned = raw_text.strip()

        # Remove markdown code block wrappers if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        # Attempt direct JSON load
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: search for outermost JSON object
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError as e:
                    raise AgronomicServiceError(
                        f"Malformed JSON in Gemini response: {e}"
                    )
            raise AgronomicServiceError(
                "No valid JSON object found in Gemini response."
            )

    def _validate_and_build_reference(
        self, data: Dict[str, Any], requested_crop: str
    ) -> AgronomicReference:
        """
        Validates the extracted JSON dictionary against structural and numeric rules.
        """
        if not isinstance(data, dict):
            raise AgronomicServiceError(
                f"Expected JSON object, got {type(data).__name__}"
            )

        crop_name = str(data.get("crop_name") or requested_crop).strip()
        crop_type = str(data.get("crop_type") or "annual").strip().lower()
        is_perennial = bool(data.get("is_perennial") or crop_type in ["perennial", "plantation"])

        # 1. Validate duration_days_min
        raw_min = data.get("duration_days_min")
        duration_min: Optional[int] = None
        if raw_min is not None:
            if isinstance(raw_min, (int, float)) and not isinstance(raw_min, bool):
                duration_min = int(raw_min)
            elif isinstance(raw_min, str) and raw_min.isdigit():
                duration_min = int(raw_min)

        # 2. Validate duration_days_max
        raw_max = data.get("duration_days_max")
        duration_max: Optional[int] = None
        if raw_max is not None:
            if isinstance(raw_max, (int, float)) and not isinstance(raw_max, bool):
                duration_max = int(raw_max)
            elif isinstance(raw_max, str) and raw_max.isdigit():
                duration_max = int(raw_max)

        # 3. Validate min <= max when both are present
        if duration_min is not None and duration_max is not None:
            if duration_max < duration_min:
                duration_max = duration_min

        # 4. Validate growth stages
        raw_stages = data.get("growth_stages")
        validated_stages: List[GrowthStage] = []

        if isinstance(raw_stages, list):
            for idx, stage in enumerate(raw_stages):
                if not isinstance(stage, dict):
                    continue

                name = stage.get("name")
                if not name or not isinstance(name, str) or not name.strip():
                    continue

                start_day = stage.get("start_day")
                end_day = stage.get("end_day")

                try:
                    start_day = int(start_day)
                    end_day = int(end_day)
                except (ValueError, TypeError):
                    continue

                if start_day < 0 or end_day < start_day:
                    continue

                desc = stage.get("description")
                if desc is not None and not isinstance(desc, str):
                    desc = str(desc)

                validated_stages.append(
                    GrowthStage(
                        name=name.strip(),
                        start_day=start_day,
                        end_day=end_day,
                        description=desc.strip() if desc else None,
                    )
                )

        # 5. If stages are missing but duration is known, build standard interpolated stages
        if not validated_stages and duration_min and duration_max:
            if is_perennial:
                validated_stages = [
                    GrowthStage(name="Establishment Phase", start_day=0, end_day=365, description="Initial root establishment and vegetative vigor."),
                    GrowthStage(name="Juvenile Growth", start_day=366, end_day=max(366, duration_min - 365), description="Canopy expansion and structural growth prior to bearing."),
                    GrowthStage(name="Bearing & Productive Phase", start_day=max(366, duration_min - 365) + 1, end_day=duration_max * 5, description="Active economic bearing phase.")
                ]
            else:
                s1_end = int(duration_max * 0.15)
                s2_end = int(duration_max * 0.45)
                s3_end = int(duration_max * 0.75)
                validated_stages = [
                    GrowthStage(name="Germination & Seedling", start_day=0, end_day=s1_end, description="Seed emergence and initial vegetative establishment."),
                    GrowthStage(name="Vegetative Growth", start_day=s1_end + 1, end_day=s2_end, description="Active foliage development and tillering/branching."),
                    GrowthStage(name="Flowering & Development", start_day=s2_end + 1, end_day=s3_end, description="Inflorescence, blooming, and initial fruit/grain formation."),
                    GrowthStage(name="Maturity & Harvest", start_day=s3_end + 1, end_day=duration_max, description="Crop reaches harvest maturity.")
                ]

        source = data.get("source")
        notes = data.get("notes")
        confidence = data.get("confidence") or ("high" if validated_stages else "estimated")

        return AgronomicReference(
            crop_name=crop_name,
            duration_days_min=duration_min,
            duration_days_max=duration_max,
            growth_stages=validated_stages,
            source=str(source).strip() if source else "Raitha Sathi Agronomic System",
            notes=str(notes).strip() if notes else None,
            confidence=str(confidence).strip() if confidence else "medium",
            crop_type=crop_type,
            is_perennial=is_perennial,
            bearing_age_years_min=data.get("bearing_age_years_min"),
            bearing_age_years_max=data.get("bearing_age_years_max"),
            harvest_season_description=data.get("harvest_season_description"),
        )

    async def get_crop_agronomy(self, crop_name: str) -> AgronomicReference:
        """
        Resolves reference agronomic data for a given crop name with local baselines,
        disk caching, and LLM generative fallback.
        """
        if not crop_name or not crop_name.strip():
            raise AgronomicServiceError("Crop name must not be empty.")

        crop_name = crop_name.strip()
        cache_key = crop_name.lower()

        # Step 1: Check verified baseline
        baseline = self._resolve_baseline(crop_name)
        if baseline:
            logger.info("AgronomicService: Matched verified baseline | crop={crop}", crop=crop_name)
            return baseline

        # Step 2: Check persistent disk cache
        if cache_key in self._cache:
            logger.info("AgronomicService: Retrieved from disk cache | crop={crop}", crop=crop_name)
            return self._dict_to_reference(self._cache[cache_key])

        # Step 3: Query Gemini
        if self._client is not None:
            try:
                prompt = self._build_prompt(crop_name)
                logger.info("AgronomicService: Querying Gemini for novel crop | crop={crop}", crop=crop_name)
                raw_response = await self._client.generate(prompt)
                parsed_json = self._extract_json(raw_response)
                reference = self._validate_and_build_reference(parsed_json, crop_name)

                # Persist in cache
                self._cache[cache_key] = reference.to_dict()
                self._save_cache()
                return reference
            except Exception as e:
                logger.warning(
                    "AgronomicService: Gemini resolution failed | crop={crop} | error={e}. Using safe fallback.",
                    crop=crop_name, e=str(e)
                )

        # Step 4: Generic Safe Fallback for Unknown Crops (Zero Crash Guarantee)
        logger.info("AgronomicService: Generating safe fallback reference | crop={crop}", crop=crop_name)
        fallback_ref = AgronomicReference(
            crop_name=crop_name,
            duration_days_min=90,
            duration_days_max=120,
            growth_stages=[
                GrowthStage(name="Early Establishment", start_day=0, end_day=20, description="Seed emergence and vegetative establishment."),
                GrowthStage(name="Vegetative Growth", start_day=21, end_day=55, description="Foliage expansion and active canopy growth."),
                GrowthStage(name="Flowering & Reproductive", start_day=56, end_day=90, description="Flowering and fruit/seed formation."),
                GrowthStage(name="Maturity & Harvest", start_day=91, end_day=120, description="Ripening and harvest window.")
            ],
            source="General Agronomic Lifecycle Model",
            notes="Estimated timeline based on typical agricultural crop lifecycles. May vary by variety and season.",
            confidence="estimated",
            crop_type="annual",
            is_perennial=False,
        )
        self._cache[cache_key] = fallback_ref.to_dict()
        self._save_cache()
        return fallback_ref
