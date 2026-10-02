import type { Metadata } from "next";
import { Guide, SourceLink, repository } from "@/components/guide";
export const metadata: Metadata = {
  title: "Security and privacy | SecretSense",
};
export default function Security() {
  return (
    <Guide
      eyebrow="SECURITY & PRIVACY"
      title="Keep the input close."
      intro="Use the CLI or run the demo on your own machine. The hosted portfolio mode accepts no scan input. No credential is tested against a provider."
    >
      <section>
        <h2>What happens to your input.</h2>
        <p>
          The local demo sends source directly from your browser to
          127.0.0.1:8000. Input clears on submission. The API processes it in a
          disposable worker and returns fully redacted values with a fixed
          filename. Source is not routed through the Next.js server or written
          to disk by the scanner.
        </p>
        <p>
          Redacted results stay in React memory across in-site navigation.
          Reloading, leaving the site, clearing results, or starting another
          scan clears them. There is no application analytics, browser storage,
          cookie tracking, or remote asset loading. Browser extensions,
          developer tools, swap, and crash dumps can still expose memory; secure
          erasure is not guaranteed.
        </p>
      </section>
      <section>
        <h2>Bounds before work.</h2>
        <div className="policy-grid">
          <div>
            <strong>1 MiB</strong>
            <span>Encoded request body</span>
          </div>
          <div>
            <strong>2 scans</strong>
            <span>Concurrent requests</span>
          </div>
          <div>
            <strong>30 / minute</strong>
            <span>POST admission per process</span>
          </div>
          <div>
            <strong>5 seconds</strong>
            <span>Worker deadline</span>
          </div>
        </div>
        <p>
          The request deadline is ten seconds. Reports are capped at 1,000
          findings and 2 MiB. Limits fail explicitly; incomplete work never
          becomes a clean result. These are application limits, not an
          operating-system sandbox.
        </p>
      </section>
      <section>
        <h2>Reports still need care.</h2>
        <p>
          CLI reports mask values but include paths, locations, and partial
          value characters. API reports fully redact values and filenames. Both
          can reveal service names and finding counts. Treat reports as
          sensitive and review any upload destination. Scanned content is never
          executed.
        </p>
      </section>
      <section className="guide-callout">
        <h2>Found an exposed credential?</h2>
        <p>
          Revoke or rotate it, update consumers, and review provider access
          logs. Deleting a line does not remove Git history. Follow the
          finding’s service-specific response guidance.
        </p>
      </section>
      <section>
        <h2>Report a vulnerability privately.</h2>
        <p>
          Do not post credentials, private code, or exploit details in a public
          issue. Use GitHub’s private reporting flow if enabled. Otherwise open
          a minimal issue asking for a private contact channel. Only the latest
          development version is maintained; no response-time guarantee is
          offered.
        </p>
        <a className="text-link" href={`${repository}/security`}>
          Repository security page →
        </a>
      </section>
      <p className="source-links">
        <SourceLink path="SECURITY.md">Security policy</SourceLink>
        <SourceLink path="docs/threat-model.md">Threat model</SourceLink>
        <SourceLink path="PRIVACY.md">Privacy policy</SourceLink>
      </p>
    </Guide>
  );
}
