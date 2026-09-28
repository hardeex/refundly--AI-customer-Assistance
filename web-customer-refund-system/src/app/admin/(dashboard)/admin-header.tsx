"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export function AdminHeader() {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/admin/logout", { method: "POST" });
    router.push("/admin/login");
    router.refresh();
  }

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <Link href="/admin" className="font-semibold text-slate-900">
        Support dashboard
      </Link>
      <button
        onClick={handleLogout}
        className="text-sm text-slate-600 transition hover:text-slate-900"
      >
        Sign out
      </button>
    </header>
  );
}
