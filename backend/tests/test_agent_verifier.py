"""Unit and integration tests for Part 2 Autonomous Multi-Tool Verification Agent."""

from fastapi.testclient import TestClient
import pytest

from app.agent.normalizer import cleanse_and_merge_records
from app.agent.tools.calendar_tool import fetch_calendar_events
from app.agent.tools.email_tool import extract_all_emails, fetch_gardener_emails
from app.agent.tools.gbif_tool import verify_species_gbif
from app.agent.verifier import verify_all_records
from app.main import app


def test_gbif_tool_typo_correction_and_exact_match() -> None:
    """Verify GBIF taxonomic tool corrects spelling typos and preserves exact matches."""
    # 1. Solanumm lykopersikun typo
    res1 = verify_species_gbif("Solanumm lykopersikun")
    assert res1["verified_name"] == "Solanum lycopersicum"
    assert res1["is_typo_corrected"] is True
    assert res1["confidence"] == 96

    # 2. Brasika oleracia var. acefala typo
    res2 = verify_species_gbif("Brasika oleracia var. acefala")
    assert res2["verified_name"] == "Brassica oleracea var. acephala"
    assert res2["is_typo_corrected"] is True
    assert res2["confidence"] == 94

    # 3. Kukurbitia moskata typo
    res3 = verify_species_gbif("Kukurbitia moskata")
    assert res3["verified_name"] == "Cucurbita moschata"
    assert res3["is_typo_corrected"] is True
    assert res3["confidence"] == 95

    # 4. Spinacia oleracea exact match
    res4 = verify_species_gbif("Spinacia oleracea")
    assert res4["verified_name"] == "Spinacia oleracea"
    assert res4["is_typo_corrected"] is False
    assert res4["is_unverified"] is False


def test_verifier_3_file_join_and_all_flags() -> None:
    """Verify 5-way rule verification engine produces correct flags and audit classifications."""
    raw_emails, _ = fetch_gardener_emails("demo")
    calendar_events, _ = fetch_calendar_events("demo")

    extracted = extract_all_emails(raw_emails)
    merged = cleanse_and_merge_records(extracted, raw_emails)
    verified = verify_all_records(merged, calendar_events)

    assert len(verified) == 8
    v_map = {r.record_id: r for r in verified}

    # REC-001 (Sipho Ndlovu, Woodstock): FLAGGED, typo corrected, pH out of range, lime recommendation
    rec1 = v_map["REC-001"]
    assert rec1.gardener_name == "Sipho Ndlovu"
    assert rec1.suburb == "Woodstock"
    assert rec1.status == "FLAGGED"
    assert "SPECIES_TYPO_CORRECTED" in rec1.flags
    assert "SOIL_PH_OUT_OF_RANGE" in rec1.flags
    assert "150g/m2 Agricultural Lime" in rec1.soil_treatment_recommendation

    # REC-002 (Zanele Mbeki, Constantia): VERIFIED, no flags, quantity 40
    rec2 = v_map["REC-002"]
    assert rec2.gardener_name == "Zanele Mbeki"
    assert rec2.suburb == "Constantia"
    assert rec2.status == "VERIFIED"
    assert rec2.flags == []
    assert rec2.quantity_planted == 40

    # REC-003 (Pieter van der Merwe, Kirstenbosch): AUTO_CORRECTED
    rec3 = v_map["REC-003"]
    assert rec3.gardener_name == "Pieter van der Merwe"
    assert rec3.status == "AUTO_CORRECTED"
    assert rec3.flags == ["SPECIES_TYPO_CORRECTED"]

    # REC-004 (Amina Patel, Bellville): AUTO_CORRECTED
    rec4 = v_map["REC-004"]
    assert rec4.gardener_name == "Amina Patel"
    assert rec4.status == "AUTO_CORRECTED"
    assert rec4.flags == ["SPECIES_TYPO_CORRECTED"]

    # REC-006 (Lerato Molefe, Observatory PLOT-O09): FLAGGED, UNSCHEDULED_PLANTING
    rec6 = v_map["REC-006"]
    assert rec6.gardener_name == "Lerato Molefe"
    assert rec6.plot_id == "PLOT-O09"
    assert rec6.status == "FLAGGED"
    assert "UNSCHEDULED_PLANTING" in rec6.flags

    # REC-007 (Johan Botha, Hout Bay): FLAGGED, MISSING_REQUIRED_FIELDS
    rec7 = v_map["REC-007"]
    assert rec7.gardener_name == "Johan Botha"
    assert rec7.status == "FLAGGED"
    assert "MISSING_REQUIRED_FIELDS" in rec7.flags


def test_langgraph_and_fastapi_agent_endpoint() -> None:
    """Verify LangGraph 5-node workflow execution via FastAPI POST /api/agent/run."""
    client = TestClient(app)

    # 1. Run Agent endpoint
    res = client.post("/api/agent/run", json={"mode": "demo"})
    assert res.status_code == 200
    data = res.json()

    assert data["summary"] == {
        "raw_emails_count": 10,
        "calendar_events_count": 8,
        "merged_records_count": 8,
        "verified_count": 3,
        "auto_corrected_count": 2,
        "flagged_count": 3,
    }

    assert len(data["workflow_nodes"]) == 5
    assert len(data["records"]) == 8
    assert "REC-001" in data["csv_export"]
    assert "Solanum lycopersicum" in data["csv_export"]

    # 2. Fixtures inspector endpoint
    res_fix = client.get("/api/agent/fixtures")
    assert res_fix.status_code == 200
    fix_data = res_fix.json()
    assert len(fix_data["calendar_events"]) == 8
    assert len(fix_data["raw_emails"]) == 10
