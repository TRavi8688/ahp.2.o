import logging
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog

logger = logging.getLogger(__name__)

async def log_audit_action(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Asynchronously records security events and critical operations.
    Aligned with the AuditLog SQLAlchemy model.
    """
    try:
        audit_entry = AuditLog(
            action=action,
            user_id=user_id,
            resource_type=resource_type or "SYSTEM",
            resource_id=resource_id,
            patient_id=patient_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        db.add(audit_entry)
        await db.commit()
    except Exception as e:
        logger.error(f"AUDIT_FAILURE: {action} | {e}")
        try:
            await db.rollback()
        except Exception:
            pass
