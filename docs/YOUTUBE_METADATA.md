# YouTube publication metadata

## Title

HandoverGuard — AWS-Native Human-in-the-Loop Agent | Agents for Humans Hackathon

## Description

HandoverGuard turns noisy bilingual hotel shift notes into accountable operational work while
keeping humans in control of safety, compensation, payments, and external communication.

This video demonstrates the real public AWS deployment end to end:

- Amazon CloudFront and API Gateway receive the handover.
- Amazon S3, EventBridge, and SQS preserve and route the event.
- Amazon Bedrock AgentCore Runtime hosts the Strands supervisor.
- Bedrock Guardrails inspects the input before Amazon Nova Lite performs multilingual,
  schema-validated extraction and deduplication.
- AgentCore Gateway exposes narrow Lambda-backed tools.
- Deterministic Lambda policy creates safe internal work or starts genuine Step Functions
  approval waits.
- DynamoDB stores idempotent state; SNS, CloudWatch/X-Ray, and S3 provide notification,
  observability, and digest-bearing evidence.

The demonstrated scenario produces one safe internal task, two human approval checkpoints,
and zero external actions. All data is synthetic.

Live demo: https://d1234urv6397y8.cloudfront.net
Source code: https://github.com/redwanrahman-cloud/handoverguard

Built for the Amazon Agents for Humans Hackathon with Strands Agents SDK, Amazon Nova Lite,
Amazon Bedrock AgentCore, and AWS managed services.

## Visibility

Public (required by the official hackathon rules).

## Audience

Not made for kids.

## Category

Science & Technology

## Tags

AWS, Amazon Bedrock, Amazon Nova, Strands Agents, Bedrock AgentCore, AI agents,
human in the loop, Step Functions, serverless, hotel operations, hackathon

## Thumbnail

Use `docs/DASHBOARD.png` as the primary visual. If YouTube allows a custom thumbnail, prefer a
16:9 crop that keeps the HandoverGuard title, AWS service strip, and `0 external actions`
evidence visible.
