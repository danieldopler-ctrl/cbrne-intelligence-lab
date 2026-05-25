from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_audit(
    db: Session,
    action: str,
    object_type: str,
    object_id: int | str,
    *,
    actor: str = "local_analyst",
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            metadata_json=metadata or {},
        )
    )
