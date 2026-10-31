"""Tests for Part 2 Agent tools, regex extractor, and deterministic normalizer."""

import pytest

from app.agent.normalizer import (
    canonicalize_crop_name,
    cleanse_and_merge_records,
    normalize_date_iso,
    normalize_email_address,
    normalize_plot_id,
)
from app.agent.schemas import RawEmailMessage
from app.agent.tools.calendar_tool import fetch_calendar_events
from app.agent.tools.email_tool import (
    _deterministic_extract,
    extract_all_emails,
    extract_record_from_email,
    fetch_gardener_emails,
)


def test_normalize_date_iso_formats():
    """Verify various human date formats normalize to strict ISO YYYY-MM-DD."""
    assert normalize_date_iso("Nov 2nd, 2026") == "2026-11-02"
    assert normalize_date_iso("02/11/2026") == "2026-11-02"
    assert normalize_date_iso("03/11/2026") == "2026-11-03"
    assert normalize_date_iso("4 Nov 2026") == "2026-11-04"
    assert normalize_date_iso("06/11/2026") == "2026-11-06"
    assert normalize_date_iso("2026-11-05") == "2026-11-05"


def test_normalize_plot_id_variations():
    """Verify case, separator, and prefix normalization for plot identifiers."""
    assert normalize_plot_id("plot-w04") == "PLOT-W04"
    assert normalize_plot_id("plot w04") == "PLOT-W04"
    assert normalize_plot_id("plot_b07") == "PLOT-B07"
    assert normalize_plot_id("W04") == "PLOT-W04"
    assert normalize_plot_id("PLOT-KH02") == "PLOT-KH02"


def test_cleanse_and_merge_demo_emails():
    """Test full ingestion, extraction, and deduplication of 10 demo gardener emails."""
    raw_emails, mode = fetch_gardener_emails("demo")
    assert mode == "demo"
    assert len(raw_emails) == 10

    extracted = extract_all_emails(raw_emails)
    assert len(extracted) == 10

    merged = cleanse_and_merge_records(extracted, raw_emails)
    assert len(merged) == 8

    # Check REC-001 merged follow-up pH fill
    rec1 = merged[0]
    assert rec1.record_id == "REC-001"
    assert rec1.gardener_name == "Sipho Ndlovu"
    assert rec1.plot_id == "PLOT-W04"
    assert rec1.planted_date == "2026-11-02"
    assert rec1.source_email_ids == ["EMAIL-101", "EMAIL-102"]
    assert rec1.crop_name == "Heirloom Tomato"
    assert rec1.species_scientific_raw == "Solanumm lykopersikun"
    assert rec1.quantity_planted == 24
    assert rec1.measured_soil_ph == 5.3
    assert rec1.seed_batch_id == "BATCH-CT-2026-09"
    assert len(rec1.merge_audit_log) == 1
    assert "measured_soil_ph=5.3" in rec1.merge_audit_log[0]

    # Check REC-002 merged follow-up quantity update (30 -> 40)
    rec2 = merged[1]
    assert rec2.record_id == "REC-002"
    assert rec2.gardener_name == "Zanele Mbeki"
    assert rec2.plot_id == "PLOT-C02"
    assert rec2.planted_date == "2026-11-03"
    assert rec2.source_email_ids == ["EMAIL-103", "EMAIL-104"]
    assert rec2.crop_name == "Spinach"
    assert rec2.quantity_planted == 40
    assert len(rec2.merge_audit_log) == 1
    assert "quantity_planted 30 -> 40" in rec2.merge_audit_log[0]

    # Check REC-007 missing pH and batch ID
    rec7 = merged[6]
    assert rec7.record_id == "REC-007"
    assert rec7.gardener_name == "Johan Botha"
    assert rec7.plot_id == "PLOT-H05"
    assert rec7.planted_date == "2026-11-06"
    assert rec7.measured_soil_ph is None
    assert rec7.seed_batch_id is None


def test_calendar_fetch_demo():
    """Verify loading demo calendar events fixture."""
    events, mode = fetch_calendar_events("demo")
    assert mode == "demo"
    assert len(events) == 8
    assert events[0].plot_id == "PLOT-W04"
    assert events[0].gardener_name == "Sipho Ndlovu"


def test_regex_extraction_without_hints():
    """Verify regex extraction from email body when parsed_hints is empty."""
    raw = RawEmailMessage(
        email_id="EMAIL-CUSTOM",
        sender_name="Sipho Ndlovu",
        sender_email="sipho@capegardens.org.za",
        received_at="2026-11-02T14:15:00Z",
        subject="Woodstock planting report - plot w04",
        body=(
            "Planted 24 Heirloom Tomato plants (scientific name Solanum lycopersicun) "
            "at Woodstock plot-w04 on Nov 2nd, 2026. Batch was BATCH-CT-2026-09. "
            "Measured soil pH exactly 5.5."
        ),
        parsed_hints={},
    )
    rec = extract_record_from_email(raw)
    assert rec.planted_date_raw == "Nov 2nd, 2026"
    assert rec.suburb == "Woodstock"
    assert rec.plot_id == "PLOT-W04"
    assert rec.crop_name == "Heirloom Tomato"
    assert rec.species_scientific_raw == "Solanum lycopersicun"
    assert rec.quantity_planted == 24
    assert rec.measured_soil_ph == 5.5
    assert rec.seed_batch_id == "BATCH-CT-2026-09"
