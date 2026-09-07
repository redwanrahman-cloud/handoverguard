# Devpost submission draft

## Project name

HandoverGuard

## Public links

- Demo video: **https://youtu.be/gr7awofIHmw**
- Live AWS demo: **https://d1234urv6397y8.cloudfront.net**
- Source code: **https://github.com/redwanrahman-cloud/handoverguard**

## Tagline

A policy-bound Strands agent that turns noisy hotel shift notes into owned work—and pauses
exactly where human judgment begins.

## Inspiration

Hotel shift handovers are full of copied notes, unresolved maintenance items, guest requests,
and exceptions with no clear owner. A summary can make the list shorter, but it does not make
the next shift safer. HandoverGuard was created to convert that operational noise into action
while preserving human authority over safety, compensation, payments, and guest contact.

## What it does

HandoverGuard sends a synthetic bilingual shift through a visible AWS execution pipeline. Nova
extracts canonical issues; deterministic policy creates routine internal work while safety,
financial, compensation, and guest-contact actions become Step Functions approval waits. A judge
can approve or reject them in the public console and watch the managed service trace update.

The competition scenario demonstrates five raw notes:

- two Arabic and English reports of the same electrical burning smell, merged into one canonical
  safety incident;
- a towel request, converted into a safe internal task;
- a SAR 250 room charge, held for financial approval;
- a prompt-injection instruction that is ignored and never becomes an action.

Approval does not silently contact a guest, move money, or close an incident. It creates an
owned follow-up task. Rejection leaves the proposed action blocked.

## How it was built

- **Amazon CloudFront** serves the public judge console over HTTPS.
- **Amazon API Gateway** validates synthetic submissions and allocates run IDs.
- **Amazon S3, EventBridge, and SQS** preserve raw input, create managed events, and isolate
  retries through a dead-letter queue.
- **Amazon Bedrock AgentCore Runtime** hosts the Python supervisor built with **Strands Agents**.
- **Amazon Bedrock Guardrails** inspects input before **Amazon Nova Lite** performs bilingual,
  schema-validated extraction.
- **AgentCore Gateway** exposes only three narrow MCP tools backed by **AWS Lambda**; there is no
  send, charge, refund, resolve, or guest-contact tool.
- **Lambda policy** decides autonomous vs. human work independently of the model.
- **Amazon DynamoDB** stores idempotent run state with point-in-time recovery.
- **AWS Step Functions callback tokens and Amazon SNS** implement genuine human approval waits.
- **Amazon S3 evidence packets and CloudWatch/X-Ray** preserve proof and operational telemetry.
- **A deterministic proof CLI** reproduces the full workflow without cloud credentials.
- **A live proof CLI** invokes Strands through Bedrock and independently verifies the resulting
  database state after the model finishes.
- **A digest-bearing evidence export** lets a reviewer download the report, approvals, full
  audit chain, zero-external-action count, and SHA-256 proof digest from the dashboard.

All demonstration data is synthetic. No real guest, employee, or property data is used.

## Challenges

The central challenge was making human oversight an enforceable system property rather than a
prompt promise. HandoverGuard therefore treats the model as a caller of narrow tools. The tools
enforce approval gates, idempotency, deduplication, and audit recording on the server side.

A second challenge was producing evidence judges can trust. The first real AgentCore run exposed
an incomplete model/tool loop; a later public run exposed bilingual duplication. We fixed both as
server-enforced invariants rather than hiding them with prompt wording. The console now shows
service-level evidence, latency, policy decisions, approval waits, and zero external actions.

## Accomplishments

- Routine work proceeds without unnecessary human interruption.
- Compensation and safety actions cannot bypass human approval.
- Duplicate notes do not create duplicate work.
- Approval and rejection are idempotent and auditable.
- Every state-changing event participates in a verified hash chain.
- The same safety invariants are covered by automated tests and judge-readable proof commands.
- Nine reproducible synthetic policy probes cover routine operations, compensation, payments,
  external-message prompt injection, the SAR 100 boundary, critical severity, and safety;
  all nine pass with zero external actions.
- A real AWS vertical slice is deployed and publicly testable at
  **https://d1234urv6397y8.cloudfront.net**.
- The live proof uses AgentCore Runtime, AgentCore Gateway, Bedrock Guardrails, Nova Lite,
  Step Functions, DynamoDB, S3, EventBridge, SQS, SNS, API Gateway, CloudFront, and CloudWatch.

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

Python, TypeScript, AWS CDK, Strands Agents SDK, Amazon Bedrock AgentCore Runtime, AgentCore
Gateway, Amazon Bedrock Guardrails, Amazon Nova Lite, AWS Lambda, Step Functions, DynamoDB, S3,
EventBridge, SQS, SNS, API Gateway, CloudFront, CloudWatch/X-Ray, FastAPI, Pydantic, SQLite,
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
- [x] Add a standalone architecture diagram
- [x] Add downloadable judge evidence packet
- [x] Deploy a public AWS-native judge console
- [x] Complete a real end-to-end AgentCore/Nova/Gateway/Step Functions run
- [x] Record the 4:24 judge-facing demo video using `docs/DEMO_VIDEO_SCRIPT.md`
- [x] Upload the approved master to YouTube and make it public
- [ ] Add final screenshots and thumbnail
- [x] Make the GitHub repository public before submission
- [ ] Fill all remaining Devpost fields and submit
