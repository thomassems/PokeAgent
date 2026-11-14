/**
 * The stream names a tool by its function name, which is what the model sees.
 * The panel is read by a person, so the translation lives here rather than at
 * the point of display: one map to extend when the registry grows, and one
 * place to look when a label reads wrong.
 */
const TOOL_LABELS: Record<string, string> = {
  get_pokemon: "Looking up Pokémon",
  get_move: "Looking up a move",
  find_pokemon: "Searching the dex",
  get_type_matchups: "Checking type matchups",
  get_type_effectiveness: "Checking type effectiveness",
  search_strategy: "Reading strategy notes",
  web_search: "Searching the web",
};

export const THINKING = "Thinking";

/**
 * Tool events arrive in pairs: "Using web_search", then "web_search returned".
 * Only the first says what is happening now. The second means the tool is done
 * and the model is about to be called again, which is thinking, not a tool
 * still running - and on these runs that gap is where most of the time goes.
 *
 * An unmapped tool falls back to its own name. A tool added to the registry
 * without a label here should look unpolished, not disappear.
 */
export function toolActivity(message: string): string {
  const using = /^Using (\w+)$/.exec(message);
  if (!using) return THINKING;
  return TOOL_LABELS[using[1]] ?? using[1];
}

/** "Step 3 of 8" as the panel shows it, or null for a status it cannot parse. */
export function stepLabel(message: string): string | null {
  return /^Step \d+ of \d+$/.test(message) ? message.toLowerCase() : null;
}
