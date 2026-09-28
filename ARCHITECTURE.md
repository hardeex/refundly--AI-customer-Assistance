# Architecture & Design Decisions

This document records why the system is put together the way it is - the
reasoning behind the structural choices, not just what the code does. It's
meant to be useful the next time a change needs to fit into this design, or
when picking the project back up after time away.

## Request flow

A refund request moves through the system as: browser → Next.js route
handler (attaches the right credential, never exposes it to the browser) →
FastAPI → Postgres for order/customer/policy data → Anthropic for a
recommendation → a plain Python function that re-checks the hard policy
rules → one row written to `refund_requests`, one to `decision_logs` →
response back to the browser, with any registered webhooks firing in the
background.

The flow was exercised end to end against the real Anthropic API, not a
mock: a damaged-item claim produces an approval citing the specific policy
rules; a final-sale refund request produces a deterministic denial; a
message attempting to override the policy gets flagged and still denied on
the hard rule. Those same cases, plus idempotency, cross-tenant isolation,
and auth failure modes, are pinned as automated tests so they don't
regress silently - see `api-customer-refund-system/README.md#testing`.

## AI integration design

The model produces the reasoning and nuance judgment - whether a claim is
plausible, whether the message is consistent with the order - but it never
makes the final call. That split exists because "the model is usually
right" is a different guarantee than "the $500 threshold is never crossed,"
and conflating the two is a common failure mode in systems that hand a
model too much authority.

The model is called with forced tool use
(`api-customer-refund-system/src/api_customer_refund_system/services/ai/client.py`):
the `RefundRecommendation` Pydantic schema is passed as the tool definition
and `tool_choice` forces the model to call it, so it cannot answer in free
text. That turns "parse whatever came back" into "validate a JSON payload
against a schema" - it removes an entire class of parsing failures and
means the output is type-checked before anything downstream touches it.

`finalize_decision()` (`services/policy_engine.py`) is a pure function with
no model call in it at all. It checks final-sale status, the amount
ceiling, and the return window in plain conditionals, and only falls
through to the model's own recommendation when none of those apply. A
message that talks the model into recommending approval on a final-sale
item is still denied, because the check doesn't read the model's reasoning
at all - only the verified order facts.

Four layers work together against a message that tries to redirect the
system's behavior:

1. The customer's message is wrapped in a `<customer_message>` tag in the
   prompt, structurally separated from the instructions around it
   (`services/ai/prompts.py`).
2. The prompt explicitly tells the model to treat anything
   instruction-shaped inside that tag as part of the complaint, not a
   command to follow.
3. Forced structured output means there's no free-text channel for an
   embedded instruction to land in even if the model complied with it.
4. The deterministic re-check doesn't trust the model's output for the
   rules that matter, so it doesn't need to detect an attempt to know the
   outcome is correct.

The first three reduce the chance the model complies with an embedded
instruction. The fourth means it doesn't matter if it does anyway - and
that's the layer that's testable without a model in the loop at all:
`test_policy_engine.py::test_prompt_injection_flag_does_not_bypass_the_final_sale_rule`
hands `finalize_decision()` a recommendation that already says "approve"
with the injection flag set, and confirms the hard rule still wins.

When a request is ambiguous, the system prompt tells the model to prefer
escalating over guessing - a deliberately raised bar for automatic
approval rather than tuning toward approving more requests.

## Backend design

Data access, policy evaluation, and AI orchestration live in separate
modules (`api/`, `services/`, `models/`) so each can be tested and reasoned
about independently. `services/policy_engine.py` has no dependency on
FastAPI, SQLAlchemy, or Anthropic - it's pure functions over plain values,
which is why its tests need no database, no mocking, and no running
server.

Postgres was a deliberate choice, not an interchangeable detail: `JSONB`
for policy rules and native `UUID` primary keys are used throughout the
schema, not kept as a compatibility shim "just in case." A codebase that
claims to be database-agnostic but has only ever run against one engine
tends to have that claim quietly stop being true the first time it
actually matters.

API keys are hashed with SHA-256; user passwords are hashed with bcrypt -
different algorithms for different problems. A password is low-entropy and
needs a slow, salted hash to resist offline brute-forcing. An API key is
already a 256-bit random token, so brute-forcing the key itself is
infeasible regardless of hash speed, and a fast deterministic hash is what
lets a key be looked up by an indexed column instead of compared against
every stored hash in turn.

Login takes the same amount of time whether the email exists or not: a
dummy bcrypt hash is checked on the "user not found" path
(`api/v1/auth.py`) so that path isn't measurably faster than a real
wrong-password check, which would otherwise let response timing reveal
which emails are registered.

## Frontend design

Every request from the website goes through a Next.js route handler under
`src/app/api/`, rather than the browser calling the backend directly. That
structure is what makes it possible for the tenant's API key to exist only
in server-side environment variables (`server-only` marks the module so
importing it from a client component fails the build, not just a
convention to remember). The admin session gets the same treatment via an
`httpOnly` cookie rather than client-side state, so a script running on the
page can't read a support agent's session token.

Two credential types resolve to the same backend, answering different
questions: the tenant API key answers "which business is this request
for" - what a real integration would present - while the admin session
answers "which staff member is looking at the dashboard," a human identity
rather than a system one. `get_current_tenant_id` resolves either to the
same `tenant_id`, so route handlers don't need to know which was used.

The admin dashboard sits in a route group (`admin/(dashboard)/`) rather
than a plain `admin/layout.tsx`, because a layout wraps its entire subtree
including the login page - an auth guard placed there would redirect the
login page to itself. The route group lets the guard wrap only the
authenticated pages without changing the URL structure.

## Data model and multi-tenancy

Every table holding business data carries a `tenant_id`, and the auth
layer resolves it before any query runs. That's more structure than a
single-business setup strictly needs today, but retrofitting tenant
isolation into a schema later is a real migration with real risk - which
table needs the column, which existing query is now missing a filter.
Building it in from the first migration costs little when there's one
tenant in practice, and means a decision made for one connected business's
customers cannot leak into another's by construction, not by convention.

## Reliability and failure handling

The Anthropic call is the one external dependency that can be slow,
rate-limited, or unavailable. It's rate-limited per caller
(`api/rate_limit.py`) because it's both the most expensive and most
abuse-prone endpoint. If the AI provider is unreachable, that one request
fails - it doesn't take down order lookups, the dashboard, or request
submission generally, since those don't depend on it.

The rate limiter's in-memory store doesn't share state across multiple
backend instances, which is the first thing that would need to change
under horizontally-scaled load - a second instance would enforce its own
limit independently, effectively doubling the real ceiling. Moving that
store to something shared (Redis, for instance) is the natural next step
if that becomes a real deployment shape. This is called out explicitly in
`api-customer-refund-system/README.md#assumptions-and-trade-offs` rather
than left implicit.

## Scope decisions

The webhook system exists because a decision only visible on a dashboard
isn't infrastructure another system can build against - it's a page with a
UI. The signed callback (`services/webhook_dispatcher.py`, verified the
same way Stripe or GitHub webhooks are) is what makes the difference
between "a refund page" and "something an e-commerce platform could
integrate against without polling." It's also scoped honestly: delivery is
best-effort rather than queued with retries, and the README says so rather
than treating the current version as production-hardened.

Policy version history has no browsing UI yet. Policies are still
versioned in the database and every decision records which version
produced it - the data supports the feature - but building a UI for
browsing that history wasn't prioritized over solidifying the core
submit-decide-audit loop. It's on the roadmap rather than silently absent.

## Security

Beyond the prompt-injection handling described above:

- **Idempotency.** `POST /refund-requests` accepts an `Idempotency-Key`
  header, so a retried request after a dropped connection returns the
  original decision instead of creating a duplicate and re-triggering an
  AI call.
- **Least privilege by construction.** The frontend's server-side code
  holds a tenant API key, not database credentials - it can only do what
  the backend's API surface exposes, not run arbitrary queries.
- **An audit trail that includes attempted misuse.** `decision_logs`
  records the exact prompt sent, the raw model output, and any flags
  raised, so a flagged injection attempt is visible in the audit trail
  even in a case where the deterministic check somehow didn't apply.
- **What isn't hardened yet, stated rather than hidden:** no role-based
  access for admin users (any active user for a tenant has full access),
  no webhook delivery retry queue, and rate limiting that doesn't survive
  multiple backend instances. The full list lives in
  `api-customer-refund-system/README.md#assumptions-and-trade-offs`.

## How the documentation is organized

The root README, the two project READMEs, and this file are deliberately
not repeating each other. The root README is the entry point for getting
the project running. The project READMEs are reference for whoever is
working inside that specific codebase. This file is the reasoning behind
the structure, for whenever that needs revisiting. The backend's
auto-generated API reference (`/docs`) rounds out the set. All four are
cross-linked so a reader lands on the right one regardless of where they
start.
