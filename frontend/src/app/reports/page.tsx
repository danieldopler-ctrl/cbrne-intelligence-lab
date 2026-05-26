import Link from "next/link";
import { ReportWorkspace } from "@/components/ReportWorkspace";
import { apiGet } from "@/lib/api";

type ReportIndex = {
  id: number;
  title: string;
  domain_pack: string;
  rule_set_version: string;
  alert_count: number;
  generated_at: string;
};

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: Promise<{ domain?: string }>;
}) {
  const { domain } = await searchParams;
  const domainPack =
    domain === "chem" ? "CBRNE_CHEM" : domain === "bio" ? "CBRNE_BIO" : domain === "misuse" ? "AI_MISUSE" : null;
  const path = domainPack ? `/reports?domain_pack=${domainPack}` : "/reports";
  const reports = (await apiGet<ReportIndex[]>(path)) ?? [];
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="text-sm uppercase tracking-[0.22em] text-[#54b5c4]">Reviewed Reporting</p>
      <h1 className="mt-3 text-3xl font-semibold">Source-cited reports</h1>
      <p className="mt-3 max-w-4xl text-[#9db2bd]">
        Reports assemble existing reviewed alerts, evidence citations, rule rationale, and source
        limitations. They add no new conclusion or generated narrative.
      </p>
      <nav className="mt-5 flex gap-3 text-sm">
        <Link className="rounded border border-[#20323f] px-3 py-2 text-[#75cad7]" href="/reports">All</Link>
        <Link className="rounded border border-[#20323f] px-3 py-2 text-[#75cad7]" href="/reports?domain=chem">CHEM</Link>
        <Link className="rounded border border-[#20323f] px-3 py-2 text-[#75cad7]" href="/reports?domain=bio">BIO</Link>
        <Link className="rounded border border-[#20323f] px-3 py-2 text-[#75cad7]" href="/reports?domain=misuse">AI Misuse</Link>
      </nav>
      <div className="mt-8 overflow-hidden rounded border border-[#20323f]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#111b23] text-[#8da2ae]">
            <tr>
              {["Report", "Domain", "Rule Set", "Alerts", "Generated"].map((heading) => (
                <th key={heading} className="px-4 py-3 font-medium">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id} className="border-t border-[#20323f]">
                <td className="px-4 py-4">
                  <Link className="text-[#75cad7]" href={`/reports/${report.id}`}>{report.title}</Link>
                </td>
                <td className="px-4 py-4">{report.domain_pack}</td>
                <td className="px-4 py-4">{report.rule_set_version}</td>
                <td className="px-4 py-4">{report.alert_count}</td>
                <td className="px-4 py-4">{new Date(report.generated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {reports.length === 0 ? (
          <p className="p-8 text-center text-[#8da2ae]">No reviewed reports generated yet.</p>
        ) : null}
      </div>
      <ReportWorkspace />
    </main>
  );
}
