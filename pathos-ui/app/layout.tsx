import type { Metadata } from "next";
import Link from "next/link";
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
  title: "Theory World Model",
  description: "Multi-Agent Reasoning For The Markets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <div className="app-shell">
          <header className="app-header">
            <div className="app-header__inner">
              <Link href="/client-workspace" className="brand-mark" aria-label="Theory World Model home">
                <span className="brand-mark__glyph" />
                <span className="brand-mark__text">Theory World Model</span>
              </Link>

              <div className="app-header__meta">
                <span className="status-pill">
                  <span className="status-pill__dot" />
                  Multi-agent market lab
                </span>
              </div>
            </div>
          </header>

          <div className="app-main">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}