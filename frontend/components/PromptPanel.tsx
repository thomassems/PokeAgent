import type { Game } from "@/lib/game";
import type { Generation } from "@/lib/types";
import { GameChip } from "./GameChip";
import { GenerationChip } from "./GenerationChip";

type PromptPanelProps = {
  prompt: string;
  isRunning: boolean;
  game: Game;
  generation: Generation | null;
  onGameChange: (game: Game) => void;
  onGenerationChange: (generation: Generation | null) => void;
  onPromptChange: (prompt: string) => void;
  onSubmit: () => void;
};

export function PromptPanel({
  prompt,
  isRunning,
  game,
  generation,
  onGameChange,
  onGenerationChange,
  onPromptChange,
  onSubmit,
}: PromptPanelProps) {
  return (
    <form
      className="chat-composer"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label htmlFor="prompt" className="sr-only">Message PokeAgent</label>
      <textarea
        id="prompt"
        rows={2}
        value={prompt}
        onChange={(event) => onPromptChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            if (!isRunning) onSubmit();
          }
        }}
        placeholder="Message PokeAgent"
        className="chat-input"
      />
      <div className="chat-composer-actions">
        <div className="chat-composer-chips">
          <GameChip game={game} onChange={onGameChange} tone="light" placement="up" />
          {game === "main" && (
            <GenerationChip
              generation={generation}
              onChange={onGenerationChange}
              tone="light"
              placement="up"
            />
          )}
        </div>
        <div className="chat-composer-submit">
          <span>Shift + Enter for a new line</span>
          <button type="submit" disabled={isRunning || !prompt.trim()} aria-label="Send message">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 19V5m0 0-6 6m6-6 6 6" />
            </svg>
          </button>
        </div>
      </div>
    </form>
  );
}
