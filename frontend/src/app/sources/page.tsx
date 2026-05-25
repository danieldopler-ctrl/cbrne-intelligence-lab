import { IngestWorkflow } from "@/components/IngestWorkflow";

export default function SourcesPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="text-sm uppercase tracking-[0.22em] text-[#54b5c4]">Source Registry</p>
      <h1 className="mt-3 text-3xl font-semibold">Ingest approved source records</h1>
      <p className="mt-3 max-w-3xl text-[#9db2bd]">
        Record source terms and limitations before importing a local extract. Detection rules run only after
        the analyst confirms how source fields map to the common event schema.
      </p>
      <div className="mt-8">
        <IngestWorkflow />
      </div>
    </main>
  );
}
