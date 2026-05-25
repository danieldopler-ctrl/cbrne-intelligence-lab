"use client";

import { FormEvent, useState } from "react";
import { API_BASE } from "@/lib/api";

export function AlertReviewPanel({ alertId }: { alertId: number }) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const response = await fetch(`${API_BASE}/alerts/${alertId}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    setBusy(false);
    setMessage(response.ok ? "Analyst review recorded in the audit trail." : result.detail ?? "Review failed.");
  }

  async function submitPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const response = await fetch(`${API_BASE}/alerts/${alertId}/plan-reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    setBusy(false);
    setMessage(response.ok ? "Response-doctrine applicability recorded." : result.detail ?? "Plan review failed.");
  }

  async function submitNotification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const response = await fetch(`${API_BASE}/alerts/${alertId}/notifications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    setBusy(false);
    setMessage(response.ok ? "Notification assessment recorded. No contact was sent by the platform." : result.detail ?? "Notification assessment failed.");
  }

  return (
    <section className="mt-8 grid gap-6 lg:grid-cols-2">
      <form onSubmit={submitReview} className="rounded border border-[#20323f] bg-[#111b23] p-6">
        <h2 className="text-xl font-medium">Analyst disposition</h2>
        <div className="mt-5 space-y-4">
          <input name="reviewer" placeholder="Reviewer identifier" required />
          <select name="threat_level" defaultValue="TL2">
            {["TL0", "TL1", "TL2", "TL3", "TL4"].map((level) => <option key={level}>{level}</option>)}
          </select>
          <select name="disposition" defaultValue="INVESTIGATE">
            {["MONITOR", "INVESTIGATE", "ESCALATE", "CLOSED_FALSE_POSITIVE", "CLOSED_NO_ACTION"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
          <textarea name="note" rows={4} placeholder="Evidence assessment and rationale" required />
          <button disabled={busy} type="submit">Record Review</button>
        </div>
      </form>
      <form onSubmit={submitPlan} className="rounded border border-[#20323f] bg-[#111b23] p-6">
        <h2 className="text-xl font-medium">Response doctrine review</h2>
        <p className="mt-2 text-sm text-[#9db2bd]">
          Potential applicability is not agency activation. Use verified status only with a documented reference.
        </p>
        <div className="mt-5 space-y-4">
          <input name="reviewer" placeholder="Reviewer identifier" required />
          <select name="plan_code" defaultValue="NIMS_ICS">
            {["NIMS_ICS", "NRF", "ESF_8", "ESF_10", "NCP_NRS", "BIA", "NRIA", "NARP", "PREVENTION_INFO_SHARING"].map((plan) => (
              <option key={plan}>{plan}</option>
            ))}
          </select>
          <select name="applicability" defaultValue="POTENTIALLY_APPLICABLE">
            <option>POTENTIALLY_APPLICABLE</option>
            <option>APPLICABLE_VERIFIED</option>
            <option>NOT_APPLICABLE</option>
          </select>
          <select name="activation_status" defaultValue="NOT_VERIFIED">
            <option>NOT_VERIFIED</option>
            <option>VERIFIED_ACTIVE</option>
            <option>VERIFIED_NOT_ACTIVE</option>
          </select>
          <input name="incident_reference" placeholder="Verified incident/EOC reference, if any" />
          <textarea name="rationale" rows={3} placeholder="Applicability rationale" required />
          <button disabled={busy} type="submit">Record Plan Review</button>
        </div>
      </form>
      <form onSubmit={submitNotification} className="rounded border border-[#20323f] bg-[#111b23] p-6 lg:col-span-2">
        <h2 className="text-xl font-medium">Notification assessment</h2>
        <p className="mt-2 text-sm text-[#9db2bd]">
          This records a decision or completed contact. The platform does not send notifications.
        </p>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <select name="threat_level" defaultValue="TL3">
            <option>TL2</option><option>TL3</option><option>TL4</option>
          </select>
          <select name="route_type" defaultValue="INTERNAL">
            <option>INTERNAL</option><option>EXTERNAL</option>
          </select>
          <input name="route_name" placeholder="Duty lead, NRC, FBI, ATF, local responder..." required />
          <select name="reporting_assessment" defaultValue="REVIEW_REQUIRED">
            <option>NOT_APPLICABLE</option>
            <option>REVIEW_REQUIRED</option>
            <option>REPORTED</option>
            <option>DECLINED_WITH_RATIONALE</option>
          </select>
          <input name="authorized_by" placeholder="Authorized by, if applicable" />
          <input name="reference_number" placeholder="Agency or case reference, if provided" />
          <textarea className="md:col-span-2" name="rationale" rows={3} placeholder="Decision rationale and follow-up owner" required />
          <button disabled={busy} type="submit">Record Notification Assessment</button>
        </div>
      </form>
      {message && <p className="lg:col-span-2 rounded border border-[#294552] bg-[#101d24] p-4 text-[#b9d3dc]">{message}</p>}
    </section>
  );
}
