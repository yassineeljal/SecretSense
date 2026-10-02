"use client";
import { useState } from "react";
export type Metrics = {
  precision: number;
  recall: number;
  f1: number;
  rows: number;
  confusion_matrix: number[][];
};
export type Experiment = {
  id: string;
  title: string;
  description: string;
  source: string;
  methods: { name: string; metrics: Metrics }[];
};
const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
export function BenchmarkExplorer({
  experiments,
}: {
  experiments: Experiment[];
}) {
  const [experimentId, setExperimentId] = useState(experiments[0].id);
  const [methodIndex, setMethodIndex] = useState(1);
  const experiment = experiments.find((item) => item.id === experimentId)!;
  const method = experiment.methods[methodIndex];
  const [[tn, fp], [fn, tp]] = method.metrics.confusion_matrix;
  return (
    <div className="benchmark-explorer">
      <label className="control-label">
        Recorded experiment
        <select
          value={experimentId}
          onChange={(event) => {
            setExperimentId(event.target.value);
            setMethodIndex(1);
          }}
        >
          {experiments.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title}
            </option>
          ))}
        </select>
      </label>
      <p className="experiment-description">{experiment.description}</p>
      <div
        className="table-scroll"
        role="region"
        aria-label="Benchmark comparison"
        tabIndex={0}
      >
        <table>
          <caption>
            {experiment.title} — synthetic holdout,{" "}
            {method.metrics.rows.toLocaleString("en-US")} rows
          </caption>
          <thead>
            <tr>
              <th scope="col">Method</th>
              <th scope="col">Precision</th>
              <th scope="col">Recall</th>
              <th scope="col">F1</th>
            </tr>
          </thead>
          <tbody>
            {experiment.methods.map((item) => (
              <tr key={item.name}>
                <th scope="row">{item.name}</th>
                <td>{percent(item.metrics.precision)}</td>
                <td>{percent(item.metrics.recall)}</td>
                <td>{percent(item.metrics.f1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <label className="control-label">
        Inspect a method
        <select
          value={methodIndex}
          onChange={(event) => setMethodIndex(Number(event.target.value))}
        >
          {experiment.methods.map((item, index) => (
            <option key={item.name} value={index}>
              {item.name}
            </option>
          ))}
        </select>
      </label>
      <div className="evidence-grid" aria-live="polite" aria-atomic="true">
        <section className="metric-bars">
          <h2>{method.name}</h2>
          {(["precision", "recall", "f1"] as const).map((key) => (
            <div key={key}>
              <div className="metric-label">
                <span>
                  {key === "f1" ? "F1" : key[0].toUpperCase() + key.slice(1)}
                </span>
                <strong>{percent(method.metrics[key])}</strong>
              </div>
              <div className="metric-track" aria-hidden="true">
                <span style={{ width: `${method.metrics[key] * 100}%` }} />
              </div>
            </div>
          ))}
        </section>
        <table className="matrix">
          <caption>Confusion matrix — actual rows, predicted columns</caption>
          <thead>
            <tr>
              <th scope="col">Actual / predicted</th>
              <th scope="col">Negative</th>
              <th scope="col">Positive</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Negative</th>
              <td>
                <strong>{tn}</strong>
                <span>True negatives</span>
              </td>
              <td>
                <strong>{fp}</strong>
                <span>False positives</span>
              </td>
            </tr>
            <tr>
              <th scope="row">Positive</th>
              <td>
                <strong>{fn}</strong>
                <span>False negatives</span>
              </td>
              <td>
                <strong>{tp}</strong>
                <span>True positives</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        Precision measures how many flagged rows carry the positive label.
        Recall measures how many positive rows are found. F1 balances both.
        Labels describe invented examples, not verified credentials.
      </p>
      <a className="text-link" href={experiment.source}>
        Read this experiment’s aggregate evidence →
      </a>
    </div>
  );
}
