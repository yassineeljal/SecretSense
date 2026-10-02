import type { Metadata } from "next";
import Link from "next/link";
import { Guide, SourceLink } from "@/components/guide";
export const metadata: Metadata = { title: "Model card | SecretSense" };
export default function Model() {
  return (
    <Guide
      eyebrow="EXPERIMENTAL LOCAL ML"
      title="A score is another signal."
      intro="The integrated random forest is an optional annotation tool. Rules plus entropy remain the default, and no finding is removed by model score."
    >
      <div className="three-grid">
        <section>
          <h2>13 features</h2>
          <p>
            Lengths, entropy, character composition, format indicators, and
            assignment context. Labels, IDs, provenance, and split membership
            are excluded.
          </p>
        </section>
        <section>
          <h2>100 trees</h2>
          <p>
            The historical forest uses maximum depth 6 and minimum leaf size 2.
            A fixed validation-only search selected a 0.6 annotation threshold.
          </p>
        </section>
        <section>
          <h2>Local inference</h2>
          <p>
            Explicit artifact loading and an independently trusted SHA-256 are
            required. A matching hash alone does not make an untrusted pickle
            safe.
          </p>
        </section>
      </div>
      <section>
        <h2>What the model learned from.</h2>
        <p>
          The baseline corpus contains 6,000 balanced, invented examples grouped
          by source and template family. Candidate extraction finds no negatives
          in training or validation, so the forest trains on annotated values.
          That population mismatch limits what validation tells us about actual
          scanner candidates.
        </p>
        <SourceLink path="ml/README.md">
          Dataset provenance and reproduction
        </SourceLink>
      </section>
      <section className="guide-callout">
        <h2>Known failure: missed database passwords.</h2>
        <p>
          The historical hypothetical filter misses 210 of 300 positive
          database-password examples. Three already fail candidate extraction;
          the model rejects another 207. Provider-shaped dummy values can also
          look like intended positives. Shape and entropy cannot establish
          intent or credential validity.
        </p>
        <Link className="text-link" href="/benchmarks">
          Inspect the precision and recall tradeoff →
        </Link>
      </section>
      <section>
        <h2>What is not established.</h2>
        <p>
          Scores are not calibrated probabilities. Independent review,
          real-repository performance, score calibration, and robustness across
          languages and providers remain future work. Proposed 0.4/0.8
          confidence bands are not implemented. XGBoost is a separate evaluation
          artifact, not the CLI model; Ollama is planned.
        </p>
        <SourceLink path="docs/model-card.md">
          Full model card and artifact trust policy
        </SourceLink>
      </section>
    </Guide>
  );
}
