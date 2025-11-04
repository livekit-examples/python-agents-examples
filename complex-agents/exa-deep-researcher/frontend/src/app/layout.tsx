import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Exa + LiveKit Deep Researcher - Voice AI Research Assistant",
  description: "Autonomous deep research agent with iterative planning, real-time UI updates via RPC streaming, and intelligent query clarification. Demonstrates how voice agents can conduct comprehensive multi-step research workflows.",
  keywords: ["voice AI", "research assistant", "Exa", "LiveKit", "deep research", "AI agent"],
  authors: [{ name: "LiveKit" }],
  openGraph: {
    title: "Exa + LiveKit Deep Researcher",
    description: "Voice AI Research Assistant - Autonomous deep research with real-time updates",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
