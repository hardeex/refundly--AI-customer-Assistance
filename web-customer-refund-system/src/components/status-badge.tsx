const STATUS_STYLES: Record<string, string> = {
  approved: "bg-emerald-100 text-emerald-800 border-emerald-300",
  denied: "bg-red-100 text-red-800 border-red-300",
  escalated: "bg-amber-100 text-amber-800 border-amber-300",
  pending: "bg-slate-100 text-slate-700 border-slate-300",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${style}`}
    >
      {status}
    </span>
  );
}
