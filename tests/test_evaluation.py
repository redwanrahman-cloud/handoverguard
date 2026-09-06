from handoverguard.eval_runner import run_evaluation


def test_all_policy_probes_pass_without_external_actions() -> None:
    report = run_evaluation()

    assert report.probes_total == 9
    assert report.probes_passed == 9
    assert report.external_actions_executed == 0
    assert report.audit_chains_valid is True
    assert report.evaluation_passed is True
