import Link from "next/link";
import { PrintReportButton } from "@/components/PrintReportButton";
import { API_BASE, apiGet } from "@/lib/api";

type Evidence = {
  event_id: number;
  source_name: string;
  source_record_id: string;
  source_citation: string | null;
  hazard_domain: string;
  event_type: string;
  region: string | null;
  source_limitations: string;
  indicator_score: number;
  indicator_evidence: Record<string, unknown>;
};

type ReportDetail = {
  report_id: number;
  generated_at: string;
  domain_pack: string;
  rule_set_version: string;
  title: string;
  claim_summary: string;
  alerts: Array<{
    alert_id: number;
    alert_title: string;
    rule_ids: string[];
    review_framework: string;
    review_level: string;
    rule_rationale: string;
    claim_limits: string[];
    analyst_disposition: string;
    analyst_notes: string;
    reviewer: string;
    reviewed_at: string;
    evidence: Evidence[];
  }>;
};

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = await apiGet<ReportDetail>(`/reports/${id}`);
  if (!report) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-[#9db2bd]">Report unavailable or API is offline.</p>
        <Link className="mt-4 inline-block text-[#75cad7]" href="/reports">Return to reports</Link>
      </main>
    );
  }
  return (
    <main className="print-report mx-auto max-w-6xl px-6 py-10">
      <div className="no-print flex items-center justify-between gap-4">
        <Link className="text-sm text-[#75cad7]" href="/reports">Back to reports</Link>
        <div className="flex gap-3">
          <a
            className="rounded bg-[#54b5c4] px-4 py-2 text-sm font-bold text-[#061016]"
            href={`${API_BASE}/reports/${report.report_id}/export.json`}
            download
          >
            Download JSON
          </a>
          <PrintReportButton />
        </div>
      </div>
      <p className="mt-7 text-sm uppercase tracking-[0.22em] text-[#54b5c4]">{report.domain_pack}</p>
      <h1 className="mt-3 text-3xl font-semibold">{report.title}</h1>
      <p className="mt-3 text-sm text-[#9db2bd]">
        {report.rule_set_version} | Generated {new Date(report.generated_at).toLocaleString()}
      </p>
      <div className="mt-6 rounded border border-[#504222] bg-[#17150c] px-5 py-4 text-sm text-[#e0c37a]">
        <p className="font-medium">Report claim limit</p>
        <p className="mt-2">{report.claim_summary}</p>
      </div>
      <section className="mt-8 space-y-6">
        {report.alerts.map((alert) => (
          <article key={alert.alert_id} className="rounded border border-[#20323f] bg-[#111b23] p-6">
            <p className="text-xs uppercase text-[#54b5c4]">
              {alert.review_framework === "AI_MISUSE_REVIEW" ? "Misuse Review" : "Threat Review"} / {alert.review_level}
            </p>
            <h2 className="mt-2 text-xl font-medium">{alert.alert_title}</h2>
            <p className="mt-3 text-sm text-[#9db2bd]">
              Rule(s): {alert.rule_ids.join(", ")} | Disposition: {alert.analyst_disposition} | Reviewer: {alert.reviewer}
            </p>
            <p className="mt-4 text-sm">{alert.rule_rationale}</p>
            <p className="mt-4 text-sm text-[#9db2bd]">
              Analyst note: {alert.analyst_notes || "No note recorded."}
            </p>
            <div className="mt-5 space-y-4">
              {alert.evidence.map((evidence) => {
                const cdcEvidence = evidence.source_name.toLowerCase().includes("cdc");
                return (
                  <div key={evidence.event_id} className="rounded border border-[#20323f] bg-[#0b151c] p-4 text-sm">
                    <p className="font-medium text-white">{evidence.source_name} / {evidence.source_record_id}</p>
                    <p className="mt-2 text-[#9db2bd]">{evidence.event_type} | {evidence.region ?? "Region unavailable"}</p>
                    {evidence.source_citation ? (
                      <a className="mt-2 block text-[#75cad7]" href={evidence.source_citation} target="_blank" rel="noreferrer">
                        Source citation
                      </a>
                    ) : null}
                    <pre className="mt-3 overflow-auto rounded bg-[#081116] p-3 text-[#bad1d9]">
                      {JSON.stringify(evidence.indicator_evidence, null, 2)}
                    </pre>
                    <p className="mt-3 text-[#d1bb85]">Limitation: {evidence.source_limitations}</p>
                    {cdcEvidence ? (
                      <p className="mt-2 text-[#d1bb85]">CDC NNDSS counts are provisional and subject to revision.</p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
