"use client";

import { useState } from "react";
import { CUSTOM_LOOP_LINES, LANGCHAIN_LINES } from "@/lib/mock-data";
import { ResultPanel, type PanelMetrics } from "./ResultPanel";

/** Labelled by implementation, not by vendor - that is what is being compared. */
const PANELS = [
  {
    id: "custom",
    title: "Custom loop",
    lines: CUSTOM_LOOP_LINES,
    metrics: { steps: "14", elapsed: "8.2s", cost: "$0.0041" } satisfies PanelMetrics,
  },
  {
    id: "langchain",
    title: "LangChain",
    lines: LANGCHAIN_LINES,
    metrics: { steps: "6", elapsed: "5.7s", cost: "$0.0029" } satisfies PanelMetrics,
  },
] as const;

type PanelId = (typeof PANELS)[number]["id"];

export function ResultPanels() {
  const [activePanel, setActivePanel] = useState<PanelId>("custom");

  return (
    <div className="space-y-3">
      {/*
        Tabs exist only below the panels breakpoint. Above it both panels are
        visible, where tab semantics would be a lie - so these are plain toggle
        buttons with aria-pressed rather than a full ARIA tablist, and the
        inactive panel is display:none so it leaves the accessibility tree too.
      */}
      <div className="flex gap-1 panels:hidden">
        {PANELS.map(({ id, title }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActivePanel(id)}
            aria-pressed={activePanel === id}
            className={`flex-1 rounded-sm border px-3 py-1.5 text-xs font-medium transition-colors ${
              activePanel === id
                ? "border-plasma-600 bg-plasma-600/20 text-ink-100"
                : "border-shell-700 bg-shell-900 text-ink-500 hover:text-ink-100"
            }`}
          >
            {title}
          </button>
        ))}
      </div>

      {/*
        items-start keeps each panel at its natural height instead of stretching
        both to the taller one. The uneven placeholder content is the point:
        equal-height columns would hide how the footer behaves.
      */}
      <div className="grid items-start gap-3 panels:grid-cols-2">
        {PANELS.map(({ id, title, lines, metrics }) => (
          <div key={id} className={`${activePanel === id ? "" : "hidden"} panels:block`}>
            <ResultPanel title={title} lines={lines} metrics={metrics} />
          </div>
        ))}
      </div>
    </div>
  );
}
