import { NextResponse } from "next/server";

import { backendFetch, toErrorResponse } from "@/lib/backend";
import { getAdminToken } from "@/lib/session";
import type { RefundRequestListItem } from "@/lib/types";

export async function GET(request: Request) {
  const token = await getAdminToken();
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status") ?? undefined;

  try {
    const data = await backendFetch<RefundRequestListItem[]>("/v1/refund-requests", {
      token,
      searchParams: { status },
    });
    return NextResponse.json(data);
  } catch (error) {
    return toErrorResponse(error);
  }
}
