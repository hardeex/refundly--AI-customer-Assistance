import { redirect } from "next/navigation";

import { getAdminToken } from "@/lib/session";
import { AdminHeader } from "./admin-header";

// Only checks that a session cookie exists, not that the JWT inside it is
// still valid - an expired token still gets past this. The dashboard page
// itself handles a 401 from the backend by redirecting to login, which
// covers that case without duplicating token verification here.
export default async function AdminDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const token = await getAdminToken();
  if (!token) {
    redirect("/admin/login");
  }

  return (
    <div className="flex flex-1 flex-col">
      <AdminHeader />
      <main className="flex flex-1 flex-col bg-slate-50">{children}</main>
    </div>
  );
}
