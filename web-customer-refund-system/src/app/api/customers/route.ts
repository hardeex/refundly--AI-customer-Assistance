import { NextResponse } from "next/server";

import { backendFetch, tenantApiKey, toErrorResponse } from "@/lib/backend";
import type { Customer } from "@/lib/types";

export async function GET() {
  try {
    const customers = await backendFetch<Customer[]>("/v1/customers", {
      token: tenantApiKey(),
    });
    return NextResponse.json(customers);
  } catch (error) {
    return toErrorResponse(error);
  }
}
