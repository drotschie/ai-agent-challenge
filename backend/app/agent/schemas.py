"""Pydantic v2 schemas for Part 2 Autonomous Multi-Tool Verification Agent."""

from typing import Any
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Scheduled planting appointment in community calendar."""

    event_id: str
    scheduled_date: str
    suburb: str
    plot_id: str
    gardener_name: str
    gardener_email: str
    notes: str = ""


class RawEmailMessage(BaseModel):
    """Raw gardener email message before extraction."""

    email_id: str
    sender_name: str
    sender_email: str
    received_at: str
    subject: str
    body: str
    parsed_hints: dict[str, Any] = Field(default_factory=dict)


class ExtractedEmailRecord(BaseModel):
    """Structured planting record extracted from a single email."""

    email_id: str
    sender_name: str
    sender_email: str
    received_at: str
    planted_date_raw: str | None = None
    suburb: str | None = None
    plot_id: str | None = None
    crop_name: str | None = None
    species_scientific_raw: str | None = None
    quantity_planted: int | None = None
    measured_soil_ph: float | None = None
    seed_batch_id: str | None = None


class CleanedMergedRecord(BaseModel):
    """Cleaned record deduplicated and merged across follow-up emails."""

    record_id: str
    source_email_ids: list[str]
    raw_emails_before: list[RawEmailMessage]
    merge_audit_log: list[str] = Field(default_factory=list)
    gardener_name: str
    gardener_email: str
    suburb: str
    plot_id: str
    planted_date: str
    crop_name: str | None = None
    species_scientific_raw: str | None = None
    quantity_planted: int | None = None
    measured_soil_ph: float | None = None
    seed_batch_id: str | None = None


class VerifiedPlantingRecord(BaseModel):
    """End-to-end verified planting record with external validation flags."""

    record_id: str
    source_email_ids: list[str]
    raw_emails_before: list[RawEmailMessage]
    merge_audit_log: list[str] = Field(default_factory=list)
    gardener_name: str
    gardener_email: str
    suburb: str
    soil_type: str
    plot_id: str
    planted_date: str
    crop_name: str
    species_scientific_raw: str
    species_scientific_verified: str
    gbif_match_confidence: int
    quantity_planted: int | None = None
    measured_soil_ph: float | None = None
    ideal_ph_range: str
    seed_batch_id: str | None = None
    soil_treatment_recommendation: str
    weather_advisory: str
    status: str
    flags: list[str] = Field(default_factory=list)


class WorkflowNodeTrace(BaseModel):
    """Audit trace for a single node in the LangGraph workflow."""

    node_id: str
    step_number: int
    label: str
    status: str = "completed"
    duration_ms: int
    summary_text: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunSummary(BaseModel):
    """Summary counts for a verification run."""

    raw_emails_count: int
    calendar_events_count: int
    merged_records_count: int
    verified_count: int
    auto_corrected_count: int
    flagged_count: int


class AgentRunRequest(BaseModel):
    """Request payload to trigger an agent verification run."""

    mode: str = "demo"


class AgentRunResponse(BaseModel):
    """Complete response payload for an agent verification run."""

    run_id: str
    mode_used: str
    summary: AgentRunSummary
    workflow_nodes: list[WorkflowNodeTrace]
    records: list[VerifiedPlantingRecord]
    csv_export: str
