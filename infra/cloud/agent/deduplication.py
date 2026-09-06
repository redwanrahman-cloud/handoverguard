"""Deterministic canonical-key deduplication for Nova extraction results."""

from __future__ import annotations

from typing import Protocol


class CanonicalIssue(Protocol):
    """Minimum shape required by the deduplication boundary."""

    canonical_key: str


def deduplicate_issues[IssueT: CanonicalIssue](
    issues: list[IssueT],
) -> tuple[list[IssueT], int]:
    """Keep the first issue for each normalized, model-supplied canonical key."""
    unique: list[IssueT] = []
    seen: set[str] = set()
    for issue in issues:
        key = "-".join(issue.canonical_key.casefold().strip().split())
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique, len(issues) - len(unique)
