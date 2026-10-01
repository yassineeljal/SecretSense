import type { Metadata } from "next";
import Link from "next/link";
import { ScanSession } from "@/components/scan-session";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecretSense — Keep your secrets out of source",
  description:
    "A local secret scanner with clear findings and practical remediation.",
  robots: { index: false, follow: false },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a className="skip" href="#main">
          Skip to content
        </a>
        <header className="site-header">
          <Link className="brand" href="/" aria-label="SecretSense home">
            <span className="brand-mark" aria-hidden="true">
              S.
            </span>{" "}
            SecretSense
          </Link>
          <nav aria-label="Main navigation">
            <Link href="/scan">Scanner</Link>
            <Link href="/results">Results</Link>
            <span className="local-badge">
              <i /> Local demo
            </span>
          </nav>
        </header>
        <ScanSession>
          <main id="main">{children}</main>
        </ScanSession>
        <footer>
          <span>
            SecretSense{" "}
            <span className="muted">/ Built for a closer look.</span>
          </span>
          <span>Local processing. Redacted findings.</span>
        </footer>
      </body>
    </html>
  );
}
