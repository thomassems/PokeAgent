import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Press_Start_2P } from "next/font/google";
import { SiteFooter } from "@/components/SiteFooter";
import { AppNameProvider } from "@/lib/app-name";
import "./globals.css";

function appName(): string {
  const configured = process.env.APP_NAME?.trim();
  return configured ? configured : "Field Notes";
}

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

const name = appName();

export const metadata: Metadata = {
  title: name,
  description: "Ask questions about Pokémon and explore a team builder preview.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} ${pixel.variable}`}>
      <body className="font-sans antialiased">
        <AppNameProvider name={name}>
          {children}
          <SiteFooter appName={name} />
        </AppNameProvider>
      </body>
    </html>
  );
}
