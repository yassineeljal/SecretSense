"use client";
import { useState } from "react";
export function CopyCommand({ command }: { command: string }) {
  const [status, setStatus] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(command);
      setStatus("Copied commands.");
    } catch {
      setStatus("Copy unavailable. Select the commands and copy manually.");
    }
  }
  return (
    <div className="command-block">
      <pre>
        <code>{command}</code>
      </pre>
      <div>
        <button type="button" className="button secondary" onClick={copy}>
          Copy commands
        </button>
        <span role="status">{status}</span>
      </div>
    </div>
  );
}
