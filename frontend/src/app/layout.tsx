import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Court Vitals",
  description:
    "NBA analytics: Elo ratings, season simulation, and a player health layer. Not affiliated with the NBA, not gambling related.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
