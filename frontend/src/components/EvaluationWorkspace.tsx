"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

export function EvaluationWorkspace() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function registerFixture() {
    setBusy(true);
    const response = await fetch(`${API_BASE}/evaluations/register-ai-misuse-fixture`, { method: "POST" });
    setMessage(response.ok ? "Safe fixture evaluation set registered." : "Registration failed. Import the safe fixture first.");
    setBusy(false);
    router.refresh();
  }

  async function createChemSet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE}/evaluations/sets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        version: form.get("version"),
        domain_pack: "CBRNE_CHEM",
        review_framework: "THREAT_LEVEL",
        evaluation_type: "REVIEWED_BENCHMARK",
        description: form.get("description"),
        source_basis: form.get("source_basis"),
        claim_limit: "This report measures rule behavior on selected analyst-labeled public-source benchmark records. It does not establish intent, population-level detection rates, or operational readiness.",
        status: "DRAFT",
      }),
    });
    const data = response.ok ? await response.json() : null;
    setMessage(response.ok ? `CHEM benchmark set created: ${data.evaluation_set_id}.` : "Unable to create benchmark set.");
    setBusy(false);
    router.refresh();
  }

  async function addChemCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const setId = form.get("evaluation_set_id");
    const response = await fetch(`${API_BASE}/evaluations/sets/${setId}/cases`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        normalized_event_id: Number(form.get("normalized_event_id")),
        case_key: form.get("case_key"),
        expected_review_level: form.get("expected_review_level"),
        expected_rule_ids: [],
        label_rationale: form.get("label_rationale"),
        citation: form.get("citation"),
        label_status: "ANALYST_REVIEWED",
      }),
    });
    setMessage(response.ok ? "Reviewed benchmark case recorded." : "Case was not accepted. Confirm the event domain, citation, and level.");
    setBusy(false);
    router.refresh();
  }

  async function runEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE}/evaluations/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        evaluation_set_id: Number(form.get("evaluation_set_id")),
        detection_run_id: Number(form.get("detection_run_id")),
      }),
    });
    const data = response.ok ? await response.json() : null;
    setMessage(response.ok ? `Evaluation completed: run ${data.evaluation_run_id}.` : "Evaluation could not be completed for that set/run pair.");
    setBusy(false);
    router.refresh();
  }

  return (
    <section className="mt-10 grid gap-5 lg:grid-cols-2">
      <div className="rounded border border-[#20323f] bg-[#111b23] p-5">
        <p className="text-xs uppercase text-[#54b5c4]">Fixture Conformance</p>
        <h2 className="mt-2 text-lg font-medium">AI misuse safe fixture</h2>
        <p className="mt-2 text-sm text-[#9db2bd]">
          Registers the existing public-safe fixture only. This is not real-world model safety performance.
        </p>
        <button className="mt-4" type="button" onClick={registerFixture} disabled={busy}>
          Register Safe Fixture Evaluation
        </button>
      </div>
      <form onSubmit={runEvaluation} className="rounded border border-[#20323f] bg-[#111b23] p-5">
        <p className="text-xs uppercase text-[#54b5c4]">Evaluate</p>
        <h2 className="mt-2 text-lg font-medium">Run against existing detections</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-sm">Evaluation set ID<input required name="evaluation_set_id" type="number" /></label>
          <label className="text-sm">Detection run ID<input required name="detection_run_id" type="number" /></label>
        </div>
        <button className="mt-4" type="submit" disabled={busy}>Run Evaluation</button>
      </form>
      <form onSubmit={createChemSet} className="rounded border border-[#20323f] bg-[#111b23] p-5">
        <p className="text-xs uppercase text-[#54b5c4]">CHEM Benchmark</p>
        <h2 className="mt-2 text-lg font-medium">Create reviewed benchmark set</h2>
        <p className="mt-2 text-sm text-[#9db2bd]">Selected public-source records only; this does not establish intent or broad detection rates.</p>
        <div className="mt-4 grid gap-3">
          <label className="text-sm">Name<input required name="name" /></label>
          <label className="text-sm">Version<input required name="version" placeholder="CHEM_REVIEWED_BENCHMARK_V0.1" /></label>
          <label className="text-sm">Description<textarea required name="description" /></label>
          <label className="text-sm">Source basis<textarea required name="source_basis" /></label>
        </div>
        <button className="mt-4" type="submit" disabled={busy}>Create Benchmark Set</button>
      </form>
      <form onSubmit={addChemCase} className="rounded border border-[#20323f] bg-[#111b23] p-5">
        <p className="text-xs uppercase text-[#54b5c4]">Label Existing Event</p>
        <h2 className="mt-2 text-lg font-medium">Add reviewed benchmark case</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-sm">Set ID<input required name="evaluation_set_id" type="number" /></label>
          <label className="text-sm">Normalized event ID<input required name="normalized_event_id" type="number" /></label>
          <label className="text-sm">Case key<input required name="case_key" /></label>
          <label className="text-sm">Expected TL
            <select required name="expected_review_level" defaultValue="TL2">
              {["TL0", "TL1", "TL2", "TL3", "TL4"].map((level) => <option key={level}>{level}</option>)}
            </select>
          </label>
        </div>
        <label className="mt-3 block text-sm">Label rationale<textarea required name="label_rationale" /></label>
        <label className="mt-3 block text-sm">Public-source citation<textarea required name="citation" /></label>
        <button className="mt-4" type="submit" disabled={busy}>Record Benchmark Case</button>
      </form>
      {message ? <p className="lg:col-span-2 rounded border border-[#20323f] px-4 py-3 text-sm text-[#75cad7]">{message}</p> : null}
    </section>
  );
}
