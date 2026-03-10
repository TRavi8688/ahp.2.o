import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import User, Patient, PatientDashboard
from app.services.dashboard_service import DashboardService
from app.core.config import settings
import time

def verify_dashboard():
    # 1. Setup DB Session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 2. Check for existence of patient #1 (Mock)
        patient = db.query(Patient).filter(Patient.id == 1).first()
        if not patient:
            print("Creating mock patient...")
            user = User(email="test@example.com", first_name="Test", last_name="User", role="patient")
            db.add(user)
            db.commit()
            db.refresh(user)
            patient = Patient(user_id=user.id, ahp_id="AHP-TEST", blood_group="O+", phone_number="1234567890")
            db.add(patient)
            db.commit()
            db.refresh(patient)

        service = DashboardService(db)

        # 3. Test Aggregation
        print("Testing aggregation...")
        start_time = time.time()
        data = service.aggregate_dashboard_data(patient.id)
        print(f"Aggregation took: {time.time() - start_time:.4f}s")
        print(f"Data: {data.get('profile', {})}")

        # 4. Test Redis Retrieval (should be fast)
        print("Testing Redis retrieval...")
        start_time = time.time()
        cached_data = service.get_dashboard(patient.id)
        elapsed = time.time() - start_time
        print(f"Redis retrieval took: {elapsed:.4f}s")
        
        if elapsed < 0.01:
            print("✅ SUCCESS: Sub-10ms retrieval confirmed.")
        else:
            print("⚠️ WARNING: Retrieval slower than expected.")

    finally:
        db.close()

if __name__ == "__main__":
    verify_dashboard()
