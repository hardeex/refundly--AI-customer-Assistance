import { NextResponse } from "next/server";

import { backendFetch, tenantApiKey, toErrorResponse } from "@/lib/backend";
import type { RefundRequestResult } from "@/lib/types";

// Proxies the customer-facing chat's submission to the backend using the
// tenant's API key, which stays server-side. The customer never sees or
// needs credentials of their own - this route stands in for "the tenant's
// own backend calling Refundly on the customer's behalf."
export async function POST(request: Request) {
  const body = await request.json();
  try {
    const result = await backendFetch<RefundRequestResult>("/v1/refund-requests", {
      method: "POST",
      token: tenantApiKey(),
      body,
    });
    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    return toErrorResponse(error);
  }
}
