"""Privacy-safe synthetic data for the competition demo."""

from datetime import UTC, datetime

from .domain import ActionKind, Category, Department, IssueCreate, Priority

DEMO_SHIFT_ID = "SHIFT-NIGHT-2408"


def demo_issues() -> list[IssueCreate]:
    reported = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    return [
        IssueCreate(
            source_ref="DEMO-NOTE-001",
            property_id="DEMO-RIYADH-01",
            shift_id=DEMO_SHIFT_ID,
            department=Department.MAINTENANCE,
            category=Category.MAINTENANCE,
            summary="Air conditioner is noisy in ROOM-412",
            details="Synthetic guest reported intermittent fan noise; cooling still works.",
            room_label="ROOM-412",
            reported_at=reported,
        ),
        IssueCreate(
            source_ref="DEMO-NOTE-002",
            property_id="DEMO-RIYADH-01",
            shift_id=DEMO_SHIFT_ID,
            department=Department.MAINTENANCE,
            category=Category.MAINTENANCE,
            summary="Air conditioner is noisy in ROOM-412",
            details="Duplicate synthetic note copied from the front-desk handover.",
            room_label="ROOM-412",
            reported_at=reported,
        ),
        IssueCreate(
            source_ref="DEMO-NOTE-003",
            property_id="DEMO-RIYADH-01",
            shift_id=DEMO_SHIFT_ID,
            department=Department.FRONT_DESK,
            category=Category.GUEST_REQUEST,
            summary="Prepare late-arrival welcome pack for ROOM-208",
            details="Synthetic arrival is expected after midnight; prepare the standard pack.",
            room_label="ROOM-208",
            priority=Priority.HIGH,
            reported_at=reported,
        ),
        IssueCreate(
            source_ref="DEMO-NOTE-004",
            property_id="DEMO-RIYADH-01",
            shift_id=DEMO_SHIFT_ID,
            department=Department.FRONT_DESK,
            category=Category.GUEST_REQUEST,
            summary="Review compensation request for ROOM-305",
            details="Synthetic guest requests SAR 250 after a delayed room change.",
            room_label="ROOM-305",
            requested_action=ActionKind.AUTHORIZE_COMPENSATION,
            financial_impact_sar=250,
            priority=Priority.HIGH,
            reported_at=reported,
        ),
        IssueCreate(
            source_ref="DEMO-NOTE-005",
            property_id="DEMO-RIYADH-01",
            shift_id=DEMO_SHIFT_ID,
            department=Department.SECURITY,
            category=Category.SAFETY,
            summary="Inspect synthetic fire-door obstruction on level two",
            details="Training scenario: a linen trolley may be blocking a marked fire door.",
            requested_action=ActionKind.ESCALATE_SAFETY,
            safety_sensitive=True,
            priority=Priority.CRITICAL,
            reported_at=reported,
        ),
    ]
