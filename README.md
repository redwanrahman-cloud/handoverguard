# HandoverGuard

HandoverGuard is a policy-bound AI agent for hotel shift handovers. It turns noisy
operational notes into owned follow-up work, while holding safety, guest compensation,
payments, and external communications for explicit human approval.

This repository was created on 24 August 2026 for the Amazon **Agents for Humans**
Hackathon. It is a new project, not an extension of a previous competition entry.

## Why it exists

Hotel teams inherit unresolved maintenance issues, guest requests, housekeeping blockers,
and financial exceptions at every shift change. Ordinary summaries make the list shorter;
HandoverGuard performs the safe routine work and surfaces only decisions that need a person.

## Safety model

- Synthetic demonstration data only.
- Server-side approval gates cannot be bypassed by the language model.
- Safety, compensation, payment, and external-contact actions always require approval.
- Every state change is appended to a tamper-evident SHA-256 audit chain.
- The agent never marks an issue resolved without an explicit human action.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/uvicorn handoverguard.api:app --reload
```

The deterministic workflow and tests do not call a model. A live Strands cycle uses Amazon
Bedrock and is enabled only when AWS credentials are deliberately configured. Do not place
real guest, employee, or property data in the demo.

## AI-assisted development disclosure

Redwan Rahman directs the product, requirements, review, and submission. OpenAI Codex is
used as an AI coding assistant for implementation, testing, and documentation. All generated
work is reviewed in this repository, third-party dependencies remain under their own licenses,
and no pre-existing competition project code is incorporated. See
[`docs/AI_ASSISTANCE.md`](docs/AI_ASSISTANCE.md).

