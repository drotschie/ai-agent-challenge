"""Pydantic v2 data models for Part 1 Structured RAG."""

from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Document chunk extracted from structured source files."""

    chunk_id: str
    source_file: str
    locator: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """Retrieved document chunk with cosine similarity score."""

    chunk_id: str
    source_file: str
    locator: str
    similarity: float
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Chat message in conversation history."""

    role: str
    content: str


class SubQuery(BaseModel):
    """Sub-query targeted at a specific reference source."""

    target_source: str
    query: str


class QueryTransformResult(BaseModel):
    """Structured result from conversational query transformation."""

    resolved_question: str
    detected_suburb: str | None = None
    detected_crops: list[str] = Field(default_factory=list)
    detected_soil_ph: float | None = None
    sub_queries: list[SubQuery] = Field(default_factory=list)


class LiveWeatherInfo(BaseModel):
    """Live weather observation and regional soil baseline."""

    suburb: str
    temperature_c: float
    condition: str
    humidity_pct: int
    precipitation_mm: float
    soil_moisture: float
    frost_risk_7d: bool
    baseline_ph_range: str
    soil_type: str
    source: str = "Open-Meteo API & Regional Datasets"


class RecommendedCropCard(BaseModel):
    """Crop recommendation card with optimal parameters and citation."""

    crop_name: str
    scientific_name: str
    description: str
    optimal_ph: str
    water_mm_per_week: int
    citation: str


class CitationItem(BaseModel):
    """Citation referencing a specific chunk and source."""

    source_file: str
    locator: str
    label: str


class RagQueryRequest(BaseModel):
    """Request payload for RAG query endpoint."""

    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)


class RagQueryResponse(BaseModel):
    """Full response payload for RAG query endpoint."""

    answer: str
    action_banner: str | None = None
    query_transform: QueryTransformResult
    live_weather: LiveWeatherInfo | None = None
    recommended_crops: list[RecommendedCropCard] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
