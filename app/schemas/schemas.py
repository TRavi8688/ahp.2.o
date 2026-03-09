from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Auth Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None # email
    role: Optional[str] = None

class OTPRequest(BaseModel):
    identifier: str = Field(..., description="Phone number or Email")
    country_code: str = "+91"

class OTPVerify(BaseModel):
    identifier: str
    otp: str

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Patient Schemas
class PatientBase(BaseModel):
    ahp_id: str
    phone_number: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    language_code: str = "en"

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    date_of_birth: str
    gender: str
    blood_group: str
    language_code: str = "en"
    conditions: List[str] = []
    medications: List[str] = []

class PatientResponse(PatientBase):
    id: int
    class Config:
        from_attributes = True

# Medical Record Schemas
class MedicalRecordBase(BaseModel):
    type: str
    file_url: str

class MedicalRecordResponse(MedicalRecordBase):
    id: int
    ai_summary: Optional[str] = None
    patient_summary: Optional[str] = None
    doctor_summary: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Doctor Schemas
class DoctorBase(BaseModel):
    specialty: str
    license_number: str

class DoctorResponse(DoctorBase):
    id: int
    license_status: str
    class Config:
        from_attributes = True

# Analytics / Dashboard
class DashboardMetrics(BaseModel):
    health_score: Optional[int] = None
    alerts: List[dict] = []
    conditions: List[str] = []
    medications: List[dict] = []
