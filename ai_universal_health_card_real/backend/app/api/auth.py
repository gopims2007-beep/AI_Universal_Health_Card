from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, PatientProfile, OneTimeToken, AuditLog
from app.schemas import RegisterIn, LoginIn, TokenOut, PasswordResetRequest, PasswordResetConfirm
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, random_token, token_hash
from app.services.email import send_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if data.role not in {"patient", "doctor", "hospital", "admin"}:
        raise HTTPException(400, "Invalid role")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    if data.role != "patient":
        # Public self-registration is limited to patients.
        raise HTTPException(403, "Only patient self-registration is enabled")

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role="patient",
        full_name=data.full_name.strip(),
        phone=data.phone,
    )
    db.add(user)
    db.flush()

    # Deterministic card ID derived from immutable internal user ID.
    card_id = f"AHC-{user.id:010d}"
    patient = PatientProfile(user_id=user.id, card_id=card_id)
    db.add(patient)

    raw = random_token()
    db.add(OneTimeToken(
        user_id=user.id,
        token_hash=token_hash(raw),
        purpose="email_verify",
        expires_at=datetime.utcnow() + timedelta(hours=24),
    ))
    db.add(AuditLog(user_id=user.id, action="register", resource_type="user", resource_id=str(user.id), ip_address=request.client.host if request.client else None))
    db.commit()

    verify_link = f"/api/auth/verify-email?token={raw}"
    send_email(data.email, "Verify your AI Universal Health Card account",
               f"Open this verification URL from your server: {verify_link}")

    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    row = db.query(OneTimeToken).filter(OneTimeToken.token_hash == token_hash(token), OneTimeToken.purpose == "email_verify", OneTimeToken.used == False).first()
    if not row or row.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invalid or expired verification token")
    user = db.get(User, row.user_id)
    user.is_email_verified = True
    row.used = True
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is inactive")
    db.add(AuditLog(user_id=user.id, action="login", resource_type="user", resource_id=str(user.id), ip_address=request.client.host if request.client else None))
    db.commit()
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id))

@router.post("/refresh", response_model=TokenOut)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError()
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(401, "Invalid or expired refresh token")
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid refresh token")
    return TokenOut(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id))

@router.post("/forgot-password")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    # Avoid leaking account existence.
    if user:
        raw = random_token()
        db.add(OneTimeToken(
            user_id=user.id,
            token_hash=token_hash(raw),
            purpose="password_reset",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        ))
        db.commit()
        send_email(user.email, "AI Universal Health Card password reset",
                   f"Use this password reset token within 30 minutes: {raw}")
    return {"message": "If the account exists, password-reset instructions have been sent."}

@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    row = db.query(OneTimeToken).filter(OneTimeToken.token_hash == token_hash(data.token), OneTimeToken.purpose == "password_reset", OneTimeToken.used == False).first()
    if not row or row.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invalid or expired reset token")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(data.new_password)
    row.used = True
    db.commit()
    return {"message": "Password reset successfully"}
