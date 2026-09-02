from datetime import datetime
from sqlalchemy import String, Text, Date, DateTime, Boolean, ForeignKey, Integer, Float, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="patient", index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reports = relationship("MedicalReport", back_populates="uploaded_by")

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    card_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(10), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emergency_contact_relation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="patient_profile")
    history = relationship("MedicalHistory", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("MedicalReport", back_populates="patient", cascade="all, delete-orphan")
    qr_codes = relationship("QRCodeRecord", back_populates="patient", cascade="all, delete-orphan")
    emergency_documents = relationship("EmergencyDocument", back_populates="patient", cascade="all, delete-orphan")

class MedicalHistory(Base):
    __tablename__ = "medical_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    diseases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    allergies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    current_medications: Mapped[list | None] = mapped_column(JSON, nullable=True)
    surgery_history: Mapped[list | None] = mapped_column(JSON, nullable=True)
    vaccination_records: Mapped[list | None] = mapped_column(JSON, nullable=True)
    insurance_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="history")

class MedicalReport(Base):
    __tablename__ = "medical_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    report_type: Mapped[str] = mapped_column(String(50))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="reports")
    uploaded_by = relationship("User", back_populates="reports")
    analyses = relationship("AIAnalysis", back_populates="report", cascade="all, delete-orphan")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("medical_reports.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30))
    summary: Mapped[str] = mapped_column(Text)
    key_insights: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("MedicalReport", back_populates="analyses")

class QRCodeRecord(Base):
    __tablename__ = "qr_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    qr_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    emergency_url: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    patient = relationship("PatientProfile", back_populates="qr_codes")

class EmergencyDocument(Base):
    __tablename__ = "emergency_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    emergency_id: Mapped[str] = mapped_column(String(100), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    google_drive_url: Mapped[str] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="emergency_documents")

class ConsentToken(Base):
    __tablename__ = "consent_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"))
    doctor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OneTimeToken(Base):
    __tablename__ = "one_time_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
