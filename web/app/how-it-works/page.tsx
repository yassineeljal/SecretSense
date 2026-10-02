import type { Metadata } from "next";
import Link from "next/link";
import { Guide, SourceLink } from "@/components/guide";
export const metadata: Metadata = { title: "How it works | SecretSense" };
const steps = [
  [
    "Read locally",
    "The CLI reads UTF-8 files or bounded Git history. The browser demo sends text directly to the API on your machine.",
  ],
  [
    "Find candidates",
    "Patterns recognize 15 services, JWTs, and private-key headers. Entropy checks flag random-looking literals assigned to secret-like names.",
  ],
  [
    "Explain the signal",
    "Every candidate gets a location, rule, severity, and explanation. Matching a shape cannot establish whether a credential is active.",
  ],
  [
    "Redact and respond",
    "Reports mask values and attach service-specific remediation. Review locally, rotate exposed credentials, and inspect their use.",
  ],
];
export default function HowItWorks() {
  return (
    <Guide
      eyebrow="THE PIPELINE"
      title="A signal you can inspect."
      intro="One local scanning engine, with a clear path from input to a redacted finding."
    >
      <ol className="pipeline" aria-label="Scanning pipeline">
        {steps.map(([title, text], index) => (
          <li key={title}>
            <span className="step-number">0{index + 1}</span>
            <h2>{title}</h2>
            <p>{text}</p>
          </li>
        ))}
      </ol>
      <section className="guide-callout">
        <h2>Where does machine learning fit?</h2>
        <p>
          The optional CLI forest converts candidate text and context into 13
          numeric features, then adds an experimental score. Scores are
          uncalibrated. All findings remain visible, including those below the
          artifact’s threshold. The browser demo uses rules plus entropy only.
        </p>
        <Link className="text-link" href="/benchmarks">
          See why filtering is disabled →
        </Link>
      </section>
      <section>
        <h2>Know the boundaries.</h2>
        <p>
          Ignored files, binary input, symlinks, and oversized files can hide
          secrets. Explicitly scan ignored files when needed. Resource limits
          can make scans incomplete; the CLI returns exit code 2 for errors or
          incomplete work. A clean scan is not a security guarantee.
        </p>
        <SourceLink path="docs/detection.md">
          Detection coverage and limits
        </SourceLink>
      </section>
    </Guide>
  );
}
