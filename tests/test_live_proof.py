import json

import pytest

from handoverguard.live_proof import main, run_live_proof
from handoverguard.service import HandoverService


def fake_agent_runner(service: HandoverService, shift_id: str) -> str:
    service.process_shift(shift_id, actor="strands-test-agent")
    return "Created safe internal tasks and held sensitive actions for human approval."


def test_live_proof_verifies_post_agent_policy_state() -> None:
    proof = run_live_proof(fake_agent_runner)

    assert proof.framework == "Strands Agents"
    assert proof.model_provider == "Amazon Bedrock"
    assert proof.issues_ingested == 5
    assert proof.duplicates_linked == 1
    assert proof.safe_internal_tasks_created == 2
    assert proof.human_approvals_pending == 2
    assert proof.external_actions_executed == 0
    assert proof.audit_chain_valid is True
    assert proof.safety_invariants_passed is True


def test_live_proof_cli_can_emit_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "handoverguard.live_proof.run_live_proof",
        lambda: run_live_proof(fake_agent_runner),
    )
    monkeypatch.setattr("sys.argv", ["handoverguard-live-proof", "--json"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["framework"] == "Strands Agents"
    assert payload["safety_invariants_passed"] is True
