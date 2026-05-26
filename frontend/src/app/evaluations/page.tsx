import Link from "next/link";
import { apiGet } from "@/lib/api";
import { EvaluationWorkspace } from "@/components/EvaluationWorkspace";

type EvaluationSet = {
  id: number;
  name: string;
  version: string;
  domain_pack: string;
  review_framework: string;
  evaluation_type: string;
  status: string;
  claim_limit: string;
  latest_evaluation_run_id: number | null;
  latest_rule_set_version: string | null;
  latest_case_count: number | null;
};

type DetectionRun = {
  id: number;
  domain_pack: string;
  rule_set_version: string;
  event_count: number;
  alert_count: number;
};

type EventOption = {
  id: number;
  source_record_id: string;
  event_type: string;
  region: string | null;
};

export default async function EvaluationsPage() {
  const [sets, detectionRuns, chemEvents] = await Promise.all([
    apiGet<EvaluationSet[]>("/evaluations/sets"),
    apiGet<DetectionRun[]>("/evaluations/detection-runs"),
    apiGet<EventOption[]>("/events?domain=CHEM&limit=10"),
  ]);
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="text-sm uppercase tracking-[0.22em] text-[#54b5c4]">Evaluation Workspace</p>
      <h1 className="mt-3 text-3xl font-semibold">Measure routing behavior with evidence</h1>
      <p className="mt-3 max-w-4xl text-[#9db2bd]">
        Evaluation runs compare documented expectations with versioned detection results. They measure
        selected-case behavior and workload, not malicious intent or broad operational performance.
      </p>
      <div className="mt-8 overflow-hidden rounded border border-[#20323f]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#111b23] text-[#8da2ae]">
            <tr>
              {["Set", "Type", "Domain / Framework", "Latest Result", "Limit"].map((heading) => (
                <th key={heading} className="px-4 py-3 font-medium">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(sets ?? []).map((set) => (
              <tr key={set.id} className="border-t border-[#20323f] align-top">
                <td className="px-4 py-4">
                  <p className="font-medium text-white">{set.name}</p>
                  <p className="text-[#8da2ae]">{set.version}</p>
                </td>
                <td className="px-4 py-4">{set.evaluation_type}</td>
                <td className="px-4 py-4">{set.domain_pack}<br /><span className="text-[#8da2ae]">{set.review_framework}</span></td>
                <td className="px-4 py-4">
                  {set.latest_evaluation_run_id ? (
                    <Link className="text-[#75cad7]" href={`/evaluations/${set.latest_evaluation_run_id}`}>
                      Run {set.latest_evaluation_run_id} / {set.latest_rule_set_version}
                    </Link>
                  ) : "Not run"}
                </td>
                <td className="max-w-xs px-4 py-4 text-[#9db2bd]">{set.claim_limit}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {(sets ?? []).length === 0 ? <p className="p-8 text-center text-[#8da2ae]">No evaluation sets registered yet.</p> : null}
      </div>
      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        <div className="rounded border border-[#20323f] bg-[#111b23] p-5">
          <h2 className="text-lg font-medium">Recent Detection Runs</h2>
          <div className="mt-4 space-y-3 text-sm">
            {(detectionRuns ?? []).slice(0, 8).map((run) => (
              <p key={run.id} className="rounded border border-[#20323f] p-3">
                Run <strong>{run.id}</strong> | {run.domain_pack} / {run.rule_set_version}<br />
                <span className="text-[#8da2ae]">{run.event_count} events, {run.alert_count} alerts</span>
              </p>
            ))}
          </div>
        </div>
        <div className="rounded border border-[#20323f] bg-[#111b23] p-5">
          <h2 className="text-lg font-medium">Recent CHEM Events Available For Labeling</h2>
          <p className="mt-2 text-sm text-[#9db2bd]">Use only records you have reviewed and can cite.</p>
          <div className="mt-4 space-y-3 text-sm">
            {(chemEvents ?? []).map((event) => (
              <p key={event.id} className="rounded border border-[#20323f] p-3">
                Event <strong>{event.id}</strong> | {event.source_record_id}<br />
                <span className="text-[#8da2ae]">{event.event_type} / {event.region ?? "Region unavailable"}</span>
              </p>
            ))}
          </div>
        </div>
      </section>
      <EvaluationWorkspace />
    </main>
  );
}
