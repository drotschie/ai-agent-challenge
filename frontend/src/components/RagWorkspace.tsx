"use client";

import React, { useRef, useState } from "react";
import Image from "next/image";
import {
  ChatMessage,
  INITIAL_RAG_RESPONSE,
  RagQueryResponse,
  queryRagApi,
} from "@/lib/api";

function SearchIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-5 h-5 text-forest flex-shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <circle cx="11" cy="11" r="7" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
    </svg>
  );
}

function LeafIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-6 h-6 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
      <path d="M2 21c0-3 1.85-5.36 5.08-6" />
    </svg>
  );
}

function FruitIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-6 h-6 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="13" r="8" />
      <path d="M12 5V2" />
      <path d="M9 4c1 .8 2 1 3 1s2-.2 3-1" />
      <path d="M8 3c1.5 1 2.5 1 4 1" />
      <path d="M16 3c-1.5 1-2.5 1-4 1" />
    </svg>
  );
}

function RootIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-6 h-6 text-forest flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2v4" />
      <path d="M10 4l4-2" />
      <path d="M14 4l-4-2" />
      <path d="M18 10c0 4-3 10-6 12-3-2-6-8-6-12a6 6 0 0 1 12 0Z" />
      <path d="M9 11h6" />
      <path d="M10 15h4" />
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

function ArrowRightIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-3.5 h-3.5 flex-shrink-0"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M13 6l6 6-6 6" />
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

function getCropIcon(cropName: string) {
  const name = cropName.toLowerCase();
  if (
    name.includes("tomato") ||
    name.includes("pepper") ||
    name.includes("eggplant") ||
    name.includes("squash") ||
    name.includes("bean") ||
    name.includes("pea")
  ) {
    return <FruitIcon />;
  }
  if (
    name.includes("carrot") ||
    name.includes("beet") ||
    name.includes("potato") ||
    name.includes("radish") ||
    name.includes("turnip") ||
    name.includes("onion") ||
    name.includes("garlic")
  ) {
    return <RootIcon />;
  }
  return <LeafIcon />;
}

interface RagWorkspaceProps {
  /** Opens the Reference Data tab on the exact record behind a citation. */
  onOpenSource?: (sourceFile: string, locator: string) => void;
}

export function RagWorkspace({ onOpenSource }: RagWorkspaceProps) {
  const [question, setQuestion] = useState(
    "What vegetables grow well in Woodstock with soil pH 5.3, and how much lime do I need?"
  );
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [response, setResponse] = useState<RagQueryResponse>(INITIAL_RAG_RESPONSE);
  const [isLoading, setIsLoading] = useState(false);

  // Progressive disclosure states to keep panels calm and scannable
  const [showFullAnswer, setShowFullAnswer] = useState(false);
  const [showQueryTrace, setShowQueryTrace] = useState(false);
  const [expandedCrops, setExpandedCrops] = useState<Record<number, boolean>>({});
  const [expandedChunks, setExpandedChunks] = useState<Record<string, boolean>>({});
  const [showAllChunks, setShowAllChunks] = useState(false);

  const responsePanelRef = useRef<HTMLDivElement | null>(null);

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

  const scrollToResponsePanel = () => {
    window.setTimeout(() => {
      responsePanelRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 60);
  };

  const toggleChunk = (chunkId: string, triggerEl?: HTMLElement | null) => {
    setExpandedChunks((prev) => {
      const next = !prev[chunkId];
      if (next && triggerEl) {
        scrollIntoFrame(triggerEl.closest("div"));
      }
      return {
        ...prev,
        [chunkId]: next,
      };
    });
  };

  const toggleCrop = (idx: number, triggerEl?: HTMLElement | null) => {
    setExpandedCrops((prev) => {
      const next = !prev[idx];
      if (next && triggerEl) {
        scrollIntoFrame(triggerEl.parentElement);
      }
      return {
        ...prev,
        [idx]: next,
      };
    });
  };

  const handleQuery = async (queryText: string) => {
    if (!queryText.trim() || isLoading) {
      return;
    }
    setIsLoading(true);
    setShowFullAnswer(false);
    const updatedHistory: ChatMessage[] = [
      ...chatHistory,
      { role: "user", content: queryText },
    ];

    try {
      const result = await queryRagApi(queryText, chatHistory);
      setResponse(result);
      setChatHistory([
        ...updatedHistory,
        { role: "assistant", content: result.answer },
      ]);
      scrollToResponsePanel();
    } catch (err) {
      console.warn("Failed to execute query:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleQuery(question);
  };

  const runChipQuery = (chipQuery: string) => {
    setQuestion(chipQuery);
    handleQuery(chipQuery);
  };

  const answerText = response.answer || "";
  const isLongAnswer = answerText.length > 340;
  const displayedAnswer =
    isLongAnswer && !showFullAnswer
      ? `${answerText.slice(0, 340).trimEnd()}...`
      : answerText;

  const visibleChunks = showAllChunks
    ? response.retrieved_chunks
    : response.retrieved_chunks.slice(0, 3);

  return (
    <div className="w-full">
      {/* Aerial Cape Garden Hero Banner */}
      <section className="relative w-full overflow-hidden bg-ink">
        <div className="relative w-full min-h-[220px] aspect-[16/5]">
          <Image
            src="/images/cape-garden-banner.jpg"
            alt="Western Cape community garden and mountain panorama"
            width={1024}
            height={323}
            priority
            className="w-full h-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-ink/15" />
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            <div className="bg-ink/90 border border-mint/40 rounded-2xl px-6 sm:px-10 py-5 sm:py-6 shadow-lg max-w-2xl">
              <h1 className="font-display text-3xl sm:text-5xl font-semibold text-canvas tracking-tight text-balance">
                What thrives in your Cape garden today?
              </h1>
              <p className="mt-2.5 text-base sm:text-lg text-canvas/95 font-normal leading-relaxed text-balance">
                Soil guidance, crop matches, and live microclimate data for the Cape.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pill Search Bar Overlapping Banner */}
      <div className="-mt-8 relative z-10 px-4">
        <form
          onSubmit={handleSubmit}
          className="bg-canvas border-4 border-mint rounded-full shadow-md max-w-3xl mx-auto px-4 py-1.5 flex items-center gap-3"
        >
          <SearchIcon />
          <label htmlFor="rag-search-input" className="sr-only">
            Ask a South African gardening question
          </label>
          <input
            id="rag-search-input"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about soil pH, Cape crops, lime amendments, or watering..."
            className="min-h-[44px] flex-1 bg-transparent text-sm sm:text-base text-ink placeholder-muted/60 focus:outline-none"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="min-h-[44px] px-5 rounded-full bg-forest hover:bg-muted text-canvas font-medium text-sm whitespace-nowrap transition-colors duration-150 flex items-center gap-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            {isLoading && <SpinnerIcon />}
            <span>{isLoading ? "Thinking..." : "Ask Guide"}</span>
          </button>
        </form>

        {/* Quick-Select Filter Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-4 px-4">
          <span className="text-xs font-medium text-muted mr-1">
            Try a question:
          </span>
          <button
            type="button"
            onClick={() =>
              runChipQuery(
                "What crops thrive in sandy coastal soil in Muizenberg or Sea Point, and what mulching is needed?"
              )
            }
            className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-sand hover:bg-sand-border text-ink text-xs font-medium whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Sandy Soil
          </button>
          <button
            type="button"
            onClick={() =>
              runChipQuery(
                "What vegetables grow well in Woodstock with soil pH 5.3, and how much lime do I need?"
              )
            }
            className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-mint hover:bg-sage/60 text-ink text-xs font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Woodstock pH
          </button>
          <button
            type="button"
            onClick={() =>
              runChipQuery(
                "Can I plant Beetroot and Carrot in Durbanville clay_loam soil right now?"
              )
            }
            className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-sand hover:bg-sand-border text-ink text-xs font-medium whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Root Crops
          </button>
          <button
            type="button"
            onClick={() =>
              runChipQuery(
                "What about the winter frost risk there, and can I plant Kale?"
              )
            }
            className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-sand hover:bg-sand-border text-ink text-xs font-medium whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
          >
            Follow-up Query
          </button>
        </div>
      </div>

      {/* Main Two-Column Shared-Grid Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-8 pt-8 pb-14 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Response Panel FIRST, then Recommended Crops */}
        <section className="lg:col-span-7 space-y-6">
          {/* Card 1 (First Panel Below Prompt): Grounded Guide Response */}
          <div
            ref={responsePanelRef}
            id="guide-response-panel"
            className="scroll-mt-24 bg-canvas border-2 border-mint rounded-2xl p-6 sm:p-7 shadow-sm space-y-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-sand pb-4">
              <div>
                <p className="text-sm font-medium text-forest">
                  Guide response for{" "}
                  {response.live_weather?.suburb || "your garden"}
                </p>
                <h2 className="font-display text-2xl sm:text-3xl font-semibold text-ink tracking-normal">
                  Agronomic Recommendation
                </h2>
              </div>
              <span className="bg-surface border border-sand text-ink text-xs font-medium px-3 py-1.5 rounded-full tabular-nums">
                Soil pH{" "}
                {response.query_transform.detected_soil_ph ??
                  response.live_weather?.baseline_ph_range ??
                  "5.3"}
              </span>
            </div>

            {/* Primary Action Takeaway Banner */}
            {response.action_banner && (
              <div className="bg-forest text-canvas rounded-xl p-4 flex items-start gap-3">
                <svg
                  aria-hidden="true"
                  focusable="false"
                  className="w-5 h-5 text-mint flex-shrink-0 mt-0.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm sm:text-base font-medium leading-relaxed">
                  {response.action_banner}
                </p>
              </div>
            )}

            {/* Main Readable Answer with Progressive Disclosure */}
            <div className="space-y-3">
              <p className="whitespace-pre-line leading-relaxed text-ink text-base sm:text-[17px]">
                {displayedAnswer}
              </p>

              {isLongAnswer && (
                <button
                  type="button"
                  onClick={(e) => {
                    const card = e.currentTarget.closest("div");
                    setShowFullAnswer((prev) => {
                      const next = !prev;
                      if (next) scrollIntoFrame(card);
                      return next;
                    });
                  }}
                  className="min-h-[44px] inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface hover:bg-sand border border-sand text-sm font-semibold text-forest whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                >
                  <span>
                    {showFullAnswer ? "Show concise summary" : "Read full answer"}
                  </span>
                  <ChevronDownIcon expanded={showFullAnswer} />
                </button>
              )}
            </div>

            {/* Compact Citation Pills & Optional Query Rewrite Disclosure */}
            <div className="pt-4 border-t border-sand flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs font-medium text-muted mr-1">
                  Sources:
                </span>
                {response.citations.slice(0, 4).map((c, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onOpenSource?.(c.source_file, c.locator)}
                    title="Open this record in Reference Data"
                    className="min-h-[44px] inline-flex items-center gap-1.5 font-mono text-xs bg-surface hover:bg-mint border border-sand hover:border-sage text-ink px-2.5 py-1 rounded-md transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                  >
                    <span>{c.label}</span>
                    <ArrowRightIcon />
                  </button>
                ))}
                {response.citations.length > 4 && (
                  <span className="text-xs text-muted px-2 py-1">
                    +{response.citations.length - 4} more
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={(e) => {
                  const card = e.currentTarget.parentElement?.parentElement || null;
                  setShowQueryTrace((prev) => {
                    const next = !prev;
                    if (next) scrollIntoFrame(card);
                    return next;
                  });
                }}
                className="min-h-[44px] px-3.5 py-1.5 rounded-full bg-surface hover:bg-sand border border-sand text-xs font-semibold text-ink whitespace-nowrap inline-flex items-center gap-1.5 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
              >
                <span>
                  {showQueryTrace ? "Hide query trace" : "View query trace"}
                </span>
                <ChevronDownIcon expanded={showQueryTrace} />
              </button>
            </div>

            {showQueryTrace && (
              <div className="space-y-2.5 text-sm text-muted bg-surface p-4 rounded-xl border border-sand">
                <p>
                  <span className="font-semibold text-ink">
                    Resolved Question:
                  </span>{" "}
                  {response.query_transform.resolved_question}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-sand">
                  <p>
                    <span className="font-semibold text-ink">Suburb:</span>{" "}
                    {response.query_transform.detected_suburb || "None detected"}
                  </p>
                  <p>
                    <span className="font-semibold text-ink">Crops:</span>{" "}
                    {response.query_transform.detected_crops.length > 0
                      ? response.query_transform.detected_crops.join(", ")
                      : "General"}
                  </p>
                  <p>
                    <span className="font-semibold text-ink">Soil pH:</span>{" "}
                    {response.query_transform.detected_soil_ph ?? "Not stated"}
                  </p>
                </div>
                <div className="pt-2 border-t border-sand">
                  <p className="font-semibold text-ink mb-1.5 text-xs">
                    Sub-queries sent to ChromaDB:
                  </p>
                  <div className="space-y-1.5 font-mono text-xs">
                    {response.query_transform.sub_queries.map((sq, sqIdx) => (
                      <div
                        key={sqIdx}
                        className="flex items-start gap-2 bg-canvas px-2.5 py-1.5 rounded border border-sand"
                      >
                        <span className="text-forest font-semibold flex-shrink-0">
                          [{sq.target_source}]
                        </span>
                        <span className="text-ink">{sq.query}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Card 2: Recommended Crops (with per-crop Read More) */}
          <div className="bg-surface border border-sand-border rounded-2xl p-6 sm:p-7 space-y-5">
            <div>
              <p className="text-sm font-medium text-muted">
                Matched from crop_planting_guide.json
              </p>
              <h2 className="font-display text-2xl font-semibold text-ink tracking-normal">
                Recommended Crops ({response.recommended_crops.length})
              </h2>
            </div>

            <div className="space-y-4 divide-y divide-sand">
              {response.recommended_crops.map((crop, idx) => {
                const isExpanded = expandedCrops[idx] ?? false;
                const isLongDesc = crop.description.length > 130;
                return (
                  <div key={idx} className={idx > 0 ? "pt-4" : ""}>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <span className="p-2.5 rounded-xl bg-canvas border border-sand text-forest">
                          {getCropIcon(crop.crop_name)}
                        </span>
                        <div>
                          <h3 className="font-display text-xl font-semibold text-ink tracking-normal">
                            {crop.crop_name}
                          </h3>
                          <p className="text-sm italic text-muted">
                            {crop.scientific_name}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          onOpenSource?.("crop_planting_guide.json", crop.crop_name)
                        }
                        title="Open this crop in Reference Data"
                        className="min-h-[44px] inline-flex items-center gap-1.5 bg-mint hover:bg-sage/60 text-ink font-mono text-xs px-3 py-1 rounded-full whitespace-nowrap self-start transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                      >
                        <span>{crop.citation}</span>
                        <ArrowRightIcon />
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-sm font-medium text-muted my-2.5">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-canvas border border-sand">
                        <span>Optimal pH:</span>
                        <strong className="text-ink tabular-nums">
                          {crop.optimal_ph}
                        </strong>
                      </span>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-canvas border border-sand">
                        <span>Water:</span>
                        <strong className="text-ink tabular-nums">
                          {crop.water_mm_per_week} mm/week
                        </strong>
                      </span>
                    </div>

                    <p
                      className={`text-base text-ink/90 leading-relaxed ${
                        !isExpanded && isLongDesc ? "line-clamp-2" : ""
                      }`}
                    >
                      {crop.description}
                    </p>

                    {isLongDesc && (
                      <button
                        type="button"
                        onClick={(e) => toggleCrop(idx, e.currentTarget)}
                        className="mt-1.5 min-h-[44px] inline-flex items-center gap-1.5 text-xs font-semibold text-forest hover:text-ink whitespace-nowrap focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                      >
                        <span>
                          {isExpanded ? "Show less" : "Show planting notes"}
                        </span>
                        <ChevronDownIcon expanded={isExpanded} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Right Column: Live Weather & Progressive Vector Chunks */}
        <section className="lg:col-span-5 space-y-6">
          {/* Card 1: Live Cape Town Weather & Soil Baseline */}
          <div className="bg-forest text-canvas rounded-2xl p-6 shadow-sm">
            <p className="text-sm font-medium text-mint mb-1 tracking-normal">
              Live microclimate: {response.live_weather?.suburb}
            </p>
            <p className="font-display text-3xl sm:text-4xl text-canvas tabular-nums mb-2">
              {response.live_weather?.temperature_c.toFixed(1)}°C /{" "}
              {response.live_weather?.condition}
            </p>
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <span className="font-display text-xl text-canvas tabular-nums">
                Baseline pH {response.live_weather?.baseline_ph_range}
              </span>
              <span className="bg-sage/40 border border-mint/40 text-canvas text-xs px-3 py-1 rounded-full font-medium">
                Open-Meteo Live
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-sage/30 text-sm tabular-nums">
              <div>
                <p className="text-xs text-mint mb-0.5">Soil Type</p>
                <p className="font-medium text-canvas">
                  {formatSoilType(response.live_weather?.soil_type)}
                </p>
              </div>
              <div>
                <p className="text-xs text-mint mb-0.5">Humidity</p>
                <p className="font-medium text-canvas">
                  {response.live_weather?.humidity_pct}%
                </p>
              </div>
              <div>
                <p className="text-xs text-mint mb-0.5">7-Day Frost</p>
                <p className="font-medium text-canvas">
                  {response.live_weather?.frost_risk_7d ? "Elevated" : "None"}
                </p>
              </div>
            </div>
          </div>

          {/* Card 2: Retrieved Vector Chunks (Top 3 by default, expandable) */}
          <div className="bg-canvas border-2 border-mint rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h2 className="font-display text-xl font-semibold text-ink tracking-normal">
                  Retrieved Evidence Chunks
                </h2>
                <p className="text-xs text-muted">
                  Expand a chunk to read its indexed text, or open the original row
                </p>
              </div>
              <span className="text-xs font-sans bg-surface border border-sand px-2.5 py-1 rounded-full text-ink tabular-nums">
                {response.retrieved_chunks.length} matched
              </span>
            </div>

            <div className="space-y-3">
              {visibleChunks.map((chunk, idx) => {
                const isExpanded = expandedChunks[chunk.chunk_id] ?? false;
                const pct = Math.round(chunk.similarity * 100);
                return (
                  <div
                    key={chunk.chunk_id || idx}
                    className="bg-surface border border-sand rounded-xl p-3.5"
                  >
                    <div className="h-1.5 rounded-full bg-mint/60 overflow-hidden mb-2.5">
                      <div
                        className="h-full rounded-full bg-sage transition-opacity duration-300"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between gap-2 min-w-0">
                      <button
                        type="button"
                        onClick={(e) => toggleChunk(chunk.chunk_id, e.currentTarget)}
                        className="min-h-[44px] min-w-0 flex-1 flex items-center justify-between gap-2 text-left text-xs font-mono bg-sand hover:bg-sand-border text-ink px-3 py-1.5 rounded-lg transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                      >
                        <span className="truncate">
                          {chunk.source_file} : {chunk.locator}
                        </span>
                        <ChevronDownIcon expanded={isExpanded} />
                      </button>
                      <span className="font-display text-sm font-semibold text-ink tabular-nums flex-shrink-0 whitespace-nowrap">
                        {pct}% match
                      </span>
                    </div>

                    {!isExpanded ? (
                      <p className="mt-2 text-sm text-muted leading-relaxed line-clamp-1">
                        {chunk.text}
                      </p>
                    ) : (
                      <div className="mt-3 pt-3 border-t border-sand text-xs font-mono text-ink whitespace-pre-wrap break-words bg-canvas p-3 rounded-lg">
                        {chunk.text}
                      </div>
                    )}

                    <button
                      type="button"
                      onClick={() => onOpenSource?.(chunk.source_file, chunk.locator)}
                      className="mt-1.5 min-h-[44px] inline-flex items-center gap-1.5 text-xs font-semibold text-forest hover:text-ink whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
                    >
                      <span className="whitespace-nowrap">View source row</span>
                      <ArrowRightIcon />
                    </button>
                  </div>
                );
              })}
            </div>

            {response.retrieved_chunks.length > 3 && (
              <button
                type="button"
                onClick={(e) => {
                  const card = e.currentTarget.parentElement;
                  setShowAllChunks((prev) => {
                    const next = !prev;
                    if (next) scrollIntoFrame(card);
                    return next;
                  });
                }}
                className="w-full min-h-[44px] rounded-xl bg-surface hover:bg-sand border border-sand text-xs font-semibold text-ink whitespace-nowrap inline-flex items-center justify-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
              >
                <span>
                  {showAllChunks
                    ? "Show top 3 chunks"
                    : `Show all ${response.retrieved_chunks.length} retrieved chunks`}
                </span>
                <ChevronDownIcon expanded={showAllChunks} />
              </button>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
