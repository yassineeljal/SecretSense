"use client";

import Link from "next/link";
import { useState } from "react";
import { useScanSession } from "@/components/scan-session";

export default function Results() {
  const { report, setReport } = useScanSession();
  const [severity, setSeverity] = useState("all");
  if (!report)
    return (
      <section className="empty-state">
        <p className="eyebrow">THE LOCAL SCANNER / RESULTS</p>
        <h1>A fresh start.</h1>
        <p>
          No scan is held in this tab. Results clear when you reload or leave
          the site.
        </p>
        <Link className="button primary" href="/scan">
          Start a scan ↗
        </Link>
      </section>
    );
  const findings = report.findings.filter(
    (finding) => severity === "all" || finding.severity === severity,
  );
  return (
    <section className="workspace section">
      <p className="eyebrow">THE LOCAL SCANNER / 02</p>
      <div className="result-heading">
        <div>
          <h1>
            {report.findings.length
              ? "Here’s what needs a look."
              : "No candidates found."}
          </h1>
          <p className="lede">
            {report.findings.length
              ? "Review these potential exposures and follow the response guidance."
              : "No pattern or entropy candidates were detected in this input."}{" "}
            A clean report is not a security guarantee.
          </p>
        </div>
        <Link
          className="button secondary"
          href="/scan"
          onClick={() => setReport(null)}
        >
          New scan ↗
        </Link>
      </div>
      <div className="result-summary">
        <div>
          <strong>{report.findings.length}</strong>
          <span>Potential findings</span>
        </div>
        <div>
          <strong>Complete</strong>
          <span>One text input scanned</span>
        </div>
        <div>
          <strong>Rules + entropy</strong>
          <span>ML scoring is not enabled</span>
        </div>
      </div>
      <div className="filter-bar">
        <h2>
          Findings <span className="count">{findings.length}</span>
        </h2>
        <label>
          Severity{" "}
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="all">All severities</option>
            {[...new Set(report.findings.map((finding) => finding.severity))]
              .sort()
              .map((value) => (
                <option key={value} value={value}>
                  {value[0].toUpperCase() + value.slice(1)}
                </option>
              ))}
          </select>
        </label>
      </div>
      <div className="findings">
        {findings.map((finding, index) => (
          <article
            className="finding"
            key={`${finding.rule_id}-${finding.line}-${finding.column}-${index}`}
          >
            <div className="finding-header">
              <div>
                <span className={`risk ${finding.severity}`}>
                  {finding.severity}
                </span>
                <h3>{finding.service}</h3>
              </div>
              <span className="location">
                submitted.txt · Line {finding.line}:{finding.column}
              </span>
            </div>
            <div className="finding-body">
              <div>
                <code className="redacted">[REDACTED]</code>
                <p>{finding.explanation}</p>
                <span className="micro">Rule: {finding.rule_id}</span>
              </div>
              <details>
                <summary>Response guidance</summary>
                <ol>
                  {finding.remediation.steps.map((step, number) => (
                    <li key={number}>{step}</li>
                  ))}
                </ol>
              </details>
            </div>
          </article>
        ))}
      </div>
      {findings.length === 0 && (
        <p className="empty-filter">No findings for this selection.</p>
      )}
      <p className="privacy-foot">
        Values and filenames are fully redacted. Results live only in this tab’s
        memory.{" "}
        <button className="text-link" onClick={() => setReport(null)}>
          Clear results
        </button>
      </p>
    </section>
  );
}
