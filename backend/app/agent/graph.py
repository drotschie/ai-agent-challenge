"""Five-node LangGraph orchestration workflow for Autonomous Verification Agent."""

import csv
import io
import logging
import time
from typing import Any, TypedDict
import uuid

from langgraph.graph import END, START, StateGraph

from app.agent.normalizer import cleanse_and_merge_records
from app.agent.schemas import (
    AgentRunResponse,
    AgentRunSummary,
    CalendarEvent,
    CleanedMergedRecord,
    ExtractedEmailRecord,
    RawEmailMessage,
    VerifiedPlantingRecord,
    WorkflowNodeTrace,
)
from app.agent.tools.calendar_tool import fetch_calendar_events
from app.agent.tools.email_tool import extract_all_emails, fetch_gardener_emails
from app.agent.verifier import verify_all_records

logger = logging.getLogger(__name__)


class AgentGraphState(TypedDict, total=False):
    """Execution state schema passed across nodes in the LangGraph workflow."""

    mode: str
    mode_used: str
    calendar_events: list[CalendarEvent]
    raw_emails: list[RawEmailMessage]
    extracted_records: list[ExtractedEmailRecord]
    merged_records: list[CleanedMergedRecord]
    verified_records: list[VerifiedPlantingRecord]
    workflow_nodes: list[WorkflowNodeTrace]
    summary: AgentRunSummary | None
    csv_export: str


def ingest_sources(state: AgentGraphState) -> dict[str, Any]:
    """Node 1: Load calendar events and gardener emails from Google OAuth or fixtures."""
    start_time = time.perf_counter()
    mode = state.get("mode", "demo")

    calendar_events, cal_mode = fetch_calendar_events(mode=mode)
    raw_emails, mail_mode = fetch_gardener_emails(mode=mode)
    mode_used = "google_oauth" if (cal_mode == "google_oauth" and mail_mode == "google_oauth") else "demo"

    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    trace = WorkflowNodeTrace(
        node_id="ingest_sources",
        step_number=1,
        label="1. Read Calendar & Emails",
        status="completed",
        duration_ms=duration_ms,
        summary_text=f"Loaded {len(calendar_events)} scheduled events & {len(raw_emails)} raw gardener emails",
        input_payload={"mode_requested": mode, "tools": ["calendar_tool", "email_tool"]},
        output_payload={
            "calendar_events_count": len(calendar_events),
            "raw_emails_count": len(raw_emails),
            "mode_used": mode_used,
            "sample_calendar_event": calendar_events[0].model_dump() if calendar_events else {},
            "sample_raw_email": {
                "email_id": raw_emails[0].email_id,
                "sender_email": raw_emails[0].sender_email,
                "subject": raw_emails[0].subject,
                "body": raw_emails[0].body,
            } if raw_emails else {},
        },
    )

    workflow_nodes = list(state.get("workflow_nodes", []))
    workflow_nodes.append(trace)

    return {
        "calendar_events": calendar_events,
        "raw_emails": raw_emails,
        "mode_used": mode_used,
        "workflow_nodes": workflow_nodes,
    }


def extract_email_records(state: AgentGraphState) -> dict[str, Any]:
    """Node 2: Extract structured agronomic entities from unstructured emails."""
    start_time = time.perf_counter()
    raw_emails: list[RawEmailMessage] = state.get("raw_emails", [])
    extracted = extract_all_emails(raw_emails)

    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    trace = WorkflowNodeTrace(
        node_id="extract_email_records",
        step_number=2,
        label="2. Extract Email Entities",
        status="completed",
        duration_ms=duration_ms,
        summary_text=f"Extracted structured fields from {len(extracted)} unstructured emails (null-safe)",
        input_payload={"raw_emails_count": len(raw_emails), "schema": "ExtractedEmailRecord"},
        output_payload={
            "extracted_records_count": len(extracted),
            "sample_extracted": [r.model_dump() for r in extracted[:2]],
        },
    )

    workflow_nodes = list(state.get("workflow_nodes", []))
    workflow_nodes.append(trace)

    return {
        "extracted_records": extracted,
        "workflow_nodes": workflow_nodes,
    }


def cleanse_and_deduplicate(state: AgentGraphState) -> dict[str, Any]:
    """Node 3: Normalize dates and plot IDs, merge follow-up emails, and deduplicate."""
    start_time = time.perf_counter()
    extracted: list[ExtractedEmailRecord] = state.get("extracted_records", [])
    raw_emails: list[RawEmailMessage] = state.get("raw_emails", [])
    merged = cleanse_and_merge_records(extracted, raw_emails)

    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    merge_logs = [log for m in merged for log in m.merge_audit_log]
    trace = WorkflowNodeTrace(
        node_id="cleanse_and_deduplicate",
        step_number=3,
        label="3. Cleanse & Deduplicate",
        status="completed",
        duration_ms=duration_ms,
        summary_text=f"Normalized dates/IDs & merged {len(extracted)} emails into {len(merged)} unique plot records",
        input_payload={
            "extracted_records_count": len(extracted),
            "dedup_key": "(gardener_email, plot_id, planted_date_iso)",
        },
        output_payload={
            "merged_records_count": len(merged),
            "duplicates_merged": len(extracted) - len(merged),
            "merge_audit_log": merge_logs,
        },
    )

    workflow_nodes = list(state.get("workflow_nodes", []))
    workflow_nodes.append(trace)

    return {
        "merged_records": merged,
        "workflow_nodes": workflow_nodes,
    }


def verify_against_rules(state: AgentGraphState) -> dict[str, Any]:
    """Node 4: Execute 5-way cross-tool verification across Calendar, GBIF, Weather, and Part 1 data."""
    start_time = time.perf_counter()
    merged: list[CleanedMergedRecord] = state.get("merged_records", [])
    calendar_events: list[CalendarEvent] = state.get("calendar_events", [])
    verified = verify_all_records(merged, calendar_events)

    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    trace = WorkflowNodeTrace(
        node_id="verify_against_rules",
        step_number=4,
        label="4. Verify Rules, GBIF & Weather",
        status="completed",
        duration_ms=duration_ms,
        summary_text=f"Verified {len(verified)} records against Calendar, GBIF, Open-Meteo & Part 1 pH rules",
        input_payload={
            "merged_records_count": len(merged),
            "calendar_events_count": len(calendar_events),
            "external_verifiers": ["Google Calendar Schedule", "GBIF Species API", "Open-Meteo 7d Forecast", "Part 1 3-File pH & Lime Join"],
        },
        output_payload={
            "verified_records_count": len(verified),
            "flags_by_record": {r.record_id: r.flags for r in verified if r.flags},
        },
    )

    workflow_nodes = list(state.get("workflow_nodes", []))
    workflow_nodes.append(trace)

    return {
        "verified_records": verified,
        "workflow_nodes": workflow_nodes,
    }


def compile_audit_report(state: AgentGraphState) -> dict[str, Any]:
    """Node 5: Calculate summary metrics, compile CSV export, and complete graph execution."""
    start_time = time.perf_counter()
    verified_records: list[VerifiedPlantingRecord] = state.get("verified_records", [])
    raw_emails: list[RawEmailMessage] = state.get("raw_emails", [])
    calendar_events: list[CalendarEvent] = state.get("calendar_events", [])
    merged_records: list[CleanedMergedRecord] = state.get("merged_records", [])

    verified_count = sum(1 for r in verified_records if r.status == "VERIFIED")
    auto_corrected_count = sum(1 for r in verified_records if r.status == "AUTO_CORRECTED")
    flagged_count = sum(1 for r in verified_records if r.status == "FLAGGED")

    summary = AgentRunSummary(
        raw_emails_count=len(raw_emails),
        calendar_events_count=len(calendar_events),
        merged_records_count=len(merged_records),
        verified_count=verified_count,
        auto_corrected_count=auto_corrected_count,
        flagged_count=flagged_count,
    )

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "record_id",
        "gardener_name",
        "suburb",
        "plot_id",
        "planted_date",
        "crop_name",
        "species_scientific_verified",
        "quantity_planted",
        "measured_soil_ph",
        "seed_batch_id",
        "status",
        "flags",
    ])
    for r in verified_records:
        writer.writerow([
            r.record_id,
            r.gardener_name,
            r.suburb,
            r.plot_id,
            r.planted_date,
            r.crop_name,
            r.species_scientific_verified,
            r.quantity_planted if r.quantity_planted is not None else "",
            f"{r.measured_soil_ph:.1f}" if r.measured_soil_ph is not None else "",
            r.seed_batch_id or "",
            r.status,
            ";".join(r.flags),
        ])
    csv_export = out.getvalue()

    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    trace = WorkflowNodeTrace(
        node_id="compile_audit_report",
        step_number=5,
        label="5. Compile Audit & CSV Export",
        status="completed",
        duration_ms=duration_ms,
        summary_text=(
            f"Compiled audit metrics ({verified_count} verified, "
            f"{auto_corrected_count} auto-corrected, {flagged_count} flagged) & exported CSV"
        ),
        input_payload={"verified_records_count": len(verified_records)},
        output_payload={
            "summary": summary.model_dump(),
            "csv_rows_count": len(verified_records),
        },
    )

    workflow_nodes = list(state.get("workflow_nodes", []))
    workflow_nodes.append(trace)

    return {
        "summary": summary,
        "csv_export": csv_export,
        "workflow_nodes": workflow_nodes,
    }


def build_verification_graph():
    """Build and compile the 5-node StateGraph verification workflow."""
    workflow = StateGraph(AgentGraphState)

    workflow.add_node("ingest_sources", ingest_sources)
    workflow.add_node("extract_email_records", extract_email_records)
    workflow.add_node("cleanse_and_deduplicate", cleanse_and_deduplicate)
    workflow.add_node("verify_against_rules", verify_against_rules)
    workflow.add_node("compile_audit_report", compile_audit_report)

    workflow.add_edge(START, "ingest_sources")
    workflow.add_edge("ingest_sources", "extract_email_records")
    workflow.add_edge("extract_email_records", "cleanse_and_deduplicate")
    workflow.add_edge("cleanse_and_deduplicate", "verify_against_rules")
    workflow.add_edge("verify_against_rules", "compile_audit_report")
    workflow.add_edge("compile_audit_report", END)

    return workflow.compile()


def run_verification_agent(mode: str = "demo") -> AgentRunResponse:
    """Execute the end-to-end multi-tool verification workflow."""
    app = build_verification_graph()
    initial_state: AgentGraphState = {
        "mode": mode,
        "mode_used": "demo",
        "calendar_events": [],
        "raw_emails": [],
        "extracted_records": [],
        "merged_records": [],
        "verified_records": [],
        "workflow_nodes": [],
        "summary": None,
        "csv_export": "",
    }
    result = app.invoke(initial_state)

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    return AgentRunResponse(
        run_id=run_id,
        mode_used=str(result.get("mode_used", "demo")),
        summary=result["summary"],
        workflow_nodes=result.get("workflow_nodes", []),
        records=result.get("verified_records", []),
        csv_export=str(result.get("csv_export", "")),
    )
