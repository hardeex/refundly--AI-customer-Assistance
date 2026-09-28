// The only module that talks to the FastAPI backend. Reads BACKEND_API_KEY,
// a secret, so "server-only" makes it a build error to accidentally import
// this from a client component - the key must never reach the browser.
import "server-only";

import { NextResponse } from "next/server";

const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export class BackendError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type BackendFetchOptions = {
  method?: string;
  token?: string; // Bearer token: either a tenant API key or an admin JWT
  body?: unknown;
  searchParams?: Record<string, string | undefined>;
};

export async function backendFetch<T>(
  path: string,
  options: BackendFetchOptions = {},
): Promise<T> {
  const url = new URL(path, BACKEND_API_URL);
  for (const [key, value] of Object.entries(options.searchParams ?? {})) {
    if (value !== undefined) url.searchParams.set(key, value);
  }

  const response = await fetch(url, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new BackendError(
      response.status,
      detail?.detail ?? `Backend request failed (${response.status})`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function tenantApiKey(): string {
  const key = process.env.BACKEND_API_KEY;
  if (!key) {
    throw new Error("BACKEND_API_KEY is not set - see .env.example");
  }
  return key;
}

/** Turns a BackendError (or anything else) into a NextResponse, for route
 * handlers that just want to forward the backend's status code and detail
 * message rather than handle every failure mode themselves. */
export function toErrorResponse(error: unknown): NextResponse {
  if (error instanceof BackendError) {
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }
  console.error(error);
  return NextResponse.json({ detail: "Unexpected server error" }, { status: 500 });
}
