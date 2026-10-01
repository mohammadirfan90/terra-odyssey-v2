import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Earth System Trend Detective | NASA Earth Science & Climate Investigation",
  description:
    "Offline-first, scientifically rigorous Earth system trend investigation platform. Features 2D flat cartography, area-weighted statistics, Mann-Kendall inference, and deterministic bilingual narration.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-cyan-500/20 font-sans">
        {children}
      </body>
    </html>
  );
}
