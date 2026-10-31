"""GBIF Species API verification tool adapter with deterministic offline cache."""

from functools import lru_cache
import json
import logging
import os
from typing import Any
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_gbif_fallback_cache() -> dict[str, Any]:
    """Load pre-indexed GBIF match responses from api_fallback_cache.json."""
    settings = get_settings()
    cache_path = settings.data_dir / "demo_fixtures" / "api_fallback_cache.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("gbif_matches", {})
    return {}


def verify_species_gbif(
    raw_species: str | None,
    crop_name: str | None = None,
) -> dict[str, Any]:
    """Match and verify raw taxonomic names against GBIF Species Backbone API.

    Uses deterministic fallback cache first for reproducible offline evaluation.
    """
    if not raw_species or not raw_species.strip():
        return {
            "raw_name": "",
            "verified_name": "Unknown",
            "confidence": 0,
            "match_type": "NONE",
            "is_typo_corrected": False,
            "is_unverified": True,
        }

    raw_clean = raw_species.strip()
    cache = _get_gbif_fallback_cache()

    cached_entry: dict[str, Any] | None = None
    if raw_clean in cache:
        cached_entry = cache[raw_clean]
    else:
        raw_lower = raw_clean.lower()
        for k, v in cache.items():
            if k.strip().lower() == raw_lower:
                cached_entry = v
                break

    if cached_entry is None and crop_name:
        crop_clean = crop_name.strip()
        if crop_clean in cache:
            cached_entry = cache[crop_clean]
        else:
            crop_lower = crop_clean.lower()
            for k, v in cache.items():
                if k.strip().lower() == crop_lower:
                    cached_entry = v
                    break

    verified_name = raw_clean
    confidence = 0
    match_type = "NONE"

    if cached_entry is not None:
        verified_name = str(cached_entry.get("canonicalName") or cached_entry.get("scientificName") or raw_clean)
        confidence = int(cached_entry.get("confidence", 0))
        match_type = str(cached_entry.get("matchType", "NONE")).upper()

    if os.getenv("ENABLE_LIVE_GBIF_HTTP", "0") == "1" or cached_entry is None:
        try:
            resp = httpx.get(
                "https://api.gbif.org/v1/species/match",
                params={"name": raw_clean},
                timeout=2.5,
            )
            if resp.status_code == 200:
                data = resp.json()
                live_confidence = int(data.get("confidence", 0))
                live_match_type = str(data.get("matchType", "NONE")).upper()
                live_canonical = str(data.get("canonicalName") or data.get("scientificName") or raw_clean)
                if live_confidence > 0 or cached_entry is None:
                    confidence = live_confidence
                    match_type = live_match_type
                    verified_name = live_canonical
        except Exception as exc:
            logger.info("Live GBIF HTTP query skipped or failed; using fallback: %s", exc)

    is_typo_corrected = bool(confidence >= 80 and raw_clean.lower() != verified_name.strip().lower())
    is_unverified = bool(confidence < 80 or match_type == "NONE")

    return {
        "raw_name": raw_clean,
        "verified_name": verified_name,
        "confidence": confidence,
        "match_type": match_type,
        "is_typo_corrected": is_typo_corrected,
        "is_unverified": is_unverified,
    }
