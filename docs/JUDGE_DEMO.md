# Judge demo runbook

HandoverGuard includes a repeatable proof that needs no AWS credentials, network access,
or browser. It runs the complete synthetic night-shift scenario against a fresh in-memory
database and exits non-zero if a safety invariant fails.

```bash
handoverguard-demo
```

For machine-readable evidence:

```bash
handoverguard-demo --json
```

## What the proof demonstrates

1. Five synthetic shift notes are ingested.
2. One duplicate is linked rather than actioned twice.
3. Two routine internal tasks are created autonomously.
4. Compensation and safety actions remain held at two human checkpoints.
5. No external message, payment, compensation, or safety resolution is executed.
6. All ten operational events pass SHA-256 audit-chain verification.

Expected headline result:

```text
HandoverGuard deterministic judge proof: PASS
```

## 4:25 public AWS walkthrough

Use the timed narration and screen directions in [`DEMO_VIDEO_SCRIPT.md`](DEMO_VIDEO_SCRIPT.md).
The target duration is 4:25, leaving 35 seconds below the five-minute maximum.

1. Open **https://d1234urv6397y8.cloudfront.net** and point out the visible AWS pipeline.
2. Select **Run on AWS**. The input deliberately contains Arabic/English duplication and a
   prompt-injection attempt.
3. Narrate each live hop: API Gateway, versioned S3 input, EventBridge/SQS delivery, AgentCore
   Runtime, Guardrails latency, Nova/Strands extraction, Gateway tools, Lambda policy, DynamoDB,
   Step Functions, and S3 evidence.
4. Show the expected outcome: three canonical issues, one safe internal task, two approval waits,
   and zero external actions.
5. Approve one checkpoint and reject the other. Show both Step Functions resume events and final
   `APPROVED` / `REJECTED` cards.

The local deterministic proof remains the offline fallback; the public AWS path is the primary
competition demonstration.

## Live Strands + Amazon Nova evidence

With an authenticated AWS session, run:

```bash
AWS_REGION=us-east-1 handoverguard-live-proof
```

This separate proof invokes the real Strands agent through Amazon Bedrock, then checks the
database independently of the model. A passing run proves the agent created exactly two safe
internal tasks, held exactly two sensitive actions for human approval, executed no external
actions, and preserved the audit chain. Use the deterministic command as the reliable demo
backbone and the live command as cloud-integration evidence.
