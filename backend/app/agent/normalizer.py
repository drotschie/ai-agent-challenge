"""Deterministic normalization, canonicalization, and follow-up email deduplication."""

from datetime import datetime
import logging
import re
from typing import Any

from app.agent.schemas import CleanedMergedRecord, ExtractedEmailRecord, RawEmailMessage
from app.rag.query_transform import CROP_ALIASES, get_known_crops

logger = logging.getLogger(__name__)


def normalize_date_iso(raw_date: str | None) -> str:
    """Normalize raw date strings into standard ISO YYYY-MM-DD.

    Supports ISO dates, South African DD/MM/YYYY slash dates, and month/day text formats.
    Strips ordinal suffixes (1st, 2nd, 3rd, 4th, etc.).
    """
    if not raw_date:
        return ""

    s = raw_date.strip()
    # Strip ordinal suffixes
    s = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", s, flags=re.IGNORECASE)

    # Already ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    # South African slash dates DD/MM/YYYY
    slash_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if slash_match:
        day = int(slash_match.group(1))
        month = int(slash_match.group(2))
        year = int(slash_match.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    # Text date parsing
    for fmt in (
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d %b, %Y",
        "%d %B, %Y",
        "%Y/%m/%d",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return s


def normalize_plot_id(raw_plot: str | None) -> str:
    """Extract and standardize plot codes to uppercase PLOT-<CODE>."""
    if not raw_plot:
        return ""

    clean = raw_plot.strip().upper()

    # Matches "PLOT-W04", "PLOT W04", "PLOT_B07"
    prefix_match = re.match(r"^PLOT[-_\s]+([A-Z0-9]+)$", clean)
    if prefix_match:
        return f"PLOT-{prefix_match.group(1)}"

    # Already PLOT-CODE
    if clean.startswith("PLOT-"):
        return clean

    # Standalone code like "W04", "B07", "KH02"
    code_match = re.match(r"^([A-Z0-9]+)$", clean)
    if code_match:
        return f"PLOT-{code_match.group(1)}"

    # Embedded match inside string
    sub_match = re.search(r"PLOT[-_\s]*([A-Z0-9]+)", clean)
    if sub_match:
        return f"PLOT-{sub_match.group(1)}"

    return clean


def normalize_email_address(raw_email: str | None) -> str:
    """Lowercase and strip whitespace from email addresses."""
    if not raw_email:
        return ""
    return raw_email.strip().lower()


def canonicalize_crop_name(raw_crop: str | None) -> str | None:
    """Canonicalize crop names against Part 1 canonical crops and aliases."""
    if not raw_crop:
        return None

    s = raw_crop.strip()
    s_lower = s.lower()

    if s_lower in CROP_ALIASES:
        return CROP_ALIASES[s_lower]

    known_crops = get_known_crops()
    for c in known_crops:
        if c.lower() == s_lower:
            return c

    for c in known_crops:
        if c.lower() in s_lower or s_lower in c.lower():
            return c

    return s


def cleanse_and_merge_records(
    extracted_records: list[ExtractedEmailRecord],
    raw_emails: list[RawEmailMessage],
) -> list[CleanedMergedRecord]:
    """Deduplicate and merge follow-up emails into canonical CleanedMergedRecord objects.

    Groups records by (normalized_sender_email, normalized_plot_id, normalized_date_iso).
    Preserves first-seen order and merges subsequent follow-up updates chronologically.
    """
    email_map = {e.email_id: e for e in raw_emails}

    grouped: dict[tuple[str, str, str], list[ExtractedEmailRecord]] = {}

    for rec in extracted_records:
        norm_email = normalize_email_address(rec.sender_email)
        norm_plot = normalize_plot_id(rec.plot_id)
        norm_date = normalize_date_iso(rec.planted_date_raw)
        key = (norm_email, norm_plot, norm_date)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(rec)

    cleaned_records: list[CleanedMergedRecord] = []

    for i, (key, recs) in enumerate(grouped.items(), start=1):
        recs.sort(key=lambda r: r.received_at)
        base_rec = recs[0]
        base_email_id = base_rec.email_id
        base_raw = email_map.get(base_email_id)

        source_email_ids: list[str] = [base_email_id]
        raw_emails_before: list[RawEmailMessage] = [base_raw] if base_raw else []
        merge_audit_log: list[str] = []

        gardener_name = base_rec.sender_name
        gardener_email = normalize_email_address(base_rec.sender_email)
        suburb = base_rec.suburb or ""
        plot_id = normalize_plot_id(base_rec.plot_id)
        planted_date = normalize_date_iso(base_rec.planted_date_raw)
        crop_name = canonicalize_crop_name(base_rec.crop_name)
        species_scientific_raw = base_rec.species_scientific_raw
        quantity_planted = base_rec.quantity_planted
        measured_soil_ph = base_rec.measured_soil_ph
        seed_batch_id = base_rec.seed_batch_id

        for follow_up in recs[1:]:
            source_email_ids.append(follow_up.email_id)
            follow_raw = email_map.get(follow_up.email_id)
            if follow_raw:
                raw_emails_before.append(follow_raw)

            field_updates = [
                ("suburb", suburb, follow_up.suburb),
                ("crop_name", crop_name, canonicalize_crop_name(follow_up.crop_name)),
                ("species_scientific_raw", species_scientific_raw, follow_up.species_scientific_raw),
                ("quantity_planted", quantity_planted, follow_up.quantity_planted),
                ("measured_soil_ph", measured_soil_ph, follow_up.measured_soil_ph),
                ("seed_batch_id", seed_batch_id, follow_up.seed_batch_id),
            ]

            for field_name, existing, v in field_updates:
                if v is None:
                    continue
                if existing is None:
                    if field_name == "suburb":
                        suburb = v
                    elif field_name == "crop_name":
                        crop_name = v
                    elif field_name == "species_scientific_raw":
                        species_scientific_raw = v
                    elif field_name == "quantity_planted":
                        quantity_planted = v
                    elif field_name == "measured_soil_ph":
                        measured_soil_ph = v
                    elif field_name == "seed_batch_id":
                        seed_batch_id = v
                    merge_audit_log.append(
                        f"Merged follow-up {follow_up.email_id} into {base_email_id}: filled {field_name}={v}"
                    )
                elif existing != v:
                    if field_name == "suburb":
                        suburb = v
                    elif field_name == "crop_name":
                        crop_name = v
                    elif field_name == "species_scientific_raw":
                        species_scientific_raw = v
                    elif field_name == "quantity_planted":
                        quantity_planted = v
                    elif field_name == "measured_soil_ph":
                        measured_soil_ph = v
                    elif field_name == "seed_batch_id":
                        seed_batch_id = v
                    merge_audit_log.append(
                        f"Merged follow-up {follow_up.email_id} into {base_email_id}: updated {field_name} {existing} -> {v}"
                    )

        rec_id = f"REC-{i:03d}"
        cleaned = CleanedMergedRecord(
            record_id=rec_id,
            source_email_ids=source_email_ids,
            raw_emails_before=raw_emails_before,
            merge_audit_log=merge_audit_log,
            gardener_name=gardener_name,
            gardener_email=gardener_email,
            suburb=suburb,
            plot_id=plot_id,
            planted_date=planted_date,
            crop_name=crop_name,
            species_scientific_raw=species_scientific_raw,
            quantity_planted=quantity_planted,
            measured_soil_ph=measured_soil_ph,
            seed_batch_id=seed_batch_id,
        )
        cleaned_records.append(cleaned)

    return cleaned_records
