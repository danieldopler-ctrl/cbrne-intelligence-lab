"use client";

import { FormEvent, useState } from "react";
import { API_BASE } from "@/lib/api";

const initialMapping = JSON.stringify(
  {
    source_record_id: "incident_id",
    event_date: "event_date",
    event_type: "event_type",
    region: "region",
    commodity: "commodity",
    injuries: "injuries",
    fatalities: "fatalities",
    evacuated: "evacuated",
    narrative: "narrative",
    source_url: "source_url",
  },
  null,
  2,
);

export function IngestWorkflow() {
  const [sourceId, setSourceId] = useState<number | null>(null);
  const [batchId, setBatchId] = useState<number | null>(null);
  const [bioBatchId, setBioBatchId] = useState<number | null>(null);
  const [mapping, setMapping] = useState(initialMapping);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function createSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const response = await fetch(`${API_BASE}/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    setBusy(false);
    if (!response.ok) return setMessage(data.detail ?? "Source registration failed.");
    setSourceId(data.id);
    setMessage(`Source registered as ID ${data.id}. Upload an approved extract next.`);
  }

  async function uploadFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sourceId) return setMessage("Register a source before upload.");
    setBusy(true);
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE}/ingests/upload?source_id=${sourceId}`, {
      method: "POST",
      body: data,
    });
    const result = await response.json();
    setBusy(false);
    if (!response.ok) return setMessage(result.detail ?? "Upload failed.");
    setBatchId(result.id);
    setMessage(`Batch ${result.id} stored with provenance hash. Confirm field mapping below.`);
  }

  async function normalizeAndDetect() {
    if (!batchId) return setMessage("Upload a source extract before normalization.");
    setBusy(true);
    try {
      const fields = JSON.parse(mapping);
      const normalized = await fetch(`${API_BASE}/ingests/${batchId}/normalize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version: "analyst-map-v1", fields, hazard_domain: "CHEM", event_type_default: "INCIDENT" }),
      });
      if (!normalized.ok) {
        const error = await normalized.json();
        throw new Error(error.detail ?? "Normalization failed.");
      }
      await runRules(batchId);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Workflow failed.");
    } finally {
      setBusy(false);
    }
  }

  async function syncNoaa() {
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/connectors/noaa-incidentnews/sync`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "NOAA connector failed.");
      setBatchId(result.ingest_batch_id);
      setMessage(
        `NOAA batch ${result.ingest_batch_id} stored: ${result.records_received} records, ${result.chemical_events} chemical records. Review source limitations before running rules.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "NOAA connector failed.");
    } finally {
      setBusy(false);
    }
  }

  async function importPhmsa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const data = new FormData(event.currentTarget);
      const response = await fetch(`${API_BASE}/connectors/phmsa-hazmat/import`, {
        method: "POST",
        body: data,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "PHMSA export import failed.");
      setBatchId(result.ingest_batch_id);
      setMessage(
        `PHMSA batch ${result.ingest_batch_id} stored: ${result.records_received} report rows. Review duplicate-line limitations before running rules.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "PHMSA export import failed.");
    } finally {
      setBusy(false);
    }
  }

  async function runRules(targetBatchId: number | null = batchId) {
    if (!targetBatchId) return setMessage("Select or ingest a batch before running rules.");
    const detection = await fetch(`${API_BASE}/detections/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingest_batch_id: targetBatchId }),
    });
    const result = await detection.json();
    if (!detection.ok) throw new Error(result.detail ?? "Detection failed.");
    setMessage(`${result.alerts_created} evidence-linked alerts created. Open Alerts for review.`);
  }

  async function runSafeMisuseEvaluation() {
    setBusy(true);
    try {
      const imported = await fetch(`${API_BASE}/ai-misuse/import-safe-evaluation`, { method: "POST" });
      const batch = await imported.json();
      if (!imported.ok) throw new Error(batch.detail ?? "Safe evaluation import failed.");
      const detection = await fetch(`${API_BASE}/detections/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingest_batch_id: batch.ingest_batch_id, domain_pack: "AI_MISUSE" }),
      });
      const result = await detection.json();
      if (!detection.ok) throw new Error(result.detail ?? "AI misuse assessment failed.");
      setMessage(
        `AI misuse safe evaluation run complete: ${batch.records_received} abstract cases and ${result.alerts_created} internal safety-review signals. No live prompts or external contacts were used.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "AI misuse safe evaluation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function syncCdcNndss(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const form = new FormData(event.currentTarget);
      const year = form.get("year");
      const week = form.get("week");
      const response = await fetch(`${API_BASE}/connectors/cdc-nndss/sync?year=${year}&week=${week}`, {
        method: "POST",
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "CDC NNDSS sync failed.");
      setBioBatchId(result.ingest_batch_id);
      setMessage(
        `CDC NNDSS batch ${result.ingest_batch_id} stored: ${result.records_received} weekly rows, ${result.bio_events} new BIO records (${result.revised_records} revised source rows), ${result.non_scorable_records} non-scorable rows. Counts are provisional.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "CDC NNDSS sync failed.");
    } finally {
      setBusy(false);
    }
  }

  async function syncWhoDon(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const form = new FormData(event.currentTarget);
      const limit = form.get("limit");
      const response = await fetch(`${API_BASE}/connectors/who-don/sync?limit=${limit}`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "WHO DON sync failed.");
      setBioBatchId(result.ingest_batch_id);
      setMessage(
        `WHO DON batch ${result.ingest_batch_id} stored: ${result.records_received} official reports, ${result.bio_events} new BIO records. Reports provide public-health context only.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "WHO DON sync failed.");
    } finally {
      setBusy(false);
    }
  }

  async function runBioRules() {
    if (!bioBatchId) return setMessage("Sync a biological monitoring source before running BIO rules.");
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/detections/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingest_batch_id: bioBatchId, domain_pack: "CBRNE_BIO" }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "BIO detection failed.");
      setMessage(
        `${result.alerts_created} BIO monitoring review indicators created under ${result.rule_set_version}. These indicators do not establish cause or intent.`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "BIO detection failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="rounded border border-[#294552] bg-[#101d24] p-6 lg:col-span-2">
        <p className="text-xs uppercase tracking-wide text-[#54b5c4]">Official Connector</p>
        <h2 className="mt-2 text-xl font-medium">NOAA IncidentNews public incident data</h2>
        <p className="mt-2 max-w-4xl text-sm text-[#9db2bd]">
          NOAA publishes selected response-support incidents as a public-domain CSV. It is useful for
          chemical-release monitoring but is not a complete release inventory and does not establish intent.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <button disabled={busy} onClick={syncNoaa}>Sync NOAA Public Feed</button>
          <button disabled={busy || !batchId} onClick={() => runRules()}>Run Rules On Current Batch</button>
        </div>
        <div className="mt-7 border-t border-[#294552] pt-5">
          <p className="text-xs uppercase tracking-wide text-[#54b5c4]">Official Export Import</p>
          <h3 className="mt-2 text-lg font-medium">PHMSA Hazmat Incident Reports</h3>
          <p className="mt-2 max-w-4xl text-sm text-[#9db2bd]">
            Import a delimited text export from the PHMSA search tool. The app maps official
            fatality count, injury indicator, serious-evacuation indicator, and commodity fields.
            It creates incident-level alerts by report number and evaluates released quantity only
            when PHMSA reports standardized liquid gallons (LGA). Gas and solid units stay
            unconverted.
          </p>
          <form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={importPhmsa}>
            <input name="file" type="file" accept=".txt,.tsv,.csv" required />
            <button disabled={busy} type="submit">Import PHMSA Export</button>
          </form>
        </div>
        <div className="mt-7 border-t border-[#294552] pt-5">
          <p className="text-xs uppercase tracking-wide text-[#54b5c4]">Biological Monitoring</p>
          <h3 className="mt-2 text-lg font-medium">CDC NNDSS weekly provisional data</h3>
          <p className="mt-2 max-w-4xl text-sm text-[#9db2bd]">
            Sync one reporting week of official aggregate surveillance data. Weekly counts can change
            as reporting is revised or delayed; review indicators do not identify cause or intent.
          </p>
          <form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={syncCdcNndss}>
            <input name="year" type="number" min="2014" max="2100" defaultValue="2026" required />
            <input name="week" type="number" min="1" max="53" defaultValue="19" required />
            <button disabled={busy} type="submit">Sync CDC Reporting Week</button>
          </form>
          <h3 className="mt-6 text-lg font-medium">WHO Disease Outbreak News</h3>
          <p className="mt-2 max-w-4xl text-sm text-[#9db2bd]">
            Sync a bounded set of official public outbreak reports for analyst context. A report is
            not evidence of deliberate release or attribution.
          </p>
          <form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={syncWhoDon}>
            <input name="limit" type="number" min="1" max="100" defaultValue="20" required />
            <button disabled={busy} type="submit">Sync WHO DON Reports</button>
            <button disabled={busy || !bioBatchId} type="button" onClick={runBioRules}>Run BIO Rules On Current Batch</button>
          </form>
        </div>
        <div className="mt-7 border-t border-[#294552] pt-5">
          <p className="text-xs uppercase tracking-wide text-[#54b5c4]">Controlled Evaluation</p>
          <h3 className="mt-2 text-lg font-medium">AI Misuse Risk Assessment Module</h3>
          <p className="mt-2 max-w-4xl text-sm text-[#9db2bd]">
            Load the public-safe abstract fixture set and run deterministic internal safety-review rules.
            These records are not user prompts, model outputs, threat incidents, or external-report triggers.
          </p>
          <button className="mt-4" disabled={busy} onClick={runSafeMisuseEvaluation}>
            Run Safe AI Misuse Evaluation
          </button>
        </div>
      </section>
      <section className="rounded border border-[#20323f] bg-[#111b23] p-6">
        <h2 className="text-xl font-medium">1. Register approved source</h2>
        <form className="mt-5 space-y-4" onSubmit={createSource}>
          <input name="name" placeholder="Dataset name" required />
          <input name="organization" placeholder="Publishing organization" required />
          <input name="url" placeholder="Official source URL" type="url" required />
          <div className="grid grid-cols-2 gap-3">
            <input name="source_type" defaultValue="PUBLIC_DATASET" required />
            <select name="modality" defaultValue="CHEM">
              <option>CHEM</option><option>BIO</option><option>EXP</option><option>RAD</option>
            </select>
          </div>
          <textarea name="access_terms" placeholder="Access terms / permitted use" required rows={3} />
          <textarea name="limitations" placeholder="Analytical limitations shown on alerts" required rows={3} />
          <button disabled={busy} type="submit">Register Source</button>
        </form>
      </section>
      <section className="rounded border border-[#20323f] bg-[#111b23] p-6">
        <h2 className="text-xl font-medium">2. Upload and map records</h2>
        <p className="mt-2 text-sm text-[#9db2bd]">
          Accepted formats: CSV, delimited TXT/TSV, or JSON. Raw files remain local and excluded from git.
        </p>
        <form className="mt-5 space-y-4" onSubmit={uploadFile}>
          <input name="file" type="file" accept=".csv,.json" required />
          <button disabled={busy || !sourceId} type="submit">Store Extract</button>
        </form>
        <label className="mt-6 block text-sm text-[#9db2bd]">Field mapping JSON</label>
        <textarea className="mt-2 font-mono text-sm" rows={13} value={mapping} onChange={(event) => setMapping(event.target.value)} />
        <button className="mt-4" disabled={busy || !batchId} onClick={normalizeAndDetect}>
          Normalize and Run Rules
        </button>
      </section>
      {message && (
        <p className="lg:col-span-2 rounded border border-[#294552] bg-[#101d24] p-4 text-[#b9d3dc]">{message}</p>
      )}
    </div>
  );
}
