import type { View } from "@/lib/types";

const EXAMPLE_PROMPTS: readonly string[] = [
  "Build me a balanced team around Infernape.",
  "My team loses to Ice types. Fix it.",
  "Fill the remaining slots, favouring speed over bulk.",
];

export function PromptPanel({ view }: { view: View }) {
  return (
    <section className="rounded-md border border-shell-700 bg-shell-900 p-4">
      <label htmlFor="prompt" className="text-xs font-semibold tracking-widest text-ink-500 uppercase">
        Prompt
      </label>
      <textarea
        id="prompt"
        rows={3}
        placeholder="Describe the team you want…"
        className="mt-2 w-full resize-y rounded-sm border border-shell-700 bg-screen-950 p-3 text-sm text-ink-100 placeholder:text-shell-600"
      />
      <div className="mt-3 flex items-center justify-between gap-4">
        <p className="text-xs text-ink-500">Both agents run the same prompt.</p>
        {/* Inert by design - this shell makes no calls. */}
        <button
          type="button"
          className="rounded-sm bg-plasma-600 px-3 py-1.5 text-sm font-medium text-ink-100 transition-colors hover:bg-plasma-500"
        >
          Compare
        </button>
      </div>

      {view === "before" && (
        <div className="mt-4 border-t border-shell-800 pt-4">
          <h2 className="text-xs font-semibold tracking-widest text-ink-500 uppercase">
            Nothing run yet
          </h2>
          <p className="mt-2 text-sm text-ink-300">
            Fill some slots on the left, or just describe what you want. Both agents solve the same
            problem and their traces appear here side by side.
          </p>
          <ul className="mt-3 space-y-1.5">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <li key={prompt} className="font-mono text-xs text-ink-500">
                <span aria-hidden className="mr-2 text-shell-600">
                  →
                </span>
                {prompt}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
