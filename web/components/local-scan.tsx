"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useScanSession, type Report } from "@/components/scan-session";

const MAX_BYTES = 1_048_576;
const failure: Record<number, string> = {
  413: "This request is too large. Keep the encoded request below 1 MiB.",
  422: "The scan could not complete. Use UTF-8 text with fewer than 1,001 findings.",
  429: "Too many requests. Wait a minute, then try again.",
  503: "Both scanner slots are busy. Try again shortly.",
  504: "The scan timed out. Try a smaller input. No complete result is available.",
};
export default function Scan() {
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const uploadVersion = useRef(0);
  const { setReport } = useScanSession();
  const router = useRouter();
  useEffect(() => {
    const clear = () => {
      setContent("");
      controller.current?.abort();
      uploadVersion.current++;
    };
    window.addEventListener("pagehide", clear);
    return () => {
      clear();
      window.removeEventListener("pagehide", clear);
    };
  }, []);
  async function loadFile(file?: File) {
    const version = ++uploadVersion.current;
    setError("");
    setContent("");
    setReport(null);
    if (!file) return;
    if (file.size > MAX_BYTES) {
      setError("This file exceeds 1 MiB. Choose a smaller text file.");
      return;
    }
    setReading(true);
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(
        await file.arrayBuffer(),
      );
      if (text.includes("\0")) throw new Error();
      if (version === uploadVersion.current) setContent(text);
    } catch {
      if (version === uploadVersion.current)
        setError("Choose a UTF-8 text file without binary content.");
    } finally {
      if (version === uploadVersion.current) setReading(false);
    }
  }
  async function analyze(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setReport(null);
    const body = JSON.stringify({ content });
    if (new TextEncoder().encode(body).byteLength > MAX_BYTES) {
      setError(
        "This request is too large. Keep the encoded request below 1 MiB.",
      );
      return;
    }
    setBusy(true);
    setContent("");
    const abort = new AbortController();
    controller.current = abort;
    const timeout = setTimeout(() => abort.abort(), 12_000);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        cache: "no-store",
        credentials: "omit",
        signal: abort.signal,
      });
      if (!response.ok) {
        setError(
          failure[response.status] ||
            "The scan failed. No complete result is available.",
        );
        return;
      }
      const report: Report = await response.json();
      if (!report.complete || !Array.isArray(report.findings))
        throw new Error();
      if (abort.signal.aborted) return;
      setReport(report);
      router.push("/results");
    } catch {
      setError(
        "Could not finish the scan. Check that the local API is running, then try again.",
      );
    } finally {
      clearTimeout(timeout);
      setBusy(false);
      controller.current = null;
    }
  }
  return (
    <section className="workspace section">
      <p className="eyebrow">THE LOCAL SCANNER / 01</p>
      <h1>A closer look at your code.</h1>
      <p className="lede">
        Paste a snippet or choose a text file. We’ll look for potential secrets
        and show you the next steps.
      </p>
      <div className="scan-grid">
        <form className="input-panel" onSubmit={analyze}>
          <div className="panel-heading">
            <label htmlFor="code">Source text</label>
            <span>UTF-8 · Up to 1 MiB per request</span>
          </div>
          <textarea
            id="code"
            value={content}
            onChange={(event) => setContent(event.target.value)}
            disabled={busy || reading}
            spellCheck={false}
            autoComplete="off"
            autoCapitalize="off"
            placeholder="Paste your code here…"
            required
            aria-describedby="input-privacy"
          />
          <div className="upload-row">
            <label className="file-label">
              Choose a text file
              <input
                type="file"
                aria-label="Choose a text file"
                disabled={busy || reading}
                onChange={(event) => {
                  void loadFile(event.target.files?.[0]);
                  event.target.value = "";
                }}
              />
            </label>
            <span>
              {reading
                ? "Reading file…"
                : `${new TextEncoder().encode(content).byteLength.toLocaleString()} bytes`}
            </span>
          </div>
          <div className="submit-row">
            <p id="input-privacy">Input is cleared when scanning starts.</p>
            <button
              className="button primary"
              disabled={busy || reading || !content.trim()}
              type="submit"
            >
              {busy ? "Scanning…" : "Analyze text"}
              <span aria-hidden="true">↗</span>
            </button>
          </div>
          {busy && (
            <p className="status" role="status">
              Scanning locally. This can take a few seconds.
            </p>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>
        <aside className="scan-aside">
          <span className="outline-icon" aria-hidden="true">
            ⌘
          </span>
          <h2>Your code stays close.</h2>
          <p>
            Text is sent to the API on your machine, processed in memory, and
            never written to an application log or content cache.
          </p>
          <ul>
            <li>Fully redacted result values</li>
            <li>No credential verification</li>
            <li>No source execution</li>
            <li>No stored scan history</li>
          </ul>
          <div className="note">
            <strong>A signal, not a verdict.</strong>
            <p>
              Rules and entropy can miss secrets or flag fixtures. This demo has
              no ML scores. Review every finding locally.
            </p>
          </div>
        </aside>
      </div>
    </section>
  );
}
