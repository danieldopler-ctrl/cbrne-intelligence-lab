"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

type DomainPack = "CBRNE_CHEM" | "CBRNE_BIO" | "AI_MISUSE" | "FRAUD_MONITORING";

type EligibleAlert = {
  id: number;
  title: string;
  rule_set_version: string;
  review_framework: string;
  review_level: string;
  disposition: string;
};

const CLAIM_SUMMARIES: Record<DomainPack, string> = {
  CBRNE_CHEM:
    "This report summarizes official source-derived chemical/hazmat analyst review indicators. Detections are based on public reporting records and do not establish deliberate release, malicious intent, or mandatory external notification requirements.",
  CBRNE_BIO:
    "This report summarizes official public-health surveillance and outbreak reporting analyst review indicators. CDC NNDSS counts are provisional and subject to revision. WHO Disease Outbreak News reports are official public-health event notices. Neither source establishes deliberate release, intent, or CBRN-E attribution.",
  AI_MISUSE:
    "This report summarizes AI misuse risk assessment fixture conformance review records. Results reflect controlled fixture routing behavior only. This is not real-world model safety performance or operational threat detection.",
  FRAUD_MONITORING:
    "This report summarizes fraud risk assessment fixture conformance review records. Results reflect controlled synthetic fixture routing behavior only. This is not real-world fraud detection performance, real transaction data, or an operational threat determination.",
};

export function ReportWorkspace() {
  const router = useRouter();
  const [domainPack, setDomainPack] = useState<DomainPack>("CBRNE_CHEM");
  const [alerts, setAlerts] = useState<EligibleAlert[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    setSelectedIds([]);
    fetch(`${API_BASE}/reports/eligible-alerts?domain_pack=${domainPack}`)
      .then((response) => (response.ok ? response.json() : []))
      .then((data: EligibleAlert[]) => {
        if (active) setAlerts(data);
      })
      .catch(() => {
        if (active) setAlerts([]);
      });
    return () => {
      active = false;
    };
  }, [domainPack]);

  function toggleAlert(alertId: number) {
    setSelectedIds((ids) =>
      ids.includes(alertId) ? ids.filter((id) => id !== alertId) : [...ids, alertId],
    );
  }

  async function generateReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedIds.length === 0) {
      setMessage("Select at least one reviewed alert.");
      return;
    }
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE}/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: form.get("title"), alert_ids: selectedIds }),
    });
    const payload = await response.json();
    if (response.ok) {
      router.push(`/reports/${payload.report_id}`);
      router.refresh();
    } else {
      setMessage(payload.detail ?? "Report generation failed.");
    }
    setBusy(false);
  }

  return (
    <form onSubmit={generateReport} className="mt-9 rounded border border-[#20323f] bg-[#111b23] p-6">
      <p className="text-xs uppercase text-[#54b5c4]">Generate A Report</p>
      <h2 className="mt-2 text-xl font-medium">Select analyst-reviewed alerts</h2>
      <p className="mt-2 text-sm text-[#9db2bd]">
        Only completed reviews are available. Reports remain within one domain and rule-set version.
      </p>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="text-sm">
          Domain pack
          <select
            value={domainPack}
            onChange={(event) => setDomainPack(event.target.value as DomainPack)}
          >
            <option value="CBRNE_CHEM">CHEM / TL review</option>
            <option value="CBRNE_BIO">BIO / TL review</option>
            <option value="AI_MISUSE">AI misuse / MR review</option>
            <option value="FRAUD_MONITORING">Fraud / FR review</option>
          </select>
        </label>
        <label className="text-sm">
          Report title
          <input required name="title" maxLength={200} />
        </label>
      </div>
      <div className="mt-5 rounded border border-[#504222] bg-[#17150c] p-4 text-sm text-[#e0c37a]">
        <p className="font-medium">Claim limit included in this report</p>
        <p className="mt-2">{CLAIM_SUMMARIES[domainPack]}</p>
      </div>
      <div className="mt-5 space-y-3">
        {alerts.map((alert) => (
          <label key={alert.id} className="flex gap-3 rounded border border-[#20323f] p-4 text-sm">
            <input
              className="mt-1 h-4 w-4"
              type="checkbox"
              checked={selectedIds.includes(alert.id)}
              onChange={() => toggleAlert(alert.id)}
            />
            <span>
              <span className="block text-white">{alert.title}</span>
              <span className="mt-1 block text-[#8da2ae]">
                {alert.rule_set_version} | {alert.review_level} | {alert.disposition}
              </span>
            </span>
          </label>
        ))}
        {alerts.length === 0 ? (
          <p className="rounded border border-[#20323f] p-4 text-sm text-[#8da2ae]">
            No reviewed alerts are available in this domain yet.
          </p>
        ) : null}
      </div>
      <button className="mt-5" type="submit" disabled={busy}>
        Generate Source-Cited Report
      </button>
      {message ? <p className="mt-4 text-sm text-[#e0c37a]">{message}</p> : null}
    </form>
  );
}
