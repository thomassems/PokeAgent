import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Press_Start_2P } from "next/font/google";
import "./globals.css";

// Plex was drawn for technical interfaces, which suits the device read. The mono
// face is here for the result panels, which will eventually hold log output.
const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-sans",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
});

// Press Start 2P is SIL Open Font License, used for main-series headings only.
// Body text stays Plex. This is not a Nintendo font.
const pixel = Press_Start_2P({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-pixel",
});

export const metadata: Metadata = {
  title: "PokeAgent",
  description: "Ask a Pokémon agent questions and explore a team builder preview.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} ${pixel.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
