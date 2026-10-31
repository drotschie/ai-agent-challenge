"""Integration and unit tests for Part 1 RAG pipeline and FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.rag.pipeline import run_rag_query
from app.rag.query_transform import transform_query
from app.rag.schemas import ChatMessage, RagQueryRequest


def test_query_transform_resolves_pronouns_from_history() -> None:
    """Verify conversational query transform resolves pronouns like 'there' to Woodstock."""
    chat_history = [
        ChatMessage(role="user", content="I just moved to Woodstock in Cape Town.")
    ]
    question = "What is the soil pH there, and can I plant spinach?"

    qt = transform_query(question=question, chat_history=chat_history)

    assert qt.detected_suburb == "Woodstock"
    assert "Spinach" in qt.detected_crops

    target_sources = {sq.target_source for sq in qt.sub_queries}
    expected_sources = {
        "regional_soil_and_climate.csv",
        "crop_planting_guide.json",
        "soil_treatment_and_watering_rules.pdf",
    }
    assert expected_sources.issubset(target_sources)
    assert "Woodstock" in qt.resolved_question


def test_rag_pipeline_multihop_cites_all_three_sources() -> None:
    """Verify multi-hop RAG retrieval cites all 3 reference sources and derives action banner."""
    question = (
        "I live in Woodstock and my soil pH is 5.3. Can I plant spinach right now, "
        "and how much lime do I need?"
    )
    request = RagQueryRequest(question=question, chat_history=[])
    res = run_rag_query(request)

    # 1. Live weather baseline
    assert res.live_weather is not None
    assert res.live_weather.suburb == "Woodstock"
    assert res.live_weather.soil_type == "sandy_loam"

    # 2. Action banner with treatment dosage
    assert res.action_banner is not None
    assert "150" in res.action_banner
    assert "Agricultural Lime" in res.action_banner

    # 3. Retrieved chunks cover all 3 reference files
    source_files = {c.source_file for c in res.retrieved_chunks}
    assert source_files == {
        "regional_soil_and_climate.csv",
        "crop_planting_guide.json",
        "soil_treatment_and_watering_rules.pdf",
    }

    # 4. Answer explicitly cites all 3 source files
    assert "regional_soil_and_climate.csv" in res.answer
    assert "crop_planting_guide.json" in res.answer
    assert "soil_treatment_and_watering_rules.pdf" in res.answer

    # 5. Crop recommendations include Spinach
    assert len(res.recommended_crops) >= 1
    assert any(c.crop_name == "Spinach" for c in res.recommended_crops)

    # 6. Citations list is populated
    assert len(res.citations) >= 3


def test_fastapi_endpoints_rag_and_data_sources() -> None:
    """Verify FastAPI /api/health, /api/rag/query, and /api/data/sources endpoints."""
    with TestClient(app) as client:
        # 1. Health check
        health_resp = client.get("/api/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "ok"
        assert health_data["service"] == "sa-gardener-guide-api"
        assert health_data["vector_chunks_indexed"] == 125

        # 2. RAG query POST endpoint
        query_payload = {
            "question": "What soil treatment is needed for acidic soil in Woodstock?",
            "chat_history": [],
        }
        query_resp = client.post("/api/rag/query", json=query_payload)
        assert query_resp.status_code == 200
        query_data = query_resp.json()
        assert "answer" in query_data
        assert "retrieved_chunks" in query_data
        assert len(query_data["retrieved_chunks"]) > 0
        assert query_data["live_weather"] is not None

        # 3. Data sources inspection endpoint
        sources_resp = client.get("/api/data/sources")
        assert sources_resp.status_code == 200
        sources_data = sources_resp.json()

        assert len(sources_data["crops_json"]) == 40
        assert len(sources_data["suburbs_csv"]) == 40

        pdf_tables = sources_data["pdf_tables"]
        assert len(pdf_tables["table_1_soil_treatment"]) == 25
        assert len(pdf_tables["table_2_watering_rules"]) == 20

        assert len(sources_data["demo_calendar_events"]) == 8
        assert len(sources_data["demo_gardener_emails"]) == 10
        assert "technical_summary_md" in sources_data
