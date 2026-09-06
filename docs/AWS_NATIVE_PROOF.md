# AWS-native deployment proof

Verified on 6 September 2026 in `us-east-1` using synthetic data only.

## Public judge console

https://d1234urv6397y8.cloudfront.net

## Passing managed run

The final judge-facing run `fc1e5cb8018943628c5d8a2047096b3d` completed through the full
managed pipeline:

`CloudFront → API Gateway → S3 → EventBridge → SQS → AgentCore Runtime → Bedrock Guardrails → Nova Lite + Strands → AgentCore Gateway → Lambda policy → DynamoDB → Step Functions/SNS → S3 evidence → CloudWatch`

- Nova/Strands latency: 3,528 ms
- Bedrock Guardrails latency: 163 ms
- Raw issues extracted: 4
- Bilingual duplicates removed: 1
- Canonical issues routed: 3
- Safe internal tasks: 1
- Human approval checkpoints: 2
- External actions: 0
- Evidence packet: written to the versioned operations bucket
- Runtime artifact SHA-256:
  `1a92f5dd8317758e344caadde69f20af741840fb571d1b6cd14bee57bcb89bbb`

The public UI approval controls were also exercised: the financial checkpoint was approved and
the safety/compensation checkpoint was rejected. Step Functions resumed each callback-token
workflow and DynamoDB
recorded the final decision. Neither decision executed an external hotel action.

## Failure-first evidence

The first AgentCore run failed the verifier because Nova stopped after one issue. The runtime
was changed so Nova returns a complete schema-validated shift and the server routes every issue.
A later public run exposed an Arabic/English duplicate; the runtime now requires a
language-independent canonical incident key and applies deterministic post-model deduplication.
The final run visibly reported `raw_issues=4`, `duplicates_removed=1`, and
`canonical_issues=3` in the AWS service trace.

These failures are useful evidence: the proof is not a hard-coded green screen. It reveals model
variance, and the product converts each discovered weakness into a testable server invariant.

## Authority boundary

Nova can interpret text but cannot approve, send, charge, refund, contact a guest, or close an
incident. AgentCore Gateway exposes only `record_trace`, `route_issue`, and `write_evidence`.
Deterministic Lambda policy creates either an internal task or a Step Functions human wait.
