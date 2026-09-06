# Competitive review and submission readiness

Reviewed 6 September 2026 against the public Agents for Humans rules and visible Devpost
project pages. Competitor descriptions are self-reported; this review does not assume that
every claimed feature is independently verified.

## Official scoring

The five judging criteria are equally weighted: technical implementation, design, potential
impact, creativity/originality, and presentation. Amazon Bedrock AgentCore deployment is not
required but can strengthen technical implementation. A public repository, README,
architecture diagram, and public demonstration/pitch video of no more than five minutes are
required. A live demo is optional but can improve the technical score. Up to 0.6 bonus points
are available through qualifying builder.aws posts.

Source: [official rules](https://agentsforhumans.devpost.com/rules)

## Relevant public competitors

- [WhyF](https://devpost.com/software/whyf) presents the strongest measured-evidence story:
  329 private real-world questionnaire rows, a staged Strands pipeline, AWS Lambda, DynamoDB,
  CDK, multiple Bedrock models, and explicit prompt-injection probes.
- [AetherOps Sentinel](https://devpost.com/software/aetherops-sentinel) emphasizes visual
  polish, live telemetry, multi-region simulation, human decision cards, and exportable audit
  reports. Its page also describes several ambitious infrastructure claims.
- [Governor Agent](https://devpost.com/software/governor-agent) is conceptually closest to
  HandoverGuard: the model inspects work while deterministic gates make allow, deny, or
  escalate decisions. Its public demo is deliberately narrow and synthetic.
- [StrandPulse](https://devpost.com/software/strandpulse-autonomous-background-work-orchestrator)
  emphasizes background workflow execution and human-in-the-loop decision cards.
- [Strands Guardian](https://devpost.com/software/strands-guardian) emphasizes broad external
  data integration and autonomous threat-intelligence correlation.

## HandoverGuard's defensible advantages

- A specific, understandable human problem instead of a generic assistant.
- A real Strands + Amazon Nova Lite run with independently checked workflow state.
- Server-enforced authority boundaries; the model cannot weaken approval policy.
- A failure-first live proof that caught incomplete model behavior before the corrected pass.
- Reproducible deterministic proof, 9/9 adversarial policy probes, zero external actions, and
  a tamper-evident audit chain.
- A complete interactive approval/rejection experience rather than a static mock-up.
- Synthetic-only demo data and an explicit AI-assistance disclosure.

## Remaining score gaps

1. **Presentation:** record and publish the required video; use the dashboard and live-proof
   evidence as the story spine.
2. **Testing access:** make the repository public and ideally deploy a free judge-accessible
   live demo through the end of judging.
3. **Impact evidence:** avoid invented claims. Add a clearly labeled synthetic comparison of
   manual notes versus canonical tasks, and seek one short practitioner validation quote if
   available.
4. **AWS depth:** resolved. The public vertical slice now uses AgentCore Runtime, AgentCore
   Gateway, Bedrock Guardrails, Nova Lite, Step Functions, DynamoDB, S3, EventBridge, SQS, SNS,
   API Gateway, CloudFront, and CloudWatch/X-Ray.
5. **Bonus:** publish up to three concise builder.aws build-journey posts if time remains.

## Current verdict

The product is technically credible, differentiated, and publicly testable, but it is **not
submission-complete** until the repository is public and the required video exists. The next
best investment is presentation evidence—not more speculative features.
