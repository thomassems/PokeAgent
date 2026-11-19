"use client";

export type VariantState = "verified" | "unknown" | "unavailable";

export type BackgroundOption = {
  id: string;
  label: string;
};

export type VariantOptions = {
  shiny: VariantState;
  dynamax: VariantState;
  gigantamax: VariantState;
  shadow: VariantState;
  purified: VariantState;
  lucky: VariantState;
  costume: VariantState;
  forms: string[];
  costume_forms: string[];
  backgrounds: BackgroundOption[];
};

export type VariantFlags = {
  shiny: boolean;
  dynamax: boolean;
  gigantamax: boolean;
  shadow: boolean;
  purified: boolean;
  lucky: boolean;
  costume: boolean;
};

export const EMPTY_VARIANT_FLAGS: VariantFlags = {
  shiny: false,
  dynamax: false,
  gigantamax: false,
  shadow: false,
  purified: false,
  lucky: false,
  costume: false,
};

export const EMPTY_VARIANTS: VariantOptions = {
  shiny: "unknown",
  dynamax: "unknown",
  gigantamax: "unknown",
  shadow: "unknown",
  purified: "unknown",
  lucky: "unavailable",
  costume: "unknown",
  forms: [],
  costume_forms: [],
  backgrounds: [],
};

const FLAG_LABELS: Record<keyof VariantFlags, string> = {
  shiny: "Shiny",
  dynamax: "Dynamax",
  gigantamax: "Gigantamax",
  shadow: "Shadow",
  purified: "Purified",
  lucky: "Lucky",
  costume: "Costume",
};

const FLAG_ORDER = Object.keys(FLAG_LABELS) as (keyof VariantFlags)[];

type Props = {
  variants: VariantOptions;
  flags: VariantFlags;
  form: string;
  background: string;
  onFlags: (flags: VariantFlags) => void;
  onForm: (form: string) => void;
  onBackground: (background: string) => void;
};

/** Offer verified and unknown axes. Hide only what a source rules out. */
export function VariantFields({
  variants,
  flags,
  form,
  background,
  onFlags,
  onForm,
  onBackground,
}: Props) {
  const forms = [...new Set([...variants.forms, ...variants.costume_forms])];
  const visible = FLAG_ORDER.filter((flag) => variants[flag] !== "unavailable");
  const blockedCostume =
    (flags.dynamax || flags.gigantamax) &&
    flags.costume;

  const setFlag = (flag: keyof VariantFlags, checked: boolean) => {
    const next = { ...flags, [flag]: checked };
    if (flag === "dynamax" && checked) next.gigantamax = false;
    if (flag === "gigantamax" && checked) next.dynamax = false;
    if (flag === "shadow" && checked) next.purified = false;
    if (flag === "purified" && checked) next.shadow = false;
    if (flag === "costume" && checked && variants.costume_forms.length === 1) {
      onForm(variants.costume_forms[0]);
    }
    if (flag === "costume" && !checked && variants.costume_forms.includes(form)) {
      onForm("");
    }
    onFlags(next);
  };

  const setForm = (nextForm: string) => {
    onForm(nextForm);
    onFlags({ ...flags, costume: variants.costume_forms.includes(nextForm) });
  };

  return (
    <div className="flex flex-col gap-3">
      {forms.length > 0 ? (
        <label className="text-xs text-ink-400">
          Form
          <select
            className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={forms.includes(form) ? form : ""}
            onChange={(event) => setForm(event.target.value)}
          >
            <option value="">Base form</option>
            {forms.map((name) => (
              <option key={name} value={name}>
                {variants.costume_forms.includes(name) ? `${name} (costume)` : name}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {variants.backgrounds.length > 0 ? (
        <label className="text-xs text-ink-400">
          Background
          <select
            className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={variants.backgrounds.some((item) => item.id === background) ? background : ""}
            onChange={(event) => onBackground(event.target.value)}
          >
            <option value="">No background</option>
            {variants.backgrounds.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <div className="flex flex-wrap gap-3 text-xs">
        {visible.map((flag) => (
          <label key={flag} className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={flags[flag]}
              onChange={(event) => setFlag(flag, event.target.checked)}
            />
            {FLAG_LABELS[flag]}
            {variants[flag] === "unknown" ? " (not yet verified)" : ""}
          </label>
        ))}
      </div>
      {blockedCostume ? (
        <p className="text-xs text-red-300">
          Dynamax and Gigantamax are separate from costume. This combination
          is not released for this Pokémon.
        </p>
      ) : null}
    </div>
  );
}
