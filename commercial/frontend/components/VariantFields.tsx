"use client";

export type VariantOptions = {
  shiny: boolean;
  dynamax: boolean;
  gigantamax: boolean;
  shadow: boolean;
  purified: boolean;
  lucky: boolean;
  costume: boolean;
  forms: string[];
  costume_forms: string[];
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
  onFlags: (flags: VariantFlags) => void;
  onForm: (form: string) => void;
};

/** Checkboxes and a form list limited to variants this species has. */
export function VariantFields({ variants, flags, form, onFlags, onForm }: Props) {
  const forms = [...new Set([...variants.forms, ...variants.costume_forms])];
  const visible = FLAG_ORDER.filter((flag) => variants[flag]);

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

  if (visible.length === 0 && forms.length === 0) {
    return (
      <p className="text-xs text-ink-500">
        This Pokémon has no extra variants in the catalog.
      </p>
    );
  }

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
      <div className="flex flex-wrap gap-3 text-xs">
        {visible.map((flag) => (
          <label key={flag} className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={flags[flag]}
              onChange={(event) => setFlag(flag, event.target.checked)}
            />
            {FLAG_LABELS[flag]}
          </label>
        ))}
      </div>
    </div>
  );
}
