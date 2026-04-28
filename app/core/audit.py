import hmac
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.models import AuditLog
from app.core.config import settings
from app.core.logging import logger

def calculate_log_signature(data: Dict[str, Any], prev_hash: str = "") -> str:
    """
    Cryptographic signing of audit logs to ensure immutability.
    Uses HMAC-SHA256 with the ENCRYPTION_KEY as the secret.
    """
    serialized = json.dumps(data, sort_keys=True, default=str)
    message = f"{prev_hash}|{serialized}"
    return hmac.new(
        settings.ENCRYPTION_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

async def log_audit_action(
    db: AsyncSession, # For backward compatibility (not used)
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = "SYSTEM",
    resource_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Immutable Audit Logging with Chain of Trust.
    Every log entry is signed and chained to the previous entry's hash.
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Get the hash of the previous log for chaining
            stmt = select(AuditLog.signature).order_by(desc(AuditLog.id)).limit(1)
            result = await session.execute(stmt)
            prev_hash = result.scalar() or "ROOT_GENESIS"

            # 2. Prepare log data
            log_data = {
                "action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "patient_id": patient_id,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat()
            }

            # 3. Calculate Signature (Immutability Check)
            signature = calculate_log_signature(log_data, prev_hash)

            audit_entry = AuditLog(
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                signature=signature,
                prev_hash=prev_hash
            )
            
            session.add(audit_entry)
            await session.commit()
            
        except Exception as e:
            logger.error("AUDIT_LOG_CHAIN_FAILURE", action=action, error=str(e))
