from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'patient' or 'doctor'
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ahp_id = Column(String, unique=True, index=True)
    phone_number = Column(String)
    date_of_birth = Column(String)
    gender = Column(String)
    blood_group = Column(String)
    language_code = Column(String, default="en")
    password_hash = Column(String, nullable=True) # Secondary AHP login
    
    user = relationship("User", back_populates="patient_profile")
    records = relationship("MedicalRecord", back_populates="patient")
    conditions = relationship("Condition", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    allergies = relationship("Allergy", back_populates="patient")

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    specialty = Column(String)
    license_number = Column(String, unique=True)
    license_status = Column(String, default="pending") # pending, verified, rejected
    license_copy_url = Column(String)
    verification_notes = Column(Text)
    
    user = relationship("User", back_populates="doctor_profile")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    type = Column(String) # 'document', 'scan', etc.
    file_url = Column(String)
    raw_text = Column(Text, nullable=True)
    ai_extracted = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    patient_summary = Column(Text, nullable=True)
    doctor_summary = Column(Text, nullable=True)
    hidden_by_patient = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ai_processed_at = Column(DateTime, nullable=True)
    
    patient = relationship("Patient", back_populates="records")

class Condition(Base):
    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    name = Column(String)
    added_by = Column(String) # 'patient', 'doctor', 'ai'
    confirmed_by_patient = Column(Boolean, default=False)
    hidden_by_patient = Column(Boolean, default=False)
    source_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    
    patient = relationship("Patient", back_populates="conditions")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    generic_name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    active = Column(Boolean, default=True)
    added_by = Column(String)
    confirmed_by_patient = Column(Boolean, default=False)
    hidden_by_patient = Column(Boolean, default=False)
    source_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    
    patient = relationship("Patient", back_populates="medications")

class Allergy(Base):
    __tablename__ = "allergies"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    allergen = Column(String)
    severity = Column(String, default="Moderate")
    added_by = Column(String)
    confirmed_by_patient = Column(Boolean, default=False)
    hidden_by_patient = Column(Boolean, default=False)
    
    patient = relationship("Patient", back_populates="allergies")

class DoctorAccess(Base):
    __tablename__ = "doctor_access"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_user_id = Column(Integer, ForeignKey("users.id"))
    doctor_name = Column(String)
    clinic_name = Column(String)
    access_level = Column(String) # 'read', 'write'
    status = Column(String) # 'requested', 'granted', 'revoked'
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    doctor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String)
    title = Column(String)
    body = Column(String)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AISummary(Base):
    __tablename__ = "ai_summaries"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    one_page_summary = Column(Text)
    patient_summary = Column(Text)
    doctor_summary = Column(Text)
    structured_data = Column(JSON) # Dashboard analytics
    created_at = Column(DateTime, default=datetime.utcnow)
