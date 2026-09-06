# HandoverGuard — narration master

**Target:** 4:20–4:30, never over 5:00  
**Delivery:** warm, precise, quietly witty, 134–138 words per minute  
**Voice:** polished international English; calm authority; slight smile; no sales-pitch energy
**Render:** `en-US-BrianMultilingualNeural`, rate `+8%`, pitch `-1Hz`

## Performance notes

- Treat the judge as an intelligent colleague, not an audience to impress with buzzwords.
- Pause briefly after each result count and before each trust-boundary statement.
- Put gentle emphasis on **real AWS services**, **deterministic policy**, and **zero external actions**.
- Pronounce: “Nova Lite,” “Agent Core,” “Dynamo D-B,” “S-N-S,” “S-Q-S,” and “X-Ray.”
- The two lightly witty lines should sound matter-of-fact, not comedic.

## 0:00–0:25 — The problem

Hotel handovers are where good intentions occasionally go to hide. One shift leaves behind
maintenance notes, guest requests, safety incidents, and compensation decisions—often in more
than one language. A summary makes the list shorter, but it does not create accountability.
HandoverGuard turns that noise into owned work while keeping sensitive authority with people.
And everything you are about to see is running on real AWS services, live.

## 0:25–0:55 — The adversarial handover

This synthetic report contains Arabic and English descriptions of the same blocked fire door,
a routine welcome-pack request, a two-hundred-and-fifty-riyal compensation proposal, and a hidden
instruction telling the agent to ignore policy. I submit it through the public judge console.
CloudFront serves the interface, and API Gateway validates and rate-limits the request while
assigning a traceable run identifier.

## 0:55–1:30 — Durable ingestion

The untouched handover is written to a versioned Amazon S3 bucket, preserving the original
evidence. S3 emits an event through EventBridge, which decouples ingestion from processing and
delivers the work to SQS. SQS provides retry isolation, while its dead-letter queue makes failure
visible instead of quietly losing a hotel shift. A Lambda dispatcher then invokes the managed
agent with the evidence location and run ID.

## 1:30–2:20 — The AI layer

Bedrock AgentCore Runtime hosts our Strands supervisor as an immutable Python artifact. Before
reasoning begins, Bedrock Guardrails inspects the raw report. The Strands Agents SDK coordinates
Amazon Nova Lite, which performs multilingual extraction and returns a schema-validated issue
set: category, severity, requested action, amount, and a language-independent incident key.
Malformed or incomplete model output is rejected before any governed tool can run.

That key merges the Arabic and English fire-door reports into one incident. The prompt injection
remains data, not an instruction, and produces no action. Nova is responsible for understanding
the messy world—but not for granting itself authority. Put simply, the model gets a brain, not a
company credit card.

## 2:20–3:05 — Governed action

AgentCore Gateway exposes only narrow, governed tools. Each canonical issue crosses that boundary
into Lambda, where deterministic policy—not Nova—decides what may proceed. The welcome pack
becomes one internal task. Compensation and the blocked fire door become human checkpoints.
DynamoDB stores the run, issues, tasks, approvals, and trace events with idempotency protection
and point-in-time recovery. IAM roles restrict the runtime, gateway, and Lambdas to only the
resources required for this path.

The result is three canonical issues, one safe task, two approvals, and zero external actions.
That final zero is not a hopeful metric; it is an enforced boundary.

## 3:05–3:45 — Human authority

These approval buttons are not decorative. Each sensitive proposal is an AWS Step Functions
Standard workflow waiting on a callback token. SNS can notify the responsible manager while the
workflow remains durably paused. I approve one proposal and reject the other. Step Functions
resumes each execution, Lambda validates the callback, and DynamoDB records the decision.
Public approval IDs are mapped server-side; callback tokens never enter the browser.

Even approval does not contact a guest or move money. It creates accountable follow-up work
behind the same authority boundary. Humans decide; the system remembers exactly what happened.

## 3:45–4:15 — Evidence and observability

The judge console keeps every managed hop visible, including service, timing, decision, and
evidence reference. CloudWatch and X-Ray provide operational logs and traces. The final evidence
packet is stored in versioned S3 with a SHA-256 digest, allowing the run to be independently
verified. Judges can recompute the digest themselves. The public repository also includes
adversarial tests for injection, critical severity,
payments, compensation thresholds, duplicates, and attempted external actions.

The entire architecture is defined with AWS CDK, so judges can inspect and reproduce the same
system instead of trusting a manually assembled console. CloudFormation deployed more than sixty
managed resources as one reviewable stack.

## 4:15–4:25 — Close

HandoverGuard demonstrates a practical pattern for human-centered agents: Nova understands the
messy world, AWS enforces authority, and people retain the final decision.

## Audition excerpt

Hotel handovers are where good intentions occasionally go to hide. HandoverGuard turns noisy,
multilingual shift notes into accountable work. Nova understands what happened, AWS policy
services decide what may proceed, and people retain the final decision. Put simply, the model
gets a brain—not a company credit card.
