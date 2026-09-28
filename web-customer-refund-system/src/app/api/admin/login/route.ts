import { NextResponse } from "next/server";

import { backendFetch, toErrorResponse } from "@/lib/backend";
import { setAdminToken } from "@/lib/session";

type LoginResponse = { access_token: string; token_type: string };

// The JWT never reaches client-side JS: it's set as an httpOnly cookie here
// and only ever read back out server-side (see api/admin/refund-requests),
// so an XSS bug elsewhere on the page can't steal a support agent's session.
export async function POST(request: Request) {
  const body = await request.json();
  try {
    const { access_token } = await backendFetch<LoginResponse>("/v1/auth/login", {
      method: "POST",
      body,
    });
    await setAdminToken(access_token);
    return NextResponse.json({ ok: true });
  } catch (error) {
    return toErrorResponse(error);
  }
}
