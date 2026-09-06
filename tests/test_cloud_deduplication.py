"""Tests for the post-model duplicate boundary in AgentCore Runtime."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


def load_deduplication() -> ModuleType:
    path = Path(__file__).parents[1] / "infra" / "cloud" / "agent" / "deduplication.py"
    spec = importlib.util.spec_from_file_location("cloud_deduplication", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DEDUPLICATION = load_deduplication()


@dataclass
class Issue:
    canonical_key: str
    title: str


def test_bilingual_reports_with_same_key_are_merged() -> None:
    issues = [
        Issue("room-807-electrical-burning-smell", "Burning smell near panel"),
        Issue(" ROOM-807-ELECTRICAL-BURNING-SMELL ", "رائحة احتراق قرب اللوحة"),
        Issue("room-412-two-towels", "Two towels"),
    ]

    unique, removed = DEDUPLICATION.deduplicate_issues(issues)

    assert [item.title for item in unique] == ["Burning smell near panel", "Two towels"]
    assert removed == 1


def test_empty_keys_are_rejected_from_canonical_set() -> None:
    unique, removed = DEDUPLICATION.deduplicate_issues([Issue(" ", "Invalid")])

    assert unique == []
    assert removed == 1
