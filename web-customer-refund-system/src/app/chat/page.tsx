"use client";

import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/status-badge";
import type { Customer, CustomerOrders, Order, RefundRequestResult } from "@/lib/types";

type ChatEntry = {
  id: string;
  customerMessage: string;
  requestedAmount: number | null;
  result?: RefundRequestResult;
  error?: string;
};

export default function ChatPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [orderId, setOrderId] = useState("");
  const [message, setMessage] = useState("");
  const [requestedAmount, setRequestedAmount] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/customers")
      .then((res) => {
        if (!res.ok) throw new Error("Could not load customers.");
        return res.json() as Promise<Customer[]>;
      })
      .then(setCustomers)
      .catch((err: Error) => setLoadError(err.message));
  }, []);

  useEffect(() => {
    if (!customerId) return;
    fetch(`/api/customers/${customerId}/orders`)
      .then((res) => {
        if (!res.ok) throw new Error("Could not load orders for this customer.");
        return res.json() as Promise<CustomerOrders>;
      })
      .then((data) => setOrders(data.orders))
      .catch((err: Error) => setLoadError(err.message));
  }, [customerId]);

  function handleCustomerChange(event: React.ChangeEvent<HTMLSelectElement>) {
    setCustomerId(event.target.value);
    setOrders([]);
    setOrderId("");
  }

  const selectedOrder = orders.find((order) => order.id === orderId);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!customerId || !orderId || !message.trim()) return;

    setSubmitting(true);
    const entryId = crypto.randomUUID();
    const amountValue = requestedAmount ? Number(requestedAmount) : null;
    const sentMessage = message;

    setEntries((prev) => [
      ...prev,
      { id: entryId, customerMessage: sentMessage, requestedAmount: amountValue },
    ]);
    setMessage("");
    setRequestedAmount("");

    try {
      const response = await fetch("/api/refund-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          order_id: orderId,
          message: sentMessage,
          requested_amount: amountValue,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail ?? "Something went wrong submitting your request.");
      }
      setEntries((prev) =>
        prev.map((entry) => (entry.id === entryId ? { ...entry, result: data } : entry)),
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Request failed.";
      setEntries((prev) =>
        prev.map((entry) => (entry.id === entryId ? { ...entry, error: errorMessage } : entry)),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Refund request</h1>
        <p className="text-slate-600">
          Tell us what happened with your order and we&apos;ll get back to you right away.
        </p>
      </div>

      {loadError && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {loadError}
        </p>
      )}

      <div className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">You are</span>
          <select
            className="rounded-md border border-slate-300 px-3 py-2"
            value={customerId}
            onChange={handleCustomerChange}
          >
            <option value="">Select a customer…</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name} ({customer.email})
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Order</span>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 disabled:opacity-50"
            value={orderId}
            onChange={(event) => setOrderId(event.target.value)}
            disabled={!customerId}
          >
            <option value="">Select an order…</option>
            {orders.map((order) => (
              <option key={order.id} value={order.id}>
                {order.order_date} - ${order.total_amount.toFixed(2)}
                {order.is_final_sale ? " (final sale)" : ""}
              </option>
            ))}
          </select>
        </label>
      </div>

      {selectedOrder && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          <p className="font-medium text-slate-900">Items in this order</p>
          <ul className="mt-1 list-inside list-disc">
            {selectedOrder.items.map((item) => (
              <li key={item.id}>
                {item.quantity}× {item.description ?? item.sku} - ${item.price.toFixed(2)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {entries.length > 0 && (
        <div className="flex flex-col gap-4">
          {entries.map((entry) => (
            <div key={entry.id} className="flex flex-col gap-2">
              <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-slate-900 px-4 py-2 text-sm text-white">
                {entry.customerMessage}
                {entry.requestedAmount != null && (
                  <div className="mt-1 text-xs text-slate-300">
                    Requested: ${entry.requestedAmount.toFixed(2)}
                  </div>
                )}
              </div>

              {entry.result && (
                <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="mb-1 flex items-center gap-2">
                    <StatusBadge status={entry.result.status} />
                    {entry.result.flags.length > 0 && (
                      <span className="text-xs text-slate-500">
                        flags: {entry.result.flags.join(", ")}
                      </span>
                    )}
                  </div>
                  <p className="text-slate-700">{entry.result.reasoning}</p>
                </div>
              )}

              {entry.error && (
                <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {entry.error}
                </div>
              )}

              {!entry.result && !entry.error && (
                <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm text-slate-400">
                  Thinking…
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4"
      >
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">What happened?</span>
          <textarea
            className="min-h-24 rounded-md border border-slate-300 px-3 py-2"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Describe the issue with your order…"
            required
          />
        </label>

        <label className="flex max-w-xs flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Requested amount (optional)</span>
          <input
            type="number"
            min={0}
            step="0.01"
            className="rounded-md border border-slate-300 px-3 py-2"
            value={requestedAmount}
            onChange={(event) => setRequestedAmount(event.target.value)}
            placeholder={selectedOrder ? selectedOrder.total_amount.toFixed(2) : "0.00"}
          />
        </label>

        <button
          type="submit"
          disabled={!customerId || !orderId || !message.trim() || submitting}
          className="self-start rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-40"
        >
          {submitting ? "Submitting…" : "Submit request"}
        </button>
      </form>
    </div>
  );
}
