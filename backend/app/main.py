"""FastAPI application for South African Gardener AI Guide backend.

Provides health checks, Part 1 RAG query endpoints, and data source inspection APIs.
"""

from contextlib import asynccontextmanager
import csv
from functools import lru_cache
import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber

from app.agent.graph import run_verification_agent
from app.agent.schemas import AgentRunRequest, AgentRunResponse
from app.agent.tools.calendar_tool import fetch_calendar_events
from app.agent.tools.email_tool import fetch_gardener_emails
from app.config import get_settings
from app.rag.pipeline import run_rag_query
from app.rag.schemas import RagQueryRequest, RagQueryResponse
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager that ensures ChromaDB vector store is indexed on startup."""
    logger.info("Initializing vector store index...")
    store = get_vector_store()
    count = store.ensure_indexed()
    logger.info("Vector store index verified with %d chunks", count)
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title="South African Gardener AI Guide API",
    description="Agronomic RAG and Agentic Workflow Backend for South African Gardeners",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration allowing local Next.js frontend and cloud preview domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.(vercel\.app|hf\.space)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint reporting API status and total vector chunks indexed."""
    store = get_vector_store()
    return {
        "status": "ok",
        "service": "sa-gardener-guide-api",
        "vector_chunks_indexed": store.count(),
    }


@app.post("/api/rag/query", response_model=RagQueryResponse)
async def query_rag(request: RagQueryRequest) -> RagQueryResponse:
    """Execute multi-hop structured RAG query with live weather and grounded citations."""
    return run_rag_query(request)


@lru_cache(maxsize=1)
def _load_data_sources() -> dict[str, Any]:
    """Load and cache all data sources for the reference inspector."""
    settings = get_settings()
    data_dir = settings.data_dir

    # 1. Crops JSON
    crops_path = data_dir / "crop_planting_guide.json"
    crops_json: list[dict[str, Any]] = []
    if crops_path.exists():
        with open(crops_path, encoding="utf-8") as f:
            crops_json = json.load(f)

    # 2. Suburbs CSV
    suburbs_path = data_dir / "regional_soil_and_climate.csv"
    suburbs_csv: list[dict[str, Any]] = []
    if suburbs_path.exists():
        with open(suburbs_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            suburbs_csv = [dict(row) for row in reader]

    # 3. PDF Tables
    pdf_path = data_dir / "soil_treatment_and_watering_rules.pdf"
    table_1: list[dict[str, Any]] = []
    table_2: list[dict[str, Any]] = []
    if pdf_path.exists():
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                t1 = pdf.pages[0].extract_tables()
                if t1 and len(t1[0]) > 1:
                    headers1 = [str(h).strip() if h is not None else "" for h in t1[0][0]]
                    for row in t1[0][1:]:
                        clean_row = [str(v).strip() if v is not None else "" for v in row]
                        table_1.append(dict(zip(headers1, clean_row)))

            if len(pdf.pages) > 1:
                t2 = pdf.pages[1].extract_tables()
                if t2 and len(t2[0]) > 1:
                    headers2 = [str(h).strip() if h is not None else "" for h in t2[0][0]]
                    for row in t2[0][1:]:
                        clean_row = [str(v).strip() if v is not None else "" for v in row]
                        table_2.append(dict(zip(headers2, clean_row)))

    # 4. Demo Calendar Events
    events_path = data_dir / "demo_fixtures" / "demo_calendar_events.json"
    calendar_events: list[dict[str, Any]] = []
    if events_path.exists():
        with open(events_path, encoding="utf-8") as f:
            calendar_events = json.load(f)

    # 5. Demo Gardener Emails
    emails_path = data_dir / "demo_fixtures" / "demo_gardener_emails.json"
    gardener_emails: list[dict[str, Any]] = []
    if emails_path.exists():
        with open(emails_path, encoding="utf-8") as f:
            gardener_emails = json.load(f)

    # 6. Technical Summary Markdown
    tech_summary_paths = [
        settings.base_dir.parent / "docs" / "TECHNICAL-SUMMARY.md",
        settings.base_dir / "docs" / "TECHNICAL-SUMMARY.md",
        settings.base_dir.parent / "README.md",
    ]
    tech_summary_md = ""
    for p in tech_summary_paths:
        if p.exists():
            tech_summary_md = p.read_text(encoding="utf-8")
            break

    if not tech_summary_md:
        tech_summary_md = (
            "# South African Gardener Guide - Technical Summary\n\n"
            "This document outlines the architecture, RAG grounding, and multi-agent "
            "workflow designed for the South African Gardener AI Guide.\n"
        )

    return {
        "crops_json": crops_json,
        "suburbs_csv": suburbs_csv,
        "pdf_tables": {
            "table_1_soil_treatment": table_1,
            "table_2_watering_rules": table_2,
        },
        "demo_calendar_events": calendar_events,
        "demo_gardener_emails": gardener_emails,
        "technical_summary_md": tech_summary_md,
    }


@app.get("/api/data/sources")
async def get_data_sources() -> dict[str, Any]:
    """Return all source fixtures and parsed tables for the reference inspector."""
    return _load_data_sources()


@app.get("/api/agent/fixtures")
async def get_agent_fixtures() -> dict[str, Any]:
    """Return raw fixture data for calendar events and gardener emails."""
    events, _ = fetch_calendar_events(mode="demo")
    emails, _ = fetch_gardener_emails(mode="demo")
    return {
        "calendar_events": [e.model_dump() for e in events],
        "raw_emails": [m.model_dump() for m in emails],
    }


@app.post("/api/agent/run", response_model=AgentRunResponse)
async def run_agent_endpoint(
    request: AgentRunRequest = AgentRunRequest(),
) -> AgentRunResponse:
    """Execute end-to-end multi-tool verification workflow across calendar, emails, GBIF, and weather."""
    return run_verification_agent(mode=request.mode)

