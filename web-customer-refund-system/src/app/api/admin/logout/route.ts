import { NextResponse } from "next/server";

import { clearAdminToken } from "@/lib/session";

export async function POST() {
  await clearAdminToken();
  return NextResponse.json({ ok: true });
}
