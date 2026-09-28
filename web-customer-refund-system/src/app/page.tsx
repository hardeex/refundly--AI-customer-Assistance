import Link from "next/link";

export default function HomePage() {
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "Refund System";

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-8 px-4 py-24 text-center">
      <div>
        <h1 className="text-3xl font-semibold text-slate-900">{appName}</h1>
        <p className="mt-2 text-slate-600">
          AI-assisted refund decisions, backed by your policy - not the other way around.
        </p>
      </div>

      <div className="grid w-full gap-4 sm:grid-cols-2">
        <Link
          href="/chat"
          className="rounded-lg border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-slate-300 hover:shadow"
        >
          <h2 className="font-medium text-slate-900">Request a refund</h2>
          <p className="mt-1 text-sm text-slate-600">Tell us what happened with your order.</p>
        </Link>
        <Link
          href="/admin"
          className="rounded-lg border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:border-slate-300 hover:shadow"
        >
          <h2 className="font-medium text-slate-900">Support dashboard</h2>
          <p className="mt-1 text-sm text-slate-600">Review recent requests and decisions.</p>
        </Link>
      </div>
    </div>
  );
}
