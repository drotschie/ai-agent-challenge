"use client";

import React, { useState } from "react";
import { RagWorkspace } from "@/components/RagWorkspace";
import { AgentWorkspace } from "@/components/AgentWorkspace";
import { DataExplorer } from "@/components/DataExplorer";

function BotanicalLeafIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className="w-7 h-7 text-forest flex-shrink-0"
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

function SwitchIcon() {
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
      <path d="m16 3 4 4-4 4" />
      <path d="M20 7H4" />
      <path d="m8 21-4-4 4-4" />
      <path d="M4 17h16" />
    </svg>
  );
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<number>(0);

  const togglePart = () => {
    setActiveTab((prev) => (prev === 0 ? 1 : 0));
  };

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col selection:bg-mint selection:text-ink">
      {/* Top Header */}
      <header className="bg-canvas/95 backdrop-blur-sm border-b border-sand sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-20 flex items-center justify-between gap-4">
          {/* Left Brand */}
          <div className="flex items-center gap-3">
            <BotanicalLeafIcon />
            <div>
              <span className="font-display text-2xl font-semibold tracking-tight text-ink">
                garden guide
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-sans text-forest px-2 py-0.5 rounded-full bg-surface border border-sand">
                Western Cape AI
              </span>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav
            aria-label="Main Navigation"
            className="hidden md:flex items-center gap-1.5 bg-surface p-1.5 rounded-full border border-sand"
          >
            <button
              type="button"
              onClick={() => setActiveTab(0)}
              className={`min-h-[44px] px-4 rounded-full text-sm font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                activeTab === 0
                  ? "bg-forest text-canvas shadow-sm"
                  : "text-muted hover:text-ink hover:bg-sand"
              }`}
            >
              1. Garden Guide
            </button>

            <button
              type="button"
              onClick={() => setActiveTab(1)}
              className={`min-h-[44px] px-4 rounded-full text-sm font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                activeTab === 1
                  ? "bg-forest text-canvas shadow-sm"
                  : "text-muted hover:text-ink hover:bg-sand"
              }`}
            >
              2. Verification Agent
            </button>

            <button
              type="button"
              onClick={() => setActiveTab(2)}
              className={`min-h-[44px] px-4 rounded-full text-sm font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
                activeTab === 2
                  ? "bg-forest text-canvas shadow-sm"
                  : "text-muted hover:text-ink hover:bg-sand"
              }`}
            >
              3. Reference Data
            </button>
          </nav>

          {/* Right CTA Pill Button */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={togglePart}
              className="min-h-[44px] bg-forest hover:bg-muted text-canvas rounded-full px-5 text-sm font-medium inline-flex items-center gap-2 transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest"
            >
              <SwitchIcon />
              <span>Switch / Run Demo</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="md:hidden border-t border-sand px-4 py-2 flex items-center justify-between gap-1 overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab(0)}
            className={`min-h-[44px] px-3 rounded-full text-xs font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === 0
                ? "bg-forest text-canvas"
                : "text-muted hover:text-ink"
            }`}
          >
            Part 1: RAG
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(1)}
            className={`min-h-[44px] px-3 rounded-full text-xs font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === 1
                ? "bg-forest text-canvas"
                : "text-muted hover:text-ink"
            }`}
          >
            Part 2: Agent
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(2)}
            className={`min-h-[44px] px-3 rounded-full text-xs font-semibold whitespace-nowrap transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
              activeTab === 2
                ? "bg-forest text-canvas"
                : "text-muted hover:text-ink"
            }`}
          >
            Data Sources
          </button>
        </div>
      </header>

      {/* Main Active Tab Content */}
      <main className="flex-1">
        {activeTab === 0 && <RagWorkspace />}
        {activeTab === 1 && <AgentWorkspace />}
        {activeTab === 2 && <DataExplorer />}
      </main>

      {/* Editorial Colophon Footer */}
      <footer className="bg-surface border-t border-sand py-6 px-4 sm:px-8 text-xs text-muted">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <p className="leading-relaxed">
            South African Gardener&apos;s Guide and Planting Verification Agent. Powered by
            ChromaDB (BAAI/bge-small-en-v1.5), LangGraph, GBIF Species Matching, and Open-Meteo Forecasts.
          </p>
          <p className="font-sans text-[11px] text-forest whitespace-nowrap">
            Western Cape Garden Guide &middot; 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
