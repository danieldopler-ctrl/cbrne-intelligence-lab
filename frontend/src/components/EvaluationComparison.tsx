"use client";

import { FormEvent, useState } from "react";
import { API_BASE } from "@/lib/api";

type Comparison = {
  routes_changed: Array<{ case_key: string; baseline_route: string; candidate_route: string }>;
  priority_upgrades: number;
  priority_downgrades: number;
  claim_limit: string;
};

type CompatibleRun = { id: number; detection_run_id: number; rule_set_version: string };

export function EvaluationComparison({ currentRunId, compatibleRuns }: { currentRunId: number; compatibleRuns: CompatibleRun[] }) {
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [message, setMessage] = useState("");

  async function compare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const baseline = form.get("baseline_evaluation_run_id");
    const response = await fetch(
      `${API_BASE}/evaluations/compare?baseline_evaluation_run_id=${baseline}&candidate_evaluation_run_id=${currentRunId}`,
    );
    if (!response.ok) {
      setMessage("Comparison requires two runs from the same evaluation set.");
      setComparison(null);
      return;
    }
    setComparison(await response.json());
    setMessage("");
  }

  return (
    <section className="mt-8 rounded border border-[#20323f] bg-[#111b23] p-5">
      <h2 className="text-lg font-medium">Compare Compatible Run</h2>
      <form onSubmit={compare} className="mt-4 flex max-w-lg items-end gap-3">
        <label className="flex-1 text-sm">Baseline evaluation run
          <select required name="baseline_evaluation_run_id" defaultValue="">
            <option disabled value="">Select a compatible run</option>
            {compatibleRuns.filter((run) => run.id !== currentRunId).map((run) => (
              <option key={run.id} value={run.id}>Evaluation {run.id} / detection {run.detection_run_id} / {run.rule_set_version}</option>
            ))}
          </select>
        </label>
        <button type="submit">Compare</button>
      </form>
      {compatibleRuns.filter((run) => run.id !== currentRunId).length === 0 ? (
        <p className="mt-4 text-sm text-[#8da2ae]">No earlier compatible evaluation run is available yet.</p>
      ) : null}
      {message ? <p className="mt-4 text-sm text-[#e0c37a]">{message}</p> : null}
      {comparison ? (
        <div className="mt-5 text-sm text-[#9db2bd]">
          <p>Priority upgrades: <strong className="text-white">{comparison.priority_upgrades}</strong> | Priority downgrades: <strong className="text-white">{comparison.priority_downgrades}</strong></p>
          <p className="mt-2">Routes changed: <strong className="text-white">{comparison.routes_changed.length}</strong></p>
          <p className="mt-3 text-[#e0c37a]">{comparison.claim_limit}</p>
        </div>
      ) : null}
    </section>
  );
}
