# Refund System Frontend

The customer-facing chat interface and admin dashboard for the AI-powered
refund system. Talks only to the [backend API](../api-customer-refund-system)
- never directly to Anthropic - and keeps every credential (the tenant API
key, admin JWTs) server-side.

For running this together with the backend and database as one command, see
the [repo root README](../README.md) instead - this file covers the
frontend on its own (useful if the backend is already running elsewhere).
Every page also links to the backend's interactive API docs (Swagger UI) in
the footer.

## Pages

- **`/chat`** - a customer picks themselves and one of their orders from a
  dropdown (standing in for "already logged into the tenant's site"), types
  what happened, and sees the AI-assisted decision and its reasoning appear
  as a chat reply.
- **`/admin`** - a support dashboard listing recent refund requests with
  their outcome, reasoning, and any flags (e.g. a detected prompt injection
  attempt), filterable by status. Requires signing in at `/admin/login`.

## Why two different auth patterns

The backend supports two credential types - a tenant API key and a staff
JWT (see the backend README) - and this app uses both, for different
reasons:

- **Chat** calls the backend using a tenant API key that lives only in this
  app's server environment (`BACKEND_API_KEY`). The browser never sees it -
  every request from `/chat` goes through a Next.js route handler
  (`src/app/api/...`) that attaches it server-side. This is what the backend
  docs mean by "the tenant's own systems calling in on the customer's
  behalf."
- **Admin** logs in with an email/password, which the backend exchanges for
  a JWT. That token is stored as an `httpOnly` cookie (`src/lib/session.ts`)
  rather than in client-side JS state, so it can't be read or exfiltrated by
  a script running on the page - it only ever gets read back out
  server-side, in route handlers under `src/app/api/admin/`.

Neither credential is ever sent to the browser as readable JavaScript state.

## Quick start

Requires the [backend](../api-customer-refund-system) running and seeded
first (`uv run python -m api_customer_refund_system.seed.seed_data` from
that directory).

```bash
cp .env.example .env.local
npm install
npm run dev
```

The default `.env.example` already matches the backend's default
`DEMO_API_KEY`, so nothing needs to be copy-pasted between the two for local
development - just don't change one without the other (see the comment in
`.env.example` for why).

Open `http://localhost:3000`. `/chat` needs the seeded mock customers to
have anything to pick from; `/admin/login` uses the demo admin credentials
the seed script prints (`admin@northwind-outfitters.example` /
`ChangeMe123!`).

## Environment variables

See `.env.example`. `BACKEND_API_URL` and `BACKEND_API_KEY` are read only by
server-side code (route handlers, marked with the `server-only` package so
importing them from a client component is a build error) - `.env.local` is
gitignored and must never be committed.

## Project structure

```
src/
├── app/
│   ├── page.tsx                     Landing page
│   ├── chat/page.tsx                  Customer refund request flow
│   ├── admin/
│   │   ├── login/page.tsx               Public login form
│   │   └── (dashboard)/                 Auth-guarded route group
│   │       ├── layout.tsx                 Redirects to /login if no session
│   │       ├── admin-header.tsx            Sign-out button
│   │       └── page.tsx                     Refund request list + filter
│   └── api/                         Route handlers - the only code that
│       ├── customers/                 holds backend credentials. Each one
│       ├── refund-requests/           proxies one backend endpoint and
│       └── admin/                     attaches the right credential type.
├── components/
│   ├── status-badge.tsx              Shared approved/denied/escalated pill
│   └── site-footer.tsx               Link to the backend's Swagger UI docs
└── lib/
    ├── backend.ts                   Typed fetch wrapper + error handling
    ├── session.ts                   Admin JWT cookie read/write/clear
    └── types.ts                     Response shapes, hand-kept in sync
                                        with the backend's Pydantic schemas
```

## Notes

- The `(dashboard)` route group exists so the auth-guard layout wraps `/admin`
  without also wrapping `/admin/login` - a plain `admin/layout.tsx` would
  redirect the login page to itself.
