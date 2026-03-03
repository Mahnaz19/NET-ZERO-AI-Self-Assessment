from typing import Any, Dict

from sqlalchemy.orm import Session


def orm_to_dict(instance: Any) -> Dict[str, Any]:
    """
    Convert a simple SQLAlchemy ORM instance into a plain dict.

    This is useful where we want JSON-safe data without tightly coupling
    to Pydantic models.
    """
    if instance is None:
        return {}

    data: Dict[str, Any] = {}
    for key in instance.__mapper__.c.keys():
        data[key] = getattr(instance, key)
    return data


def commit_and_refresh(db: Session, instance: Any) -> Any:
    """
    Helper to commit a session and refresh a specific instance.
    """
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance

