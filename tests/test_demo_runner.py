import json

import pytest

from handoverguard.demo_runner import main, run_demo_proof


def test_deterministic_demo_proves_safety_invariants() -> None:
    proof = run_demo_proof()

    assert proof.scenario == "SHIFT-NIGHT-2408"
    assert proof.data_classification == "synthetic-only"
    assert proof.issues_ingested == 5
    assert proof.canonical_issues == 4
    assert proof.duplicates_linked == 1
    assert proof.safe_internal_tasks_created == 2
    assert proof.human_approvals_pending == 2
    assert proof.critical_issues == 1
    assert proof.external_actions_executed == 0
    assert proof.audit_events == 10
    assert proof.audit_chain_valid is True
    assert proof.safety_invariants_passed is True


def test_demo_cli_can_emit_machine_readable_proof(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["handoverguard-demo", "--json"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["safety_invariants_passed"] is True
    assert payload["external_actions_executed"] == 0
