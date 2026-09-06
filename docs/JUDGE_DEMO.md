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

## Three-minute dashboard walkthrough

1. Start `handoverguard`, open `http://127.0.0.1:8000`, and select **Reset scenario**.
2. Select **Run the handover agent**. Point out the two internal tasks, linked duplicate,
   compensation checkpoint, safety escalation, and verified audit chain.
3. Approve the compensation checkpoint. Explain that approval creates an owned follow-up
   task; it does not contact the guest or move money.
4. Reject the safety checkpoint. Explain that rejection leaves the proposed action blocked.
5. Show the new signed audit events and repeat that all displayed data is synthetic.

The optional Bedrock/Strands route is additional integration evidence, not a dependency for
this repeatable policy-bound demonstration.

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
