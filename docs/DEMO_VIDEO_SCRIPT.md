# HandoverGuard — 4:25 judge video script

> **Production note:** The approved Brian voiceover and final spoken wording live in
> [`NARRATION_MASTER.md`](NARRATION_MASTER.md). This document remains the detailed screen-action
> runbook; the reproducible continuous-capture harness lives in [`tools/video`](../tools/video).

Target duration: **4 minutes 25 seconds**. This leaves 35 seconds below the competition's
five-minute maximum. Rehearse once before recording; do not speed up to fit more content.

## Recording setup

- Record at 1080p with browser zoom around 90–100%.
- Open the public console at `https://d1234urv6397y8.cloudfront.net`.
- Keep `docs/ARCHITECTURE.png` ready in a second tab.
- Reset to a fresh scenario before recording.
- Speak at roughly 130–140 words per minute.
- Show the mouse deliberately; pause briefly when a service trace appears.

## 0:00–0:25 — Problem and promise

**Screen:** Title card, then the HandoverGuard console.

**Narration:**

> Hotel shifts inherit noisy notes in different languages: maintenance reports, guest requests,
> safety incidents, and compensation decisions. A summary alone does not create accountability.
> HandoverGuard turns that noise into owned work, but it never lets the model authorize money,
> safety resolution, or guest contact. In the next four minutes, I will show the real AWS services
> performing every step—not a prerecorded result.

## 0:25–0:55 — Submit the adversarial bilingual shift

**Screen:** Point to the Arabic/English duplicate, compensation request, routine task, and hidden
prompt-injection text. Select **Run on AWS**.

**Narration:**

> This synthetic handover contains Arabic and English reports of the same incident, a routine
> welcome-pack task, a 250-riyal compensation request, a blocked fire door, and an instruction
> telling the agent to ignore policy. I submit the raw report through the public judge console.
> Amazon CloudFront serves this interface securely at the edge, while API Gateway validates the
> request, rate-limits the public demo, and allocates a traceable run identifier.

## 0:55–1:30 — Durable event-driven ingestion

**Screen:** Follow the first trace rows as they appear.

**Narration:**

> API Gateway writes the untouched handover to a versioned Amazon S3 bucket, giving us durable
> source evidence. S3 publishes an event through Amazon EventBridge. EventBridge decouples the
> upload from processing and delivers it to Amazon SQS. SQS provides retry isolation, and its
> dead-letter queue preserves failed jobs for investigation instead of silently losing a shift.
> A Lambda dispatcher then invokes the managed agent with the S3 evidence location and run ID.

## 1:30–2:20 — AgentCore, Guardrails, Strands, and Nova

**Screen:** Show Guardrails, AgentCore Runtime, Strands/Nova, extraction latency, and deduplication
trace rows. Briefly switch to the architecture diagram if the trace pauses.

**Narration:**

> Amazon Bedrock AgentCore Runtime hosts the supervisor, packaged as an immutable Python artifact.
> Before reasoning begins, Bedrock Guardrails inspects the raw text. The supervisor is built with
> the Strands Agents SDK and uses Amazon Nova Lite for multilingual understanding. Nova extracts a
> schema-validated issue set: category, severity, requested action, amount, and a
> language-independent incident key. That key merges the Arabic and English safety reports. The
> model interprets the operation, but it does not receive authority to approve, send, refund, or
> close anything. The prompt-injection sentence becomes data, not an instruction, and creates no
> action.

## 2:20–3:05 — Governed tools and deterministic authority

**Screen:** Show AgentCore Gateway, Lambda policy, task and approval cards, and headline counts.

**Narration:**

> AgentCore Gateway exposes only narrow governed tools. It is the visible boundary between AI
> reasoning and operational side effects. Each canonical issue is routed to AWS Lambda, where
> deterministic policy—not Nova—decides what may proceed. The welcome pack becomes one internal
> task. Compensation and fire-door actions become human checkpoints. DynamoDB stores run, issue,
> task, approval, and trace state with idempotency protection and point-in-time recovery. The
> result is three canonical issues, one safe task, two approvals, and zero external actions.

## 3:05–3:45 — Real human approval workflows

**Screen:** Approve one checkpoint and reject the other. Wait for both final states.

**Narration:**

> These are not visual-only buttons. Each sensitive action is an AWS Step Functions Standard
> workflow waiting on a callback token. Amazon SNS can notify the responsible manager while the
> workflow remains durably paused. I approve one proposal and reject the other. Step Functions
> resumes each execution, Lambda validates the callback, and DynamoDB records the final decision.
> Even approval does not contact a guest or move money; it creates an owned follow-up task behind
> the same authority boundary.

## 3:45–4:15 — Evidence and observability

**Screen:** Scroll through the complete service trace and point to the evidence result.

**Narration:**

> Every managed hop remains visible in the judge trace with its service, timing, decision, and
> evidence reference. Amazon CloudWatch and X-Ray provide operational logs and traces. The final
> evidence packet is written to versioned S3 with a SHA-256 digest, so the run can be reviewed
> independently. The repository also contains automated policy probes for prompt injection,
> critical severity, payments, compensation thresholds, duplicates, and external-action attempts.

## 4:15–4:25 — Close

**Screen:** Return to the final metrics and HandoverGuard title.

**Narration:**

> HandoverGuard demonstrates a practical pattern for human-centered agents: Nova understands the
> messy world, AWS policy services enforce authority, and people retain the final decision.

## Required final edit checks

- Final exported duration is between **4:15 and 4:35** and never exceeds 5:00.
- The public URL, project name, architecture, live trace, and approve/reject result are readable.
- No AWS account IDs, credentials, callback tokens, private email, or console secrets are visible.
- The video shows a fresh run rather than relying only on static screenshots.
- Captions are enabled or burned in, especially for AWS service names.
