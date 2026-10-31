"""Five-way Cross-Tool and Cross-Part verification engine.

Verifies cleaned planting records against:
1. Google Calendar schedules (unscheduled plantings)
2. GBIF Taxonomic Species API (spelling corrections and acceptance)
3. Part 1 reference data (crop JSON + regional CSV + PDF Table 1 soil treatment)
4. Open-Meteo live weather forecasts (frost and heat stress warnings)
5. Record completeness requirements (mandatory agronomic fields)
"""

from functools import lru_cache
import logging
from typing import Any

from app.agent.schemas import CalendarEvent, CleanedMergedRecord, VerifiedPlantingRecord
from app.agent.tools.gbif_tool import verify_species_gbif
from app.agent.tools.weather_tool import verify_suburb_weather_risk
from app.rag.pipeline import (
    _find_matching_treatment_rule,
    _get_crops_guide,
    _get_suburbs_lookup,
)
from app.rag.query_transform import CROP_ALIASES

logger = logging.getLogger(__name__)

CRITICAL_FLAGS = {
    "UNSCHEDULED_PLANTING",
    "PLOT_MISMATCH",
    "SOIL_PH_OUT_OF_RANGE",
    "MISSING_REQUIRED_FIELDS",
    "UNVERIFIED_SPECIES",
    "WEATHER_FROST_WARNING",
    "HEAT_STRESS_WARNING",
}


@lru_cache(maxsize=1)
def _get_crops_map() -> dict[str, dict[str, Any]]:
    """Build a lowercase lookup dictionary for crops in crop_planting_guide.json."""
    crops = _get_crops_guide()
    lookup: dict[str, dict[str, Any]] = {}
    for c in crops:
        name = c.get("crop_name", "").strip()
        if name:
            lookup[name.lower()] = c
    return lookup


def _find_crop_info(crop_name: str | None) -> dict[str, Any]:
    """Find crop information from crop_planting_guide.json with aliases and substring fallback."""
    if not crop_name:
        return {
            "crop_name": "Unknown",
            "soil_ph_min": 6.0,
            "soil_ph_max": 7.0,
            "frost_tolerant": True,
            "optimal_temp_max_c": 30.0,
        }

    clean_name = crop_name.strip()
    name_lower = clean_name.lower()
    crops_map = _get_crops_map()

    if name_lower in crops_map:
        return crops_map[name_lower]

    if name_lower in CROP_ALIASES:
        canonical = CROP_ALIASES[name_lower]
        if canonical.lower() in crops_map:
            return crops_map[canonical.lower()]

    for k, v in crops_map.items():
        if k in name_lower or name_lower in k:
            return v

    return {
        "crop_name": clean_name,
        "soil_ph_min": 6.0,
        "soil_ph_max": 7.0,
        "frost_tolerant": True,
        "optimal_temp_max_c": 30.0,
    }


def verify_single_record(
    record: CleanedMergedRecord,
    calendar_events: list[CalendarEvent],
) -> VerifiedPlantingRecord:
    """Verify a single CleanedMergedRecord against all five verification axes."""
    flags: list[str] = []

    # 1. Calendar Schedule Check
    calendar_match = any(
        ev.gardener_email.strip().lower() == record.gardener_email.strip().lower()
        and ev.scheduled_date.strip() == record.planted_date.strip()
        and ev.plot_id.strip().upper() == record.plot_id.strip().upper()
        for ev in calendar_events
    )
    if not calendar_match:
        flags.append("UNSCHEDULED_PLANTING")

    # 2. GBIF Species Taxonomy Check
    gbif_res = verify_species_gbif(record.species_scientific_raw, record.crop_name)
    if gbif_res["is_typo_corrected"]:
        flags.append("SPECIES_TYPO_CORRECTED")
    elif gbif_res["is_unverified"]:
        flags.append("UNVERIFIED_SPECIES")

    # 3. Part 1 Reference Data 3-File Join (JSON + CSV + PDF)
    crop_info = _find_crop_info(record.crop_name)
    soil_ph_min = float(crop_info.get("soil_ph_min", 6.0))
    soil_ph_max = float(crop_info.get("soil_ph_max", 7.0))
    ideal_ph_range = f"{soil_ph_min:.1f} - {soil_ph_max:.1f}"

    suburbs_map = _get_suburbs_lookup()
    sub_row = suburbs_map.get((record.suburb or "").strip().lower(), {})
    soil_type = str(sub_row.get("soil_type", "sandy_loam"))

    if record.measured_soil_ph is not None:
        if record.measured_soil_ph < soil_ph_min or record.measured_soil_ph > soil_ph_max:
            flags.append("SOIL_PH_OUT_OF_RANGE")
            treatment_rule, _ = _find_matching_treatment_rule(soil_type, record.measured_soil_ph)
            soil_treatment_recommendation = (
                f"Apply {treatment_rule['dosage']}g/m2 {treatment_rule['amendment']} "
                f"({soil_type}, pH {record.measured_soil_ph} -> {soil_ph_min:.1f}-{soil_ph_max:.1f})"
            )
        else:
            soil_treatment_recommendation = (
                f"Optimal soil pH ({record.measured_soil_ph} within {ideal_ph_range}); no pH amendment required"
            )
    else:
        soil_treatment_recommendation = (
            "Pending soil pH measurement before applying lime or sulfur amendment"
        )

    # 4. Live Open-Meteo Weather Risk Check
    weather_res = verify_suburb_weather_risk(record.suburb, crop_info)
    if weather_res["frost_warning"]:
        flags.append("WEATHER_FROST_WARNING")
    if weather_res["heat_warning"]:
        flags.append("HEAT_STRESS_WARNING")

    # 5. Completeness Check
    if (
        record.measured_soil_ph is None
        or not record.seed_batch_id
        or not record.plot_id
        or record.quantity_planted is None
    ):
        flags.append("MISSING_REQUIRED_FIELDS")

    # Status Determination
    if any(f in CRITICAL_FLAGS for f in flags):
        status = "FLAGGED"
    elif "SPECIES_TYPO_CORRECTED" in flags:
        status = "AUTO_CORRECTED"
    else:
        status = "VERIFIED"

    return VerifiedPlantingRecord(
        record_id=record.record_id,
        source_email_ids=record.source_email_ids,
        raw_emails_before=record.raw_emails_before,
        merge_audit_log=record.merge_audit_log,
        gardener_name=record.gardener_name,
        gardener_email=record.gardener_email,
        suburb=record.suburb,
        soil_type=soil_type,
        plot_id=record.plot_id,
        planted_date=record.planted_date,
        crop_name=record.crop_name or str(crop_info.get("crop_name", "Unknown")),
        species_scientific_raw=record.species_scientific_raw or "",
        species_scientific_verified=str(gbif_res["verified_name"]),
        gbif_match_confidence=int(gbif_res["confidence"]),
        quantity_planted=record.quantity_planted,
        measured_soil_ph=record.measured_soil_ph,
        ideal_ph_range=ideal_ph_range,
        seed_batch_id=record.seed_batch_id,
        soil_treatment_recommendation=soil_treatment_recommendation,
        weather_advisory=str(weather_res["weather_advisory"]),
        status=status,
        flags=flags,
    )


def verify_all_records(
    records: list[CleanedMergedRecord],
    calendar_events: list[CalendarEvent],
) -> list[VerifiedPlantingRecord]:
    """Verify all merged planting records against calendar, taxonomy, and agronomic rules."""
    return [verify_single_record(record, calendar_events) for record in records]
