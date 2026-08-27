import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PokeAgent",
  description: "Two agent implementations, one team-building problem, traced side by side.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
