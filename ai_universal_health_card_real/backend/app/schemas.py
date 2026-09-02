from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    role: str = "patient"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ProfileUpdate(BaseModel):
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None

class HistoryIn(BaseModel):
    diseases: list[str] = []
    allergies: list[str] = []
    current_medications: list[str] = []
    surgery_history: list[str] = []
    vaccination_records: list[str] = []
    insurance_details: dict = {}
    notes: str | None = None

class HistoryOut(HistoryIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: datetime

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

class EmergencyDocumentIn(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    google_drive_url: str = Field(min_length=1, max_length=1000)
    description: str | None = None
    document_category: str | None = None

class EmergencyDocumentOut(EmergencyDocumentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    emergency_id: str
    created_at: datetime
    updated_at: datetime
