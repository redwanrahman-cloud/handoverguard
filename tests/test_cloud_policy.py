"""Adversarial checks for the AWS Lambda policy boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_policy() -> ModuleType:
    path = Path(__file__).parents[1] / "infra" / "cloud" / "lambda" / "policy_rules.py"
    spec = importlib.util.spec_from_file_location("cloud_policy_rules", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLICY = load_policy()


def issue(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "category": "maintenance",
        "priority": "medium",
        "action": "Create an internal engineering task",
        "financial_impact_sar": 0,
        "safety_sensitive": False,
    }
    return base | overrides


def test_routine_internal_task_does_not_require_approval() -> None:
    assert POLICY.approval_reasons(issue()) == []


def test_safety_flag_cannot_be_bypassed_by_model_wording() -> None:
    reasons = POLICY.approval_reasons(issue(safety_sensitive=True, action="Routine inspection"))
    assert "safety-sensitive issue" in reasons


def test_financial_threshold_requires_approval() -> None:
    reasons = POLICY.approval_reasons(issue(financial_impact_sar=100))
    assert "financial impact is SAR 100" in reasons


def test_external_guest_contact_requires_approval() -> None:
    reasons = POLICY.approval_reasons(issue(action="Email guest with room-change confirmation"))
    assert "external guest communication" in reasons


def test_refund_requires_approval_even_with_zero_estimate() -> None:
    reasons = POLICY.approval_reasons(issue(action="Issue a refund", financial_impact_sar=0))
    assert "guest compensation or refund" in reasons
