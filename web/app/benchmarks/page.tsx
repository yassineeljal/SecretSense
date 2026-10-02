import type { Metadata } from "next";
import baseline from "../../../ml/results/baseline.json";
import fresh from "../../../ml/results/xgboost.json";
import { Guide, repository, SourceLink } from "@/components/guide";
import {
  BenchmarkExplorer,
  type Experiment,
} from "@/components/benchmark-explorer";
export const metadata: Metadata = {
  title: "Recorded benchmarks | SecretSense",
};
const oldMetrics = baseline.evaluation.test.metrics;
const newMetrics = fresh.evaluation.test.metrics;
const experiments: Experiment[] = [
  {
    id: "historical",
    title: "Sprint 3 · historical holdout",
    description:
      "Recorded September 30, 2026. 6,000 synthetic examples split 3,600 / 1,200 / 1,200 by source and template groups; 600 positives and 600 negatives in the test set. Validation had no extracted negative candidates, limiting model selection.",
    source: `${repository}/blob/main/ml/results/baseline.json`,
    methods: [
      { name: "Regex only", metrics: oldMetrics.regex_only },
      {
        name: "Rules + entropy (default)",
        metrics: oldMetrics.rules_and_entropy,
      },
      {
        name: "Historical forest filter (hypothetical)",
        metrics: oldMetrics.candidate_pipeline_model,
      },
    ],
  },
  {
    id: "fresh",
    title: "Sprint 5 · fresh candidate holdout",
    description:
      "Recorded October 1, 2026. 2,400 new synthetic examples with both candidate labels in every split. The reserved test set has 300 positives and 300 negatives. Forest and XGBoost selection was frozen before constructing this holdout.",
    source: `${repository}/blob/main/ml/results/xgboost.json`,
    methods: [
      { name: "Regex only", metrics: newMetrics.regex_only },
      {
        name: "Rules + entropy (default)",
        metrics: newMetrics.rules_and_entropy,
      },
      {
        name: "Retrained forest filter (experimental)",
        metrics: newMetrics.random_forest_filter,
      },
      {
        name: "XGBoost filter (experimental)",
        metrics: newMetrics.xgboost_filter,
      },
    ],
  },
];
export default function Benchmarks() {
  return (
    <Guide
      eyebrow="MEASURED, WITH LIMITS"
      title="The tradeoffs, in the open."
      intro="Explore two recorded synthetic evaluations. These results describe these datasets; they do not establish real-world detection quality."
    >
      <BenchmarkExplorer experiments={experiments} />
      <section className="guide-callout">
        <h2>Why the scanner keeps every candidate.</h2>
        <p>
          The historical model filter reduces recall from 99.50% to 65.00%,
          rejecting 207 additional positive examples beyond the rules’ three
          misses. Optional CLI scoring therefore annotates every finding without
          hiding any. On the fresh holdout, XGBoost and the retrained forest
          tie; each still retains 250 authored negative fixtures.
        </p>
      </section>
      <section>
        <h2>Different populations. Separate conclusions.</h2>
        <p>
          Do not compare changes across these two holdouts as model improvement:
          their groups and distributions differ. Neither dataset has independent
          human adjudication or unseen real-repository evaluation. Both holdouts
          are now observed and must not become tuning data. Sprint 4 reproduced
          the historical results; it was not a new evaluation.
        </p>
        <SourceLink path="docs/benchmarks.md">
          Protocol, interpretation, and reproduction
        </SourceLink>
      </section>
    </Guide>
  );
}
