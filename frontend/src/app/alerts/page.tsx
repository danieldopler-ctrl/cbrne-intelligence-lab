import Link from "next/link";
import { apiGet } from "@/lib/api";

type Alert = {
  id: number;
  title: string;
  priority: string;
  result_label: string;
  score: number;
  status: string;
  recommended_threat_level: string;
  created_at: string;
};

export default async function AlertsPage() {
  const alerts = (await apiGet<Alert[]>("/alerts")) ?? [];
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="text-sm uppercase tracking-[0.22em] text-[#54b5c4]">Analyst Queue</p>
      <h1 className="mt-3 text-3xl font-semibold">Evidence-linked alerts</h1>
      <p className="mt-3 text-[#9db2bd]">
        This queue shows the latest detection run. Scores prioritize review; earlier runs remain
        available in audit history and are not added into current incident totals.
      </p>
      <div className="mt-8 overflow-hidden rounded border border-[#20323f]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#111b23] text-[#8da2ae]">
            <tr>
              {["Alert", "Label", "Score", "Recommended Level", "Status"].map((head) => (
                <th key={head} className="px-4 py-3 font-medium">{head}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr key={alert.id} className="border-t border-[#20323f]">
                <td className="px-4 py-4">
                  <Link className="text-[#75cad7] hover:text-white" href={`/alerts/${alert.id}`}>
                    {alert.title}
                  </Link>
                </td>
                <td className="px-4 py-4">{alert.result_label}</td>
                <td className="px-4 py-4">{alert.score}</td>
                <td className="px-4 py-4">{alert.recommended_threat_level}</td>
                <td className="px-4 py-4">{alert.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {alerts.length === 0 && (
          <p className="p-8 text-center text-[#8da2ae]">No alerts loaded. Ingest and process an approved extract first.</p>
        )}
      </div>
    </main>
  );
}
