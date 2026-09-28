import { NextResponse } from "next/server";

import { backendFetch, tenantApiKey, toErrorResponse } from "@/lib/backend";
import type { CustomerOrders } from "@/lib/types";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ customerId: string }> },
) {
  const { customerId } = await params;
  try {
    const data = await backendFetch<CustomerOrders>(`/v1/customers/${customerId}/orders`, {
      token: tenantApiKey(),
    });
    return NextResponse.json(data);
  } catch (error) {
    return toErrorResponse(error);
  }
}
