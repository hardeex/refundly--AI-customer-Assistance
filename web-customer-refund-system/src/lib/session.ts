import "server-only";

import { cookies } from "next/headers";

// Matches the backend's ACCESS_TOKEN_EXPIRE_MINUTES default (30 minutes) -
// see api_customer_refund_system/core/config.py. The cookie expiring in step
// with the token means a stale cookie never outlives the token it holds.
export const ADMIN_SESSION_COOKIE = "refundly_admin_token";
const ADMIN_SESSION_MAX_AGE_SECONDS = 30 * 60;

export async function getAdminToken(): Promise<string | undefined> {
  const store = await cookies();
  return store.get(ADMIN_SESSION_COOKIE)?.value;
}

export async function setAdminToken(token: string): Promise<void> {
  const store = await cookies();
  store.set(ADMIN_SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: ADMIN_SESSION_MAX_AGE_SECONDS,
  });
}

export async function clearAdminToken(): Promise<void> {
  const store = await cookies();
  store.delete(ADMIN_SESSION_COOKIE);
}
