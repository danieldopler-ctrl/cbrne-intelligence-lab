import Link from "next/link";
import { API_BASE, apiGet } from "@/lib/api";
import { EvaluationComparison } from "@/components/EvaluationComparison";

type EvaluationDetail = {
  id: number;
  evaluation_set: {
    id: number;
    name: string;
    version: string;
    domain_pack: string;
    review_framework: string;
    evaluation_type: string;
    source_basis: string;
  };
  detection_run_id: number;
  rule_set_version: string;
  measures: {
    cases_in_set: number;
    cases_evaluated: number;
    cases_not_evaluated: number;
    matched_routes: number;
    missed_expected_priorities: number;
    unexpected_high_priorities: number;
    route_differences: number;
    alerts_generated_for_cases: number;
    alert_workload_by_rule: Record<string, number>;
    individual_alerts_by_level: Record<string, number>;
  };
  case_results: Array<{
    case_key: string;
    expected_review_level: string;
    generated_review_level: string;
    result: string;
    generated_rule_ids: string[];
    alert_ids: number[];
    citation: string | null;
  }>;
  claim_limit: string;
};

type CompatibleRun = { id: number; detection_run_id: number; rule_set_version: string };

export default async function EvaluationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const detail = await apiGet<EvaluationDetail>(`/evaluations/runs/${id}`);
  if (!detail) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="text-3xl font-semibold">Evaluation run not found</h1>
        <Link className="mt-4 inline-block text-[#75cad7]" href="/evaluations">Back to evaluations</Link>
      </main>
    );
  }
  const compatibleRuns = (
    await apiGet<CompatibleRun[]>(`/evaluations/sets/${detail.evaluation_set.id}/runs`)
  ) ?? [];
  const agreementLabel = detail.evaluation_set.evaluation_type === "FIXTURE_CONFORMANCE"
    ? "Fixture routing agreement"
    : "Matched routes";
  const measures = [
    ["Cases evaluated", detail.measures.cases_evaluated],
    [agreementLabel, detail.measures.matched_routes],
    ["Missed expected priorities", detail.measures.missed_expected_priorities],
    ["Unexpected high priorities", detail.measures.unexpected_high_priorities],
    ["Linked alerts", detail.measures.alerts_generated_for_cases],
  ];
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link className="text-sm text-[#75cad7]" href="/evaluations">Back to evaluations</Link>
      <p className="mt-6 text-sm uppercase tracking-[0.22em] text-[#54b5c4]">{detail.evaluation_set.evaluation_type}</p>
      <h1 className="mt-3 text-3xl font-semibold">{detail.evaluation_set.name}</h1>
      <p className="mt-3 text-[#9db2bd]">
        {detail.evaluation_set.domain_pack} / {detail.evaluation_set.review_framework} | Detection run {detail.detection_run_id} | {detail.rule_set_version}
      </p>
      <div className="mt-6 rounded border border-[#504222] bg-[#17150c] px-5 py-4 text-sm text-[#e0c37a]">
        {detail.claim_limit}
      </div>
      <section className="mt-8 grid gap-4 sm:grid-cols-5">
        {measures.map(([label, value]) => (
          <div key={label} className="rounded border border-[#20323f] bg-[#111b23] p-4">
            <p className="text-xs uppercase text-[#8da2ae]">{label}</p>
            <p className="mt-3 text-2xl font-semibold">{value}</p>
          </div>
        ))}
      </section>
      {detail.measures.cases_not_evaluated > 0 ? (
        <p className="mt-4 rounded border border-[#504222] p-3 text-[#e0c37a]">
          {detail.measures.cases_not_evaluated} case(s) were outside the selected detection run scope and are excluded from routing agreement.
        </p>
      ) : null}
      <div className="mt-8 flex justify-between">
        <h2 className="text-xl font-medium">Evidence-linked case results</h2>
        <a className="text-sm text-[#75cad7]" href={`${API_BASE}/evaluations/runs/${detail.id}`} target="_blank" rel="noreferrer">
          Open deterministic JSON report
        </a>
      </div>
      <section className="mt-6 grid gap-5 md:grid-cols-2">
        <div className="rounded border border-[#20323f] bg-[#111b23] p-5">
          <h2 className="text-lg font-medium">Alert Workload By Rule</h2>
          {Object.entries(detail.measures.alert_workload_by_rule).map(([rule, count]) => (
            <p key={rule} className="mt-3 flex justify-between text-sm text-[#9db2bd]"><span>{rule}</span><strong className="text-white">{count}</strong></p>
          ))}
        </div>
        <div className="rounded border border-[#20323f] bg-[#111b23] p-5">
          <h2 className="text-lg font-medium">Individual Alerts By Level</h2>
          {Object.entries(detail.measures.individual_alerts_by_level).map(([level, count]) => (
            <p key={level} className="mt-3 flex justify-between text-sm text-[#9db2bd]"><span>{level}</span><strong className="text-white">{count}</strong></p>
          ))}
        </div>
      </section>
      <div className="mt-4 overflow-hidden rounded border border-[#20323f]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#111b23] text-[#8da2ae]">
            <tr>
              {["Case", "Expected", "Generated", "Result", "Evidence"].map((heading) => (
                <th key={heading} className="px-4 py-3 font-medium">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {detail.case_results.map((result) => (
              <tr key={result.case_key} className="border-t border-[#20323f] align-top">
                <td className="px-4 py-4">{result.case_key}<p className="mt-1 text-[#8da2ae]">{result.citation}</p></td>
                <td className="px-4 py-4">{result.expected_review_level}</td>
                <td className="px-4 py-4">{result.generated_review_level}</td>
                <td className="px-4 py-4">{result.result}</td>
                <td className="px-4 py-4 text-[#9db2bd]">{result.generated_rule_ids.join(", ") || "No alert"}<br />Alerts: {result.alert_ids.join(", ") || "None"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <EvaluationComparison currentRunId={detail.id} compatibleRuns={compatibleRuns} />
    </main>
  );
}
