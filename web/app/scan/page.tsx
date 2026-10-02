import type { Metadata } from "next";
import Link from "next/link";
import LocalScan from "@/components/local-scan";
export const metadata: Metadata = { title: "Local scanner | SecretSense" };
export default function Scan() {
  if (process.env.NEXT_PUBLIC_SECRETSENSE_MODE === "portfolio") {
    return (
      <section className="empty-state">
        <p className="eyebrow">RUN IT ON YOUR MACHINE</p>
        <h1>Scanning stays local.</h1>
        <p>
          This portfolio accepts no source text or file uploads. Install the CLI
          or run the loopback demo to scan on your machine.
        </p>
        <Link className="button primary" href="/docs">
          Set up SecretSense →
        </Link>
      </section>
    );
  }
  return <LocalScan />;
}
