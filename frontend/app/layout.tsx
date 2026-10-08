import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Meeting Notes",
  description: "Meeting library, interactive transcripts and AI notes.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      {/* The app shell (sidebar + top bar) is added in Phase 7. */}
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}
