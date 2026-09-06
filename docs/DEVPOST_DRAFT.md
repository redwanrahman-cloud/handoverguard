# Devpost submission draft

## Project name

HandoverGuard

## Tagline

A policy-bound Strands agent that turns noisy hotel shift notes into owned work—and pauses
exactly where human judgment begins.

## Inspiration

Hotel shift handovers are full of copied notes, unresolved maintenance items, guest requests,
and exceptions with no clear owner. A summary can make the list shorter, but it does not make
the next shift safer. HandoverGuard was created to convert that operational noise into action
while preserving human authority over safety, compensation, payments, and guest contact.

## What it does

HandoverGuard ingests a synthetic hotel shift, deduplicates repeated notes, applies explicit
policy, and creates routine internal follow-up tasks automatically. Sensitive actions become
human approval requests instead of model-side side effects. An operator can approve or reject
each request, and either decision is recorded in a tamper-evident SHA-256 audit chain.

The competition scenario demonstrates five notes:

- two reports of the same room maintenance issue, linked as one canonical issue;
- a late-arrival welcome pack, converted into a safe internal task;
- a compensation request, held for human approval;
- a fire-door obstruction, escalated and held for human judgment.

Approval does not silently contact a guest, move money, or close an incident. It creates an
owned follow-up task. Rejection leaves the proposed action blocked.

## How it was built

- **Strands Agents SDK** provides the agent loop and policy-bound tools.
- **Amazon Bedrock / Amazon Nova Lite** provides the live model path.
- **FastAPI and Pydantic** provide typed API and validation boundaries.
- **SQLite** stores issues, tasks, approvals, and append-only audit events.
- **Server-side policy** decides which actions are autonomous and which require approval; the
  language model cannot weaken these rules.
- **A deterministic proof CLI** reproduces the full workflow without cloud credentials.
- **A live proof CLI** invokes Strands through Bedrock and independently verifies the resulting
  database state after the model finishes.

All demonstration data is synthetic. No real guest, employee, or property data is used.

## Challenges

The central challenge was making human oversight an enforceable system property rather than a
prompt promise. HandoverGuard therefore treats the model as a caller of narrow tools. The tools
enforce approval gates, idempotency, deduplication, and audit recording on the server side.

A second challenge was producing evidence judges can trust. The deterministic and live proof
commands exit non-zero if task counts, approval counts, zero-external-action guarantees, or the
audit chain differ from the expected scenario.

## Accomplishments

- Routine work proceeds without unnecessary human interruption.
- Compensation and safety actions cannot bypass human approval.
- Duplicate notes do not create duplicate work.
- Approval and rejection are idempotent and auditable.
- Every state-changing event participates in a verified hash chain.
- The same safety invariants are covered by automated tests and judge-readable proof commands.

## What was learned

Useful human-centered agents need two complementary layers: probabilistic reasoning for
interpreting operational context and deterministic policy for authority, side effects, and
evidence. Keeping those layers separate makes an agent easier to trust, test, and operate.

## What's next

- property-system adapters behind the existing approval boundary;
- role-based approval routing and escalation timers;
- multilingual handovers for international hotel teams;
- signed exportable evidence packets for compliance review;
- operational evaluation across more synthetic shift scenarios.

## Built with

Python, Strands Agents SDK, Amazon Bedrock, Amazon Nova Lite, FastAPI, Pydantic, SQLite,
JavaScript, HTML, and CSS.

## Submission checklist

- [x] New project built during the competition period
- [x] Apache-2.0 license
- [x] AI-assistance disclosure
- [x] Synthetic-data disclosure
- [x] Deterministic judge proof
- [x] Human approval/rejection loop
- [x] Live Strands + Bedrock proof command
- [x] Capture a passing live-proof artifact from authenticated AWS CloudShell
- [ ] Record and upload the three-minute demo video
- [ ] Add final screenshots and thumbnail
- [ ] Make the GitHub repository public before submission
- [ ] Fill all remaining Devpost fields and submit
