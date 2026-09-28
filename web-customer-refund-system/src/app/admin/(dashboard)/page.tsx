"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { StatusBadge } from "@/components/status-badge";
import type { RefundRequestListItem } from "@/lib/types";

const STATUS_OPTIONS = ["all", "pending", "approved", "denied", "escalated"] as const;
type StatusFilter = (typeof STATUS_OPTIONS)[number];

export default function AdminDashboardPage() {
  const router = useRouter();
  const [requests, setRequests] = useState<RefundRequestListItem[]>([]);
  const [status, setStatus] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Bumped by the refresh button to re-trigger the effect below without a
  // real dependency changing.
  const [refreshToken, setRefreshToken] = useState(0);

  // Every state update here happens inside a promise callback, not
  // synchronously in the effect body - setting `loading` for a request the
  // user just triggered belongs to the event handler that triggered it
  // (see handleStatusChange/handleRefresh below), not to this effect.
  useEffect(() => {
    let cancelled = false;
    const query = status === "all" ? "" : `?status=${status}`;

    fetch(`/api/admin/refund-requests${query}`)
      .then(async (response) => {
        if (cancelled) return;
        if (response.status === 401) {
          router.push("/admin/login");
          return;
        }
        if (!response.ok) {
          setError("Could not load refund requests.");
          return;
        }
        setRequests(await response.json());
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load refund requests.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [status, refreshToken, router]);

  function handleStatusChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setStatus(event.target.value as StatusFilter);
    setLoading(true);
  }

  function handleRefresh() {
    setLoading(true);
    setRefreshToken((n) => n + 1);
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Refund requests</h1>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-slate-300 px-2 py-1 text-sm"
            value={status}
            onChange={handleStatusChange}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option === "all" ? "All statuses" : option}
              </option>
            ))}
          </select>
          <button
            onClick={handleRefresh}
            className="rounded-md border border-slate-300 px-3 py-1 text-sm transition hover:bg-slate-100"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Customer</th>
              <th className="px-4 py-3 font-medium">Message</th>
              <th className="px-4 py-3 font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Flags</th>
              <th className="px-4 py-3 font-medium">Submitted</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && requests.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                  No refund requests yet.
                </td>
              </tr>
            )}
            {!loading &&
              requests.map((request) => (
                <tr key={request.id} className="border-b border-slate-100 align-top last:border-0">
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {request.customer_name}
                  </td>
                  <td className="max-w-xs px-4 py-3 text-slate-600">
                    <p className="line-clamp-2">{request.message}</p>
                    {request.reasoning && (
                      <p className="mt-1 line-clamp-2 text-xs text-slate-400">
                        {request.reasoning}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                    {request.requested_amount != null
                      ? `$${request.requested_amount.toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={request.status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {request.flags.length > 0 ? request.flags.join(", ") : "—"}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-xs text-slate-500">
                    {new Date(request.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
