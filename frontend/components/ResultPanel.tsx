export type PanelMetrics = {
  steps: string;
  elapsed: string;
  cost: string;
};

type ResultPanelProps = {
  title: string;
  lines: readonly string[];
  metrics: PanelMetrics;
};

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="text-[10px] tracking-wide text-shell-600 uppercase">{label}</span>
      <span className="font-mono text-xs text-ink-300">{value}</span>
    </div>
  );
}

export function ResultPanel({ title, lines, metrics }: ResultPanelProps) {
  return (
    <section className="min-w-0 rounded-md border border-shell-700 bg-shell-900">
      <header className="flex items-center gap-2 border-b border-shell-800 px-3 py-2">
        <span aria-hidden className="size-1.5 rounded-full bg-plasma-500" />
        <h2 className="text-xs font-semibold tracking-wide text-ink-100">{title}</h2>
      </header>

      <div className="bg-screen-950 p-3">
        <ol className="space-y-1">
          {lines.map((line, index) => (
            <li key={index} className="flex gap-3 font-mono text-xs leading-relaxed">
              <span aria-hidden className="w-4 shrink-0 text-right text-shell-600">
                {index + 1}
              </span>
              <span className="min-w-0 break-words whitespace-pre-wrap text-ink-300">{line}</span>
            </li>
          ))}
        </ol>
      </div>

      <footer className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-shell-800 px-3 py-2">
        <Metric label="Steps" value={metrics.steps} />
        <Metric label="Elapsed" value={metrics.elapsed} />
        <Metric label="Cost" value={metrics.cost} />
      </footer>
    </section>
  );
}
