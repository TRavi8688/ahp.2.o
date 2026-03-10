import json
from datetime import datetime
from typing import Optional, Dict, Any
import redis.asyncio as redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import PatientDashboard, Patient, MedicalRecord, Condition, Medication, Allergy, AISummary
from app.core.config import settings
from app.core.logging import logger

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get_dashboard(self, patient_id: int) -> Dict[str, Any]:
        """Get dashboard with multi-layer caching (Redis -> PG Precomputed -> Aggregate Fallback)."""
        cache_key = f"dashboard:{patient_id}"
        
        # 1. Redis Tier
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis error: {e}")

        # 2. Precomputed PG Tier
        stmt = select(PatientDashboard).where(PatientDashboard.patient_id == patient_id)
        result = await self.db.execute(stmt)
        db_dashboard = result.scalar_one_or_none()
        
        if db_dashboard:
            # Re-cache in Redis
            try:
                await self.redis_client.setex(cache_key, 3600, json.dumps(db_dashboard.data))
            except Exception:
                pass
            return db_dashboard.data

        # 3. Aggregate Fallback
        return await self.aggregate_dashboard_data(patient_id)

    async def aggregate_dashboard_data(self, patient_id: int) -> Dict[str, Any]:
        """Compute dashboard from raw medical history data."""
        # Fetch Patient & User (Joined)
        stmt = select(Patient).where(Patient.id == patient_id).join(Patient.user)
        result = await self.db.execute(stmt)
        patient = result.scalar_one_or_none()
        
        if not patient:
            return {"error": "Patient not found"}
        
        user = patient.user
        
        # Fetch Medical Data Components in parallel if possible, but SQLAlchemy sessions aren't thread-safe for parallel ops on one session.
        # We'll do them sequentially but asynchoronously.
        
        # Latest Records
        records_stmt = select(MedicalRecord).where(MedicalRecord.patient_id == patient_id).order_by(MedicalRecord.created_at.desc()).limit(5)
        records = (await self.db.execute(records_stmt)).scalars().all()
        
        # Active Conditions
        conditions_stmt = select(Condition).where(Condition.patient_id == patient_id, Condition.hidden_by_patient == False)
        conditions = (await self.db.execute(conditions_stmt)).scalars().all()
        
        # Medications
        meds_stmt = select(Medication).where(Medication.patient_id == patient_id, Medication.active == True)
        meds = (await self.db.execute(meds_stmt)).scalars().all()
        
        # Allergies
        allergies_stmt = select(Allergy).where(Allergy.patient_id == patient_id)
        allergies = (await self.db.execute(allergies_stmt)).scalars().all()
        
        # Latest AI Analysis
        ai_stmt = select(AISummary).where(AISummary.patient_id == patient_id).order_by(AISummary.created_at.desc())
        latest_ai = (await self.db.execute(ai_stmt)).scalars().first()

        dashboard_data = {
            "profile": {
                "full_name": f"{user.first_name} {user.last_name}",
                "ahp_id": patient.ahp_id,
                "blood_group": patient.blood_group,
                "phone": patient.phone_number,
                "dob": patient.date_of_birth,
                "gender": patient.gender
            },
            "latest_records": [
                {
                    "id": r.id,
                    "type": r.type,
                    "summary": r.patient_summary or r.ai_summary or "Processing...",
                    "date": r.created_at.isoformat()
                } for r in records
            ],
            "health_summary": latest_ai.structured_data if latest_ai else {},
            "active_conditions": [{"name": c.name} for c in conditions],
            "current_medications": [{"name": m.generic_name, "dosage": m.dosage} for m in meds],
            "allergies": [{"allergen": a.allergen, "severity": a.severity} for a in allergies],
            "updated_at": datetime.now().isoformat()
        }

        # Upsert Precomputed Table
        upsert_stmt = select(PatientDashboard).where(PatientDashboard.patient_id == patient_id)
        db_dash_res = await self.db.execute(upsert_stmt)
        db_dash = db_dash_res.scalar_one_or_none()
        
        if db_dash:
            db_dash.data = dashboard_data
            db_dash.updated_at = datetime.now()
        else:
            db_dash = PatientDashboard(patient_id=patient_id, data=dashboard_data)
            self.db.add(db_dash)
        
        await self.db.commit()

        # Update Redis Cache
        try:
            cache_key = f"dashboard:{patient_id}"
            await self.redis_client.setex(cache_key, 3600, json.dumps(dashboard_data))
        except Exception:
            pass

        return dashboard_data
