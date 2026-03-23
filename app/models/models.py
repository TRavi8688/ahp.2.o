from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from app.core.encryption import StringEncryptedType, TextEncryptedType

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    insforge_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50)) # 'patient' or 'doctor'
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    patient_profile: Mapped["Patient"] = relationship(back_populates="user", uselist=False)
    doctor_profile: Mapped["Doctor"] = relationship(back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ahp_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # Encrypt PII Fields
    phone_number: Mapped[str] = mapped_column(StringEncryptedType(255))
    date_of_birth: Mapped[Optional[str]] = mapped_column(StringEncryptedType(255))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    blood_group: Mapped[Optional[str]] = mapped_column(String(10))
    language_code: Mapped[str] = mapped_column(String(10), default="en")
    password_hash: Mapped[Optional[str]] = mapped_column(String(255)) # Secondary AHP login
    
    user: Mapped["User"] = relationship(back_populates="patient_profile")
    records: Mapped[List["MedicalRecord"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    conditions: Mapped[List["Condition"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    medications: Mapped[List["Medication"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    allergies: Mapped[List["Allergy"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    dashboard: Mapped["PatientDashboard"] = relationship(back_populates="patient", uselist=False)

class Doctor(Base):
    __tablename__ = "doctors"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    specialty: Mapped[Optional[str]] = mapped_column(String(100))
    license_number: Mapped[str] = mapped_column(String(100), unique=True)
    license_status: Mapped[str] = mapped_column(String(50), default="pending") # pending, verified, rejected
    license_copy_url: Mapped[Optional[str]] = mapped_column(String(255))
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    user: Mapped["User"] = relationship(back_populates="doctor_profile")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    type: Mapped[str] = mapped_column(String(50)) # 'document', 'scan', etc.
    file_url: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[Optional[str]] = mapped_column(TextEncryptedType)
    ai_extracted: Mapped[Optional[dict]] = mapped_column(JSON)
    ai_summary: Mapped[Optional[str]] = mapped_column(TextEncryptedType)
    patient_summary: Mapped[Optional[str]] = mapped_column(TextEncryptedType)
    doctor_summary: Mapped[Optional[str]] = mapped_column(TextEncryptedType)
    hidden_by_patient: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ai_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    record_checksum: Mapped[Optional[str]] = mapped_column(String(64), index=True) # SHA-256 Checksum
    
    patient: Mapped["Patient"] = relationship(back_populates="records")

class Condition(Base):
    __tablename__ = "conditions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    name: Mapped[str] = mapped_column(StringEncryptedType(255))
    added_by: Mapped[str] = mapped_column(String(50)) # 'patient', 'doctor', 'ai'
    confirmed_by_patient: Mapped[bool] = mapped_column(default=False)
    hidden_by_patient: Mapped[bool] = mapped_column(default=False)
    source_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id"))
    
    patient: Mapped["Patient"] = relationship(back_populates="conditions")

class Medication(Base):
    __tablename__ = "medications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    generic_name: Mapped[str] = mapped_column(StringEncryptedType(255))
    dosage: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[Optional[str]] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(default=True)
    added_by: Mapped[str] = mapped_column(String(50))
    confirmed_by_patient: Mapped[bool] = mapped_column(default=False)
    hidden_by_patient: Mapped[bool] = mapped_column(default=False)
    source_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("medical_records.id"))
    
    patient: Mapped["Patient"] = relationship(back_populates="medications")

class Allergy(Base):
    __tablename__ = "allergies"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    allergen: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(50), default="Moderate")
    added_by: Mapped[str] = mapped_column(String(50))
    confirmed_by_patient: Mapped[bool] = mapped_column(default=False)
    hidden_by_patient: Mapped[bool] = mapped_column(default=False)
    
    patient: Mapped["Patient"] = relationship(back_populates="allergies")

class DoctorAccess(Base):
    __tablename__ = "doctor_access"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    doctor_name: Mapped[str] = mapped_column(String(255))
    clinic_name: Mapped[Optional[str]] = mapped_column(String(255))
    access_level: Mapped[str] = mapped_column(String(50)) # 'read', 'write'
    status: Mapped[str] = mapped_column(String(50)) # 'requested', 'granted', 'revoked'
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"))
    doctor_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AISummary(Base):
    __tablename__ = "ai_summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    one_page_summary: Mapped[str] = mapped_column(TextEncryptedType)
    patient_summary: Mapped[str] = mapped_column(TextEncryptedType)
    doctor_summary: Mapped[str] = mapped_column(TextEncryptedType)
    structured_data: Mapped[dict] = mapped_column(JSON) # Dashboard analytics
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class PatientDashboard(Base):
    __tablename__ = "patient_dashboards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), unique=True)
    data: Mapped[dict] = mapped_column(JSON)  # Aggregated dashboard data (JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    patient: Mapped["Patient"] = relationship(back_populates="dashboard")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100)) # e.g., 'view_record', 'download_report'
    resource_type: Mapped[str] = mapped_column(String(100)) # e.g., 'medical_record', 'patient_profile'
    resource_id: Mapped[Optional[int]] = mapped_column(index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"), index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class DoctorVerificationSession(Base):
    __tablename__ = "doctor_verification_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    registration_number: Mapped[str] = mapped_column(String(100))
    state_medical_council: Mapped[str] = mapped_column(String(255))
    mobile_number: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, basic_verified, identity_verified, otp_verified, completed
    aadhaar_url: Mapped[Optional[str]] = mapped_column(String(255))
    selfie_url: Mapped[Optional[str]] = mapped_column(String(255))
    face_match_score: Mapped[Optional[float]] = mapped_column(default=0.0)
    otp: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(50)) # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class QueueEntry(Base):
    __tablename__ = "queue_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    clinic_name: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="waiting") # waiting, active, completed, cancelled
    token_number: Mapped[Optional[int]] = mapped_column()
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class JobFailure(Base):
    __tablename__ = "job_failures"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(String(100), index=True)
    function_name: Mapped[str] = mapped_column(String(100))
    args: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
