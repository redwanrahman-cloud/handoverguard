# HandoverGuard AWS architecture

This stack is the competition deployment of HandoverGuard. It is intentionally designed so a
judge can inspect what each AWS service contributes instead of seeing an opaque click-to-result
demo.

## Live path

1. **Amazon API Gateway** accepts a synthetic raw shift note and allocates a run ID.
2. **Amazon S3** preserves the raw input as a versioned object.
3. **Amazon EventBridge** turns the object-created event into an operational trigger.
4. **Amazon SQS** buffers and retries agent work; a dead-letter queue exposes failures.
5. **Amazon Bedrock AgentCore Runtime** hosts the Strands supervisor.
6. **Amazon Bedrock Guardrails** masks guest PII before inference and can block unsafe input.
7. **Amazon Nova Lite** extracts bilingual issues, merges duplicates, and proposes structured work.
8. **AgentCore Gateway** exposes a narrow MCP tool surface backed by **AWS Lambda**.
9. **Amazon DynamoDB** applies idempotency and stores run, issue, task, approval, and trace state.
10. **AWS Step Functions** uses a callback token to enforce a real human approval wait.
11. **Amazon SNS** emits approval notifications without performing the proposed external action.
12. **Amazon S3** stores a canonical SHA-256 evidence packet for the completed run.
13. **Amazon CloudWatch/X-Ray** provide operational metrics and managed traces.
14. **Amazon CloudFront** serves the public judge console over HTTPS.

Nova never receives a tool called `approve`, `send`, `charge`, or `refund`. It can only submit a
structured issue through `route_issue`. A deterministic Lambda policy then creates an internal
task or starts Step Functions. This makes the human-authority boundary independent of prompt
wording and model behavior.

## Build and synthesize

```bash
cd infra
npm ci
npm run build
npm run build:agent
npm run synth
```

`npm run build:agent` produces an ARM64/Python 3.13 AgentCore code bundle and prints its SHA-256.

## Two-stage deployment

The base stack is deployed first because the AgentCore artifact bucket is created by that stack:

```bash
npx cdk deploy --require-approval never --parameters DeployAgentCore=false
```

Upload `cloud/agent/runtime.zip` under an immutable key (for example
`agent/runtime-<digest>.zip`), then enable the runtime with that key:

```bash
npx cdk deploy --require-approval never \
  --parameters DeployAgentCore=true \
  --parameters AgentArtifactKey=agent/runtime-<digest>.zip
```

The stack outputs the public judge URL, API URL, AgentCore Gateway URL, Guardrail ID, approval
workflow ARN, table name, and data bucket name.

## Safety and cost controls

- Synthetic demo data only; no PMS or guest system is connected.
- The public input is limited to 10,000 characters.
- API Gateway throttles the anonymous judge API to a small burst of five and two requests per
  second thereafter.
- The gateway tools cannot execute external hotel actions.
- SQS retries failed runs three times before isolation in a dead-letter queue.
- S3 raw/evidence objects expire after 30 days; versioning remains enabled during that period.
- DynamoDB uses on-demand billing and point-in-time recovery.

## Public proof

The deployed judge console is available at:

https://d1234urv6397y8.cloudfront.net

Run IDs, model/guardrail latency, every AWS hop, Gateway routing outcomes, approval waits, and the
evidence-object location are displayed in the console. The demo is synthetic and intentionally
has no PMS, payment, messaging, or guest-contact connector.
