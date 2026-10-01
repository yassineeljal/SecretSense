"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Finding = {
  line: number;
  column: number;
  rule_id: string;
  service: string;
  severity: string;
  explanation: string;
  remediation: { title: string; steps: string[] };
};
export type Report = { complete: boolean; findings: Finding[]; engine: string };
const Session = createContext<{
  report: Report | null;
  setReport: (report: Report | null) => void;
} | null>(null);

export function ScanSession({ children }: { children: React.ReactNode }) {
  const [report, setReport] = useState<Report | null>(null);
  useEffect(() => {
    const clear = () => setReport(null);
    window.addEventListener("pagehide", clear);
    return () => window.removeEventListener("pagehide", clear);
  }, []);
  return (
    <Session.Provider value={{ report, setReport }}>
      {children}
    </Session.Provider>
  );
}
export function useScanSession() {
  const session = useContext(Session);
  if (!session) throw new Error("Scan session is unavailable.");
  return session;
}
