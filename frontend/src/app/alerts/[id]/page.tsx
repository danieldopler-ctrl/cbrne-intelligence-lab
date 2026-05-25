import Link from "next/link";
import { AlertReviewPanel } from "@/components/AlertReviewPanel";
import { apiGet } from "@/lib/api";

type AlertDetail = {
  id: number;
  title: string;
  priority: string;
  result_label: string;
  score: number;
  confidence: string;
  status: string;
  recommended_threat_level: string;
  confirmed_threat_level: string | null;
  rationale: string;
  evidence: Array<{
    source_record_id: string;
    event_type: string;
    region: string | null;
    source_url: string | null;
    limitations: string;
    evidence: Record<string, unknown>;
  }>;
  notifications: Array<{ route_type: string; route_name: string; reporting_assessment: string }>;
  plan_reviews: Array<{ plan_code: string; applicability: string; activation_status: string }>;
};

export default async function AlertPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const alert = await apiGet<AlertDetail>(`/alerts/${id}`);
  if (!alert) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-[#9db2bd]">Alert unavailable or API is offline.</p>
        <Link href="/alerts" className="mt-4 inline-block text-[#75cad7]">Return to alerts</Link>
      </main>
    );
  }
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <Link href="/alerts" className="text-sm text-[#75cad7]">Back to alert queue</Link>
      <div className="mt-6 flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-sm uppercase tracking-[0.22em] text-[#54b5c4]">{alert.result_label}</p>
          <h1 className="mt-2 text-3xl font-semibold">{alert.title}</h1>
          <p className="mt-3 max-w-3xl text-[#9db2bd]">{alert.rationale}</p>
        </div>
        <div className="rounded border border-[#20323f] bg-[#111b23] p-5 text-sm">
          <p>Score <strong className="ml-2 text-xl text-white">{alert.score}</strong></p>
          <p className="mt-2">Recommended: {alert.recommended_threat_level}</p>
          <p className="mt-2">Confirmed: {alert.confirmed_threat_level ?? "Pending review"}</p>
        </div>
      </div>
      {alert.confirmed_threat_level === "TL4" && (
        <div className="mt-7 rounded border border-[#614a20] bg-[#1a140b] p-5 text-[#e4c275]">
          An emergency or mandatory-report condition must not wait for application workflow. Contact appropriate
          responders and complete required reporting when facts support it.
        </div>
      )}
      {alert.confirmed_threat_level !== "TL4" && alert.recommended_threat_level === "TL3" && (
        <div className="mt-7 rounded border border-[#614a20] bg-[#1a140b] p-5 text-[#e4c275]">
          Urgent analyst review recommended. If review establishes immediate danger or a mandatory-report
          condition, do not delay appropriate response or reporting.
        </div>
      )}
      <section className="mt-8 rounded border border-[#20323f] bg-[#111b23] p-6">
        <h2 className="text-xl font-medium">Evidence and limitations</h2>
        <div className="mt-5 space-y-4">
          {alert.evidence.map((item) => (
            <div key={item.source_record_id} className="rounded border border-[#20323f] bg-[#0b151c] p-4 text-sm">
              <p className="font-medium text-white">{item.source_record_id} / {item.event_type}</p>
              <p className="mt-2 text-[#9db2bd]">Region: {item.region ?? "Not provided"}</p>
              <pre className="mt-3 overflow-auto rounded bg-[#081116] p-3 text-[#bad1d9]">{JSON.stringify(item.evidence, null, 2)}</pre>
              <p className="mt-3 text-[#d1bb85]">Limitation: {item.limitations}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded border border-[#20323f] bg-[#111b23] p-6">
          <h2 className="text-xl font-medium">Recorded notification actions</h2>
          {alert.notifications.length === 0 ? (
            <p className="mt-4 text-sm text-[#8da2ae]">No notification assessment recorded.</p>
          ) : (
            <div className="mt-4 space-y-3 text-sm">
              {alert.notifications.map((notification, index) => (
                <div key={`${notification.route_name}-${index}`} className="rounded border border-[#20323f] p-3">
                  <p className="font-medium">{notification.route_type}: {notification.route_name}</p>
                  <p className="mt-1 text-[#9db2bd]">{notification.reporting_assessment}</p>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="rounded border border-[#20323f] bg-[#111b23] p-6">
          <h2 className="text-xl font-medium">Response doctrine audit</h2>
          {alert.plan_reviews.length === 0 ? (
            <p className="mt-4 text-sm text-[#8da2ae]">No doctrine applicability review recorded.</p>
          ) : (
            <div className="mt-4 space-y-3 text-sm">
              {alert.plan_reviews.map((plan, index) => (
                <div key={`${plan.plan_code}-${index}`} className="rounded border border-[#20323f] p-3">
                  <p className="font-medium">{plan.plan_code}: {plan.applicability}</p>
                  <p className="mt-1 text-[#d1bb85]">Activation status: {plan.activation_status}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
      <AlertReviewPanel alertId={alert.id} />
    </main>
  );
}
