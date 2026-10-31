"use client";

import React, { useRef, useState } from "react";
import "@xyflow/react/dist/style.css";
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import {
  AgentRunResponse,
  INITIAL_AGENT_RESPONSE,
  VerifiedPlantingRecord,
  WorkflowNodeTrace,
  runVerificationAgentApi,
} from "@/lib/api";

function SpinnerIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 animate-spin text-canvas"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function KeyIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 2l-2 2m-1.5 1.5L14 9l-3-3 2.5-2.5" />
      <circle cx="7.5" cy="16.5" r="5.5" />
      <path d="m11.5 12.5 4 4" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function ShieldCheckIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function CheckDotIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-4 h-4 text-forest mt-0.5 flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function ChevronDownIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className={`w-4 h-4 text-muted transition-transform duration-150 ${
        expanded ? "rotate-180" : ""
      }`}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function formatSoilType(raw?: string): string {
  if (!raw) return "Loam";
  return raw
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function parseIdealRange(idealRange: string): { min: number; max: number } {
  const parts = idealRange.split("-").map((s) => parseFloat(s.trim()));
  if (parts.length === 2 && !Number.isNaN(parts[0]) && !Number.isNaN(parts[1])) {
    return { min: parts[0], max: parts[1] };
  }
  return { min: 6.0, max: 6.8 };
}

function getSoilPhState(rec: VerifiedPlantingRecord): {
  badge: string;
  tone: "good" | "bad";
  explanation: string;
} {
  if (rec.measured_soil_ph === null) {
    return {
      badge: "Soil Test Missing",
      tone: "bad",
      explanation: `The gardener has not sent a soil pH reading yet (${rec.crop_name} needs pH ${rec.ideal_ph_range}).`,
    };
  }
  const { min, max } = parseIdealRange(rec.ideal_ph_range);
  if (rec.measured_soil_ph < min) {
    return {
      badge: "Too Acidic (Needs Lime)",
      tone: "bad",
      explanation: `Measured pH ${rec.measured_soil_ph.toFixed(1)} is too acidic for ${rec.crop_name}, which needs pH ${rec.ideal_ph_range} to absorb nutrients.`,
    };
  }
  if (rec.measured_soil_ph > max) {
    return {
      badge: "Too Alkaline (Needs Sulfur)",
      tone: "bad",
      explanation: `Measured pH ${rec.measured_soil_ph.toFixed(1)} is too alkaline for ${rec.crop_name}, which needs pH ${rec.ideal_ph_range}.`,
    };
  }
  return {
    badge: "Healthy Soil pH",
    tone: "good",
    explanation: `Measured pH ${rec.measured_soil_ph.toFixed(1)} sits inside the healthy ${rec.ideal_ph_range} range for ${rec.crop_name}.`,
  };
}

function formatPlainMergeSteps(rec: VerifiedPlantingRecord): string[] {
  const steps: string[] = [];
  if (rec.raw_emails_before.length > 1) {
    steps.push(
      `Combined ${rec.raw_emails_before.length} separate emails from ${rec.gardener_name} into 1 complete planting record.`
    );
  } else {
    steps.push(
      `Received 1 email submission from ${rec.gardener_name} for Plot ${rec.plot_id}.`
    );
  }

  for (const rawMsg of rec.merge_audit_log) {
    const lower = rawMsg.toLowerCase();
    if (lower.includes("measured_soil_ph")) {
      steps.push(
        `Added the missing soil pH reading (${rec.measured_soil_ph !== null ? rec.measured_soil_ph.toFixed(1) : "none"}) from the follow-up email.`
      );
    } else if (lower.includes("seed_batch_id") && rec.seed_batch_id) {
      steps.push(
        `Added the seed packet batch number (${rec.seed_batch_id}) from the follow-up email.`
      );
    } else if (lower.includes("quantity_planted") && rec.quantity_planted !== null) {
      steps.push(
        `Updated the planted quantity to ${rec.quantity_planted} plants from the follow-up email.`
      );
    } else if (lower.includes("plot_id") && !lower.includes("by sender_email")) {
      steps.push(`Matched plot number ${rec.plot_id} from the follow-up email.`);
    }
  }

  if (
    rec.species_scientific_raw &&
    rec.species_scientific_verified &&
    rec.species_scientific_raw.toLowerCase() !==
      rec.species_scientific_verified.toLowerCase()
  ) {
    steps.push(
      `Fixed a spelling mistake in the plant's scientific name (${rec.species_scientific_raw} corrected to ${rec.species_scientific_verified}).`
    );
  }

  return steps;
}

function formatPlainTreatment(rec: VerifiedPlantingRecord): string {
  const soilState = getSoilPhState(rec);
  if (soilState.tone === "good") {
    return `No soil treatment needed: pH ${rec.measured_soil_ph?.toFixed(1)} is already in the ideal ${rec.ideal_ph_range} range.`;
  }
  if (rec.measured_soil_ph === null) {
    return `Wait for ${rec.gardener_name} to test the soil pH before adding Lime or Sulfur.`;
  }
  return rec.soil_treatment_recommendation
    .replace(/sandy_loam/gi, "Sandy Loam")
    .replace(/clay_loam/gi, "Clay Loam")
    .replace(/->/g, "to");
}

function getPlainVerdict(rec: VerifiedPlantingRecord): {
  title: string;
  mainReason: string;
  actionRequired: string;
  autoHandled: string | null;
} {
  const soilState = getSoilPhState(rec);
  const hasTypo =
    rec.species_scientific_raw &&
    rec.species_scientific_verified &&
    rec.species_scientific_raw.toLowerCase() !==
      rec.species_scientific_verified.toLowerCase();
  const hasMultiEmail = rec.raw_emails_before.length > 1;

  const autoFixes: string[] = [];
  if (hasMultiEmail) {
    autoFixes.push(
      `combined ${rec.raw_emails_before.length} emails from ${rec.gardener_name} into one record`
    );
  }
  if (hasTypo) {
    autoFixes.push(
      `fixed the spelling of the scientific name (${rec.species_scientific_raw} to ${rec.species_scientific_verified})`
    );
  }
  const autoHandled =
    autoFixes.length > 0
      ? `Already handled automatically: The system ${autoFixes.join(" and ")}.`
      : null;

  if (rec.status === "FLAGGED") {
    const reasons: string[] = [];
    if (rec.flags.includes("SOIL_PH_OUT_OF_RANGE")) {
      reasons.push(soilState.explanation);
    }
    if (rec.flags.includes("MISSING_REQUIRED_FIELDS")) {
      const missing: string[] = [];
      if (rec.measured_soil_ph === null) missing.push("soil pH test reading");
      if (!rec.seed_batch_id) missing.push("seed batch number");
      if (rec.quantity_planted === null) missing.push("number of plants");
      reasons.push(
        `The gardener's email is missing required details (${missing.join(" and ") || "soil pH or batch ID"}).`
      );
    }
    if (rec.flags.includes("UNSCHEDULED_PLANTING")) {
      reasons.push(
        `Plot ${rec.plot_id} was not booked on the community garden calendar for this planting.`
      );
    }
    if (
      rec.flags.includes("WEATHER_FROST_WARNING") ||
      rec.flags.includes("HEAT_STRESS_WARNING")
    ) {
      reasons.push(`Weather risk detected in the 7-day forecast (${rec.weather_advisory}).`);
    }

    return {
      title: "Why This Plot Is Flagged for Review",
      mainReason:
        reasons.join(" ") ||
        "The soil pH or planting details need attention before this bed passes inspection.",
      actionRequired: formatPlainTreatment(rec),
      autoHandled,
    };
  }

  if (rec.status === "AUTO_CORRECTED") {
    return {
      title: "Fixed Automatically (No Action Needed)",
      mainReason: `${soilState.explanation} The plot is booked on the calendar and the 7-day weather forecast is safe.`,
      actionRequired: "No manual intervention needed. All minor email or spelling issues were resolved automatically.",
      autoHandled,
    };
  }

  return {
    title: "All Checks Passed (Verified Clean)",
    mainReason: `${soilState.explanation} The plot matches the calendar schedule and the scientific name is accurate.`,
    actionRequired: "No action needed. This planting bed is healthy and ready to grow.",
    autoHandled,
  };
}

function getRowSummaryText(rec: VerifiedPlantingRecord): string {
  const soilState = getSoilPhState(rec);
  if (rec.status === "FLAGGED") {
    if (rec.flags.includes("SOIL_PH_OUT_OF_RANGE")) {
      return `${soilState.badge}: measured pH ${rec.measured_soil_ph?.toFixed(1)} vs ideal ${rec.ideal_ph_range}`;
    }
    if (rec.flags.includes("MISSING_REQUIRED_FIELDS")) {
      return "Missing soil pH reading or seed batch number in email";
    }
    if (rec.flags.includes("UNSCHEDULED_PLANTING")) {
      return "Plot was not booked on the garden calendar";
    }
    return "Needs manual review before approval";
  }
  if (rec.status === "AUTO_CORRECTED") {
    return "Soil pH is healthy; plant spelling or follow-up email fixed automatically";
  }
  return "Healthy soil pH, accurate plant name, and matching calendar booking";
}

export function AgentWorkspace() {
  const [agentData, setAgentData] = useState<AgentRunResponse>(INITIAL_AGENT_RESPONSE);
  const [mode, setMode] = useState<"demo" | "google_oauth">("demo");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("ingest_sources");
  const [selectedRecord, setSelectedRecord] = useState<VerifiedPlantingRecord | null>(
    INITIAL_AGENT_RESPONSE.records[0] || null
  );

  // Progressive disclosure states so panels open cleanly without overwhelming walls of text
  const [showNodePayloads, setShowNodePayloads] = useState<boolean>(false);
  const [showRawEmails, setShowRawEmails] = useState<boolean>(false);

  const inspectorRef = useRef<HTMLElement | null>(null);
  const nodeInspectorRef = useRef<HTMLDivElement | null>(null);
  const rawEmailsContainerRef = useRef<HTMLDivElement | null>(null);

  const scrollIntoFrame = (el: HTMLElement | null) => {
    if (!el) return;
    window.setTimeout(() => {
      const rect = el.getBoundingClientRect();
      if (rect.bottom > window.innerHeight - 24 || rect.top < 88) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }, 70);
  };

  const scrollToInspector = () => {
    window.setTimeout(() => {
      inspectorRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 60);
  };

  const handleRunAgent = async () => {
    setIsLoading(true);
    try {
      const result = await runVerificationAgentApi(mode);
      setAgentData(result);
      if (result.records && result.records.length > 0) {
        setSelectedRecord(result.records[0]);
      }
      scrollToInspector();
    } finally {
      setIsLoading(false);
    }
  };

  const handleInspectRecord = (rec: VerifiedPlantingRecord) => {
    setSelectedRecord(rec);
    setShowRawEmails(false);
    scrollToInspector();
  };

  const handleDownloadCsv = () => {
    const csvContent = agentData.csv_export || "";
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "verified_cape_plantings.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const selectedNode: WorkflowNodeTrace | undefined =
    agentData.workflow_nodes.find((n) => n.node_id === selectedNodeId) ||
    agentData.workflow_nodes[0];

  const flowNodes: Node[] = agentData.workflow_nodes.map((node, idx) => {
    const isSelected = node.node_id === selectedNodeId;
    return {
      id: node.node_id,
      position: { x: idx * 250 + 20, y: 65 },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      type: idx === 0 ? "input" : idx === agentData.workflow_nodes.length - 1 ? "output" : "default",
      data: {
        label: (
          <div className="text-left select-none">
            <div className="font-semibold text-xs leading-tight truncate">
              {node.label}
            </div>
            <div className="text-[11px] opacity-85 leading-snug truncate mt-1">
              {node.summary_text}
            </div>
            <div className="text-[10px] font-sans mt-1 opacity-75 tabular-nums">
              {node.duration_ms} ms
            </div>
          </div>
        ),
      },
      style: {
        background: isSelected ? "#556B5A" : "#FFF7EA",
        color: isSelected ? "#FFF7EA" : "#1C2820",
        border: isSelected ? "2px solid #1C2820" : "2px solid #8FB08A",
        borderRadius: "14px",
        padding: "10px 14px",
        width: 210,
        fontSize: "12px",
        cursor: "pointer",
        boxShadow: isSelected ? "0 4px 12px rgba(28,40,32,0.15)" : "none",
      },
    };
  });

  const flowEdges: Edge[] = agentData.workflow_nodes.slice(0, -1).map((node, idx) => ({
    id: `edge-${idx}`,
    source: node.node_id,
    target: agentData.workflow_nodes[idx + 1].node_id,
    animated: true,
    style: { stroke: "#556B5A", strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#556B5A",
    },
  }));

  const verdict = selectedRecord ? getPlainVerdict(selectedRecord) : null;
  const soilState = selectedRecord ? getSoilPhState(selectedRecord) : null;
  const plainMergeSteps = selectedRecord ? formatPlainMergeSteps(selectedRecord) : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Top Control Bar */}
      <section className="bg-surface border-2 border-mint rounded-2xl p-6 shadow-sm space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <h1 className="font-display text-2xl sm:text-3xl font-semibold text-ink">
              Planting Log Verification Agent
            </h1>
            <p className="text-base text-muted max-w-2xl leading-relaxed">
              Merges gardener emails with bookings and checks plants, soil pH, and weather.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleRunAgent}
              disabled={isLoading}
              className="min-h-[44px] px-5 rounded-full font-medium text-sm whitespace-nowrap inline-flex items-center gap-2 bg-forest hover:bg-muted text-canvas transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest disabled:opacity-50"
            >
              {isLoading ? <SpinnerIcon /> : <PlayIcon />}
              <span>{isLoading ? "Running Audit..." : "Run Verification Audit"}</span>
            </button>

            <button
              type="button"
              onClick={handleDownloadCsv}
              className="min-h-[44px] px-4 rounded-full font-medium text-sm whitespace-nowrap inline-flex items-center gap-2 bg-sand hover:bg-sand-border text-ink transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              <DownloadIcon />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Mode Selector Pills */}
        <div className="pt-3 border-t border-sand flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold text-muted">Source Mode:</span>
          <button
            type="button"
            onClick={() => setMode("demo")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              mode === "demo"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <PlayIcon />
            <span>Demo Fixtures</span>
          </button>

          <button
            type="button"
            onClick={() => setMode("google_oauth")}
            className={`min-h-[44px] px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              mode === "google_oauth"
                ? "bg-forest text-canvas border-2 border-forest"
                : "bg-canvas text-ink border-2 border-mint hover:bg-sand"
            }`}
          >
            <KeyIcon />
            <span>Live Google OAuth</span>
          </button>
        </div>
      </section>

      {/* Summary Metric Strip */}
      <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Emails Received</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-ink">
            {agentData.summary.raw_emails_count}
          </p>
        </div>

        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Booked Plots</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-ink">
            {agentData.summary.calendar_events_count}
          </p>
        </div>

        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Combined Plots</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-ink">
            {agentData.summary.merged_records_count}
          </p>
        </div>

        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Passed Clean</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-forest">
            {agentData.summary.verified_count}
          </p>
        </div>

        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Auto-Fixed</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-ochre">
            {agentData.summary.auto_corrected_count}
          </p>
        </div>

        <div className="bg-surface border border-sand rounded-xl p-4 space-y-1">
          <p className="text-xs font-semibold text-muted">Needs Review</p>
          <p className="font-display text-2xl sm:text-3xl font-semibold tabular-nums text-terracotta">
            {agentData.summary.flagged_count}
          </p>
        </div>
      </section>

      {/* Plain-English Record Inspector Panel */}
      {selectedRecord && verdict && soilState && (
        <section
          ref={inspectorRef}
          className="scroll-mt-24 bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-5"
        >
          {/* Header Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sand pb-4">
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-sand text-ink">
                  {selectedRecord.record_id}
                </span>
                <h2 className="font-display text-xl sm:text-2xl font-semibold text-ink">
                  {selectedRecord.gardener_name}: Plot {selectedRecord.plot_id} ({selectedRecord.suburb})
                </h2>
              </div>
              <p className="text-sm text-muted mt-1">
                Planted <strong className="text-ink">{selectedRecord.crop_name}</strong> on{" "}
                <strong className="tabular-nums text-ink">{selectedRecord.planted_date}</strong> in{" "}
                <strong className="text-ink">{formatSoilType(selectedRecord.soil_type)}</strong> soil
              </p>
            </div>

            <div>
              {selectedRecord.status === "VERIFIED" && (
                <span className="bg-mint text-ink px-4 py-1.5 rounded-full text-xs font-semibold inline-block">
                  PASSED ALL CHECKS
                </span>
              )}
              {selectedRecord.status === "AUTO_CORRECTED" && (
                <span className="bg-ochre/20 text-ink border border-ochre/50 px-4 py-1.5 rounded-full text-xs font-semibold inline-block">
                  FIXED AUTOMATICALLY
                </span>
              )}
              {selectedRecord.status === "FLAGGED" && (
                <span className="bg-terracotta/15 text-terracotta border border-terracotta/40 px-4 py-1.5 rounded-full text-xs font-semibold inline-block">
                  NEEDS SOIL OR RECORD ACTION
                </span>
              )}
            </div>
          </div>

          {/* Plain-English Verdict Box (Explains the Discrepancy Immediately) */}
          <div
            className={`rounded-xl p-5 border space-y-2.5 ${
              selectedRecord.status === "FLAGGED"
                ? "bg-terracotta/10 border-terracotta/30"
                : selectedRecord.status === "AUTO_CORRECTED"
                ? "bg-ochre/10 border-ochre/40"
                : "bg-mint/40 border-sage"
            }`}
          >
            <h3
              className={`font-display text-lg font-semibold ${
                selectedRecord.status === "FLAGGED" ? "text-terracotta" : "text-ink"
              }`}
            >
              {verdict.title}
            </h3>
            <p className="text-base text-ink leading-relaxed">
              <strong>What we found:</strong> {verdict.mainReason}
            </p>
            <p className="text-base text-ink leading-relaxed">
              <strong>What to do next:</strong> {verdict.actionRequired}
            </p>
            {verdict.autoHandled && (
              <p className="text-sm text-muted pt-1 border-t border-sand">
                {verdict.autoHandled}
              </p>
            )}
          </div>

          {/* Two-Column Breakdown: What Gardener Sent vs What System Checked */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: What the Gardener Sent */}
            <div
              ref={rawEmailsContainerRef}
              className="bg-surface border border-sand rounded-xl p-5 space-y-4"
            >
              <div className="flex items-center justify-between gap-2 pb-3 border-b border-sand">
                <div className="flex items-center gap-2">
                  <MailIcon />
                  <h3 className="text-base font-semibold text-ink">
                    1. What the Gardener Sent ({selectedRecord.raw_emails_before.length}{" "}
                    {selectedRecord.raw_emails_before.length === 1 ? "Email" : "Emails"})
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setShowRawEmails((prev) => {
                      const next = !prev;
                      if (next) scrollIntoFrame(rawEmailsContainerRef.current);
                      return next;
                    })
                  }
                  className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-canvas hover:bg-sand border border-sand text-xs font-semibold text-forest whitespace-nowrap inline-flex items-center gap-1.5 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                >
                  <span>{showRawEmails ? "Hide original emails" : "Read original emails"}</span>
                  <ChevronDownIcon expanded={showRawEmails} />
                </button>
              </div>

              {/* Plain-English Steps Taken on the Emails */}
              <div className="space-y-2.5">
                <p className="text-xs font-semibold text-muted">
                  How the system cleaned up the submission:
                </p>
                <ul className="space-y-2.5">
                  {plainMergeSteps.map((stepText, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-ink flex items-start gap-2.5 leading-relaxed"
                    >
                      <CheckDotIcon />
                      <span>{stepText}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Expandable Original Email Bodies */}
              {showRawEmails ? (
                <div className="space-y-3 pt-3 border-t border-sand">
                  {selectedRecord.raw_emails_before.map((email, eIdx) => (
                    <div
                      key={email.email_id}
                      className="bg-canvas border border-sand rounded-xl p-4 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-forest">
                          Email {eIdx + 1} of {selectedRecord.raw_emails_before.length} ({email.email_id})
                        </span>
                        <span className="text-muted font-mono tabular-nums">
                          {email.received_at.split("T")[0]}{" "}
                          {email.received_at.split("T")[1]?.slice(0, 5)}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-ink">
                        Subject: {email.subject}
                      </p>
                      <p className="text-sm text-ink bg-surface p-3 rounded-lg border border-sand leading-relaxed">
                        &quot;{email.body}&quot;
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-canvas border border-sand rounded-xl p-3.5 text-sm text-muted">
                  Latest email subject:{" "}
                  <strong className="text-ink">
                    {selectedRecord.raw_emails_before[
                      selectedRecord.raw_emails_before.length - 1
                    ]?.subject || "Planting update"}
                  </strong>
                </div>
              )}
            </div>

            {/* Right Column: Side-by-Side Checks */}
            <div className="bg-surface border border-sand rounded-xl p-5 space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-sand">
                <ShieldCheckIcon />
                <h3 className="text-base font-semibold text-ink">
                  2. What the System Checked
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-sm">
                {/* Check 1: Plant Name & Spelling */}
                <div className="bg-canvas border border-sand rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-muted">
                      Plant Name Check
                    </span>
                    {selectedRecord.species_scientific_raw !==
                    selectedRecord.species_scientific_verified ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-ochre/25 text-ink border border-ochre/50">
                        AI Fixed Typo
                      </span>
                    ) : (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-mint text-ink">
                        Spelled Right
                      </span>
                    )}
                  </div>
                  <p className="font-semibold text-base text-ink">
                    {selectedRecord.crop_name}
                  </p>
                  {selectedRecord.species_scientific_raw !==
                    selectedRecord.species_scientific_verified && (
                    <div className="text-xs text-ink flex flex-wrap items-center gap-1.5">
                      <span className="text-muted">Typo in email:</span>
                      <span className="font-mono font-semibold line-through text-terracotta bg-terracotta/15 px-1.5 py-0.5 rounded">
                        {selectedRecord.species_scientific_raw}
                      </span>
                    </div>
                  )}
                  <div className="text-xs text-ink flex flex-wrap items-center gap-1.5">
                    <span className="text-muted">Verified name:</span>
                    <strong className="font-mono text-forest bg-mint/60 px-1.5 py-0.5 rounded">
                      {selectedRecord.species_scientific_verified}
                    </strong>
                  </div>
                </div>

                {/* Check 2: Soil Acidity (pH) */}
                <div className="bg-canvas border border-sand rounded-xl p-4 space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-muted">
                      Soil Acidity (pH)
                    </span>
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        soilState.tone === "good"
                          ? "bg-mint text-ink"
                          : "bg-terracotta/15 text-terracotta"
                      }`}
                    >
                      {soilState.badge}
                    </span>
                  </div>
                  <p className="text-base text-ink">
                    Gardener&apos;s soil:{" "}
                    <strong className="font-display font-semibold tabular-nums">
                      {selectedRecord.measured_soil_ph !== null
                        ? `pH ${selectedRecord.measured_soil_ph.toFixed(1)}`
                        : "Not tested"}
                    </strong>
                  </p>
                  <p className="text-xs text-muted">
                    Healthy range for {selectedRecord.crop_name}:{" "}
                    <strong className="text-ink tabular-nums">
                      pH {selectedRecord.ideal_ph_range}
                    </strong>
                  </p>
                </div>
              </div>

              {/* Check 3 & 4: Soil Treatment & Weather */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-sm">
                <div className="bg-canvas border border-sand rounded-xl p-4 space-y-1">
                  <p className="text-xs font-semibold text-muted">
                    Soil Treatment Advice
                  </p>
                  <p className="text-ink leading-relaxed">
                    {formatPlainTreatment(selectedRecord)}
                  </p>
                </div>

                <div className="bg-canvas border border-sand rounded-xl p-4 space-y-1">
                  <p className="text-xs font-semibold text-muted">
                    7-Day Weather Forecast
                  </p>
                  <p className="text-ink leading-relaxed">
                    {selectedRecord.weather_advisory}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Verified Planting Table with Plain-English Explanation Column */}
      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
            All 8 Planting Records
          </h2>
          <span className="text-sm text-muted">
            Click View Details on any row to see the full explanation above
          </span>
        </div>

        <div className="bg-canvas border-2 border-mint rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-ink">
              <thead className="bg-surface border-b border-sand">
                <tr>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Plot &amp; Gardener
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Crop Planted
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Soil Test vs Healthy Range
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    What We Found (Plain Summary)
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal">
                    Result
                  </th>
                  <th scope="col" className="py-3.5 px-4 font-semibold text-muted tracking-normal text-right">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sand/70">
                {agentData.records.map((rec) => {
                  const isSelected = selectedRecord?.record_id === rec.record_id;
                  const rowSummary = getRowSummaryText(rec);
                  return (
                    <tr
                      key={rec.record_id}
                      className={`transition-colors duration-150 ${
                        isSelected
                          ? "bg-surface ring-1 ring-inset ring-sage"
                          : "hover:bg-surface/60"
                      }`}
                    >
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-semibold text-ink">
                          {rec.gardener_name}
                        </div>
                        <div className="text-xs text-muted">
                          {rec.plot_id} ({rec.suburb})
                        </div>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-semibold text-ink">
                          {rec.crop_name}
                        </div>
                        {rec.species_scientific_raw &&
                          rec.species_scientific_raw.toLowerCase() !==
                            rec.species_scientific_verified.toLowerCase() && (
                            <div className="font-mono text-xs text-terracotta line-through">
                              {rec.species_scientific_raw}
                            </div>
                          )}
                        <div className="font-mono text-xs text-forest font-semibold">
                          {rec.species_scientific_verified}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-display font-semibold tabular-nums text-sm text-ink">
                          {rec.measured_soil_ph !== null
                            ? `Tested: pH ${rec.measured_soil_ph.toFixed(1)}`
                            : "No soil test sent"}
                        </div>
                        <div className="text-xs text-muted tabular-nums">
                          Needs: pH {rec.ideal_ph_range}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 max-w-sm">
                        <p className="text-sm text-ink leading-snug">
                          {rowSummary}
                        </p>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {rec.status === "VERIFIED" && (
                          <span className="bg-mint text-ink px-2.5 py-1 rounded-full text-xs font-semibold">
                            Passed
                          </span>
                        )}
                        {rec.status === "AUTO_CORRECTED" && (
                          <span className="bg-ochre/20 text-ink border border-ochre/50 px-2.5 py-1 rounded-full text-xs font-semibold">
                            Auto-Fixed
                          </span>
                        )}
                        {rec.status === "FLAGGED" && (
                          <span className="bg-terracotta/15 text-terracotta border border-terracotta/40 px-2.5 py-1 rounded-full text-xs font-semibold">
                            Needs Action
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => handleInspectRecord(rec)}
                          className={`min-h-[44px] px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                            isSelected
                              ? "bg-forest text-canvas border-forest"
                              : "bg-surface hover:bg-sand text-ink border-mint"
                          }`}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Interactive 5-Node React Flow Canvas */}
      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-xl font-semibold text-ink break-words min-w-0">
            How the 5-Step Verification Pipeline Works
          </h2>
          <span className="text-sm text-muted">
            Click any step below to see what it did
          </span>
        </div>

        <div className="h-[250px] w-full bg-surface border-2 border-mint rounded-2xl overflow-hidden relative shadow-sm">
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            nodesDraggable={true}
            nodesConnectable={false}
            elementsSelectable={true}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#8FB08A" gap={16} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {/* Selected Node Trace Inspector with Optional Raw JSON Disclosure */}
        {selectedNode && (
          <div
            ref={nodeInspectorRef}
            className="bg-canvas border border-mint rounded-2xl p-5 shadow-sm space-y-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-mint text-ink">
                  Step {selectedNode.step_number}
                </span>
                <span className="font-display text-base font-semibold text-ink">
                  {selectedNode.label}
                </span>
                <span className="text-xs text-muted tabular-nums">
                  ({selectedNode.duration_ms} ms)
                </span>
              </div>
              <button
                type="button"
                onClick={() =>
                  setShowNodePayloads((prev) => {
                    const next = !prev;
                    if (next) scrollIntoFrame(nodeInspectorRef.current);
                    return next;
                  })
                }
                className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-surface hover:bg-sand border border-sand text-xs font-semibold text-ink whitespace-nowrap inline-flex items-center gap-1.5 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
              >
                <span>
                  {showNodePayloads ? "Hide technical JSON" : "View technical JSON"}
                </span>
                <ChevronDownIcon expanded={showNodePayloads} />
              </button>
            </div>

            <p className="text-sm text-ink leading-relaxed">
              {selectedNode.summary_text}
            </p>

            {showNodePayloads && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-sand">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-muted">
                    Step Input
                  </p>
                  <pre className="font-mono text-xs bg-surface border border-sand p-3 rounded-xl overflow-x-auto text-ink max-h-40 leading-relaxed">
                    {JSON.stringify(selectedNode.input_payload, null, 2)}
                  </pre>
                </div>

                <div className="space-y-1">
                  <p className="text-xs font-semibold text-muted">
                    Step Output
                  </p>
                  <pre className="font-mono text-xs bg-surface border border-sand p-3 rounded-xl overflow-x-auto text-ink max-h-40 leading-relaxed">
                    {JSON.stringify(selectedNode.output_payload, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
