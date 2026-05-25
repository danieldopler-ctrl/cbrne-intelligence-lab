import Link from "next/link";
import { apiGet } from "@/lib/api";

type Metrics = { sources: number; ingest_batches: number; events: number; open_alerts: number };

export default async function Home() {
  const metrics = await apiGet<Metrics>("/metrics/summary");
  const cards = [
    ["Registered Sources", metrics?.sources ?? "-"],
    ["Ingest Batches", metrics?.ingest_batches ?? "-"],
    ["Normalized Events", metrics?.events ?? "-"],
    ["Open Alerts", metrics?.open_alerts ?? "-"],
  ];
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="rounded border border-[#504222] bg-[#17150c] px-5 py-4 text-sm text-[#e0c37a]">
        Automated indicators require analyst review. This platform does not confirm intent or
        automatically contact response or law-enforcement agencies.
      </div>
      <section className="mt-10 flex flex-col gap-4">
        <p className="text-sm uppercase tracking-[0.24em] text-[#54b5c4]">Risk Signal Platform</p>
        <h1 className="max-w-4xl text-4xl font-semibold text-white">
          Evidence-linked CBRN-E indication and warning workflow
        </h1>
        <p className="max-w-3xl text-lg text-[#9db2bd]">
          Ingest approved source extracts, normalize events, execute visible detection rules, and
          document review, escalation, and response-doctrine relevance.
        </p>
      </section>
      <section className="mt-10 grid gap-4 sm:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded border border-[#20323f] bg-[#111b23] p-5">
            <p className="text-xs uppercase tracking-wide text-[#8da2ae]">{label}</p>
            <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
          </div>
        ))}
      </section>
      {!metrics && (
        <p className="mt-4 text-sm text-[#8da2ae]">
          API is not running yet. Start the backend after PostgreSQL setup to populate metrics.
        </p>
      )}
      <section className="mt-12 grid gap-5 md:grid-cols-2">
        <Link href="/sources" className="rounded border border-[#20323f] bg-[#111b23] p-6 hover:border-[#54b5c4]">
          <p className="text-xs uppercase text-[#54b5c4]">01 / Ingest</p>
          <h2 className="mt-2 text-xl font-medium">Register and map a source</h2>
          <p className="mt-2 text-sm text-[#9db2bd]">Load a CSV or JSON extract with provenance and limitations.</p>
        </Link>
        <Link href="/alerts" className="rounded border border-[#20323f] bg-[#111b23] p-6 hover:border-[#54b5c4]">
          <p className="text-xs uppercase text-[#54b5c4]">02 / Review</p>
          <h2 className="mt-2 text-xl font-medium">Review detected indicators</h2>
          <p className="mt-2 text-sm text-[#9db2bd]">Examine evidence and record threat level and disposition.</p>
        </Link>
      </section>
    </main>
  );
}
