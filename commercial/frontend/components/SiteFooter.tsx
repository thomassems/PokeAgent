type SiteFooterProps = {
  appName: string;
};

export function SiteFooter({ appName }: SiteFooterProps) {
  return (
    <footer className="border-t border-shell-800 bg-shell-900 px-4 py-4 text-xs leading-5 text-ink-500">
      <div className="mx-auto max-w-[1200px] space-y-1">
        <p>
          {appName} is not affiliated with Nintendo, The Pokémon Company, Game Freak, or
          Scopely/Niantic.
        </p>
        <p>AI-generated answers may be wrong.</p>
        <p>
          Data: species, moves, and type charts from{" "}
          <a className="underline" href="https://pokeapi.co/">
            PokéAPI
          </a>{" "}
          (BSD-3-Clause). Pokémon GO stats and rankings from{" "}
          <a className="underline" href="https://github.com/pvpoke/pvpoke">
            PvPoke
          </a>{" "}
          (MIT). No official artwork.
        </p>
      </div>
    </footer>
  );
}
