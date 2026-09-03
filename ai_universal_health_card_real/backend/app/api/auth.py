from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, PatientProfile, OneTimeToken, AuditLog
from app.schemas import (
    RegisterIn,
    LoginIn,
    TokenOut,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    random_token,
    token_hash,
)
from app.services.email import send_email


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# ============================================================
# REGISTER
# ============================================================

@router.post("/register", response_model=TokenOut)
def register(
    data: RegisterIn,
    request: Request,
    db: Session = Depends(get_db)
):

    # Only allowed roles
    if data.role not in {"patient", "doctor", "hospital", "admin"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    # Only patient can self-register
    if data.role != "patient":
        raise HTTPException(
            status_code=403,
            detail="Only patient self-registration is enabled"
        )

    # Clean email
    email = data.email.strip().lower()

    # Check existing user
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # Create User
    # --------------------------------------------------------

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        role="patient",
        full_name=data.full_name.strip(),
        phone=data.phone,
    )

    db.add(user)
    db.flush()

    # --------------------------------------------------------
    # Create Patient Profile
    # --------------------------------------------------------

    card_id = f"AHC-{user.id:010d}"

    patient = PatientProfile(
        user_id=user.id,
        card_id=card_id
    )

    db.add(patient)

    # --------------------------------------------------------
    # Email verification token
    # --------------------------------------------------------

    raw_token = random_token()

    verification_token = OneTimeToken(
        user_id=user.id,
        token_hash=token_hash(raw_token),
        purpose="email_verify",
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )

    db.add(verification_token)

    # --------------------------------------------------------
    # Audit log
    # --------------------------------------------------------

    audit = AuditLog(
        user_id=user.id,
        action="register",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
    )

    db.add(audit)

    # Save everything
    db.commit()

    # --------------------------------------------------------
    # Send verification email
    # --------------------------------------------------------

    verify_link = (
        f"/api/auth/verify-email?token={raw_token}"
    )

    try:
        send_email(
            email,
            "Verify your AI Universal Health Card account",
            (
                "Please verify your account using this link:\n\n"
                f"{verify_link}"
            ),
        )
    except Exception:
        # Registration should not fail only because email service
        # is unavailable.
        pass

    # --------------------------------------------------------
    # Return tokens
    # --------------------------------------------------------

    return TokenOut(
        access_token=create_access_token(
            user.id,
            user.role
        ),
        refresh_token=create_refresh_token(
            user.id
        ),
    )


# ============================================================
# VERIFY EMAIL
# ============================================================

@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):

    row = (
        db.query(OneTimeToken)
        .filter(
            OneTimeToken.token_hash == token_hash(token),
            OneTimeToken.purpose == "email_verify",
            OneTimeToken.used == False,
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    if row.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification token expired"
        )

    user = db.get(User, row.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.is_email_verified = True
    row.used = True

    db.commit()

    return {
        "message": "Email verified successfully"
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login", response_model=TokenOut)
def login(
    data: LoginIn,
    request: Request,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Normalize email
    # --------------------------------------------------------

    email = data.email.strip().lower()

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # IMPORTANT:
    # Do not reveal whether email or password is wrong.
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_valid = verify_password(
        data.password,
        user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # --------------------------------------------------------
    # Audit log
    # --------------------------------------------------------

    db.add(
        AuditLog(
            user_id=user.id,
            action="login",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
        )
    )

    db.commit()

    # --------------------------------------------------------
    # Generate JWT tokens
    # --------------------------------------------------------

    return TokenOut(
        access_token=create_access_token(
            user.id,
            user.role
        ),
        refresh_token=create_refresh_token(
            user.id
        ),
    )


# ============================================================
# REFRESH TOKEN
# ============================================================

@router.post("/refresh", response_model=TokenOut)
def refresh(
    refresh_token: str,
    db: Session = Depends(get_db)
):

    try:

        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = int(payload["sub"])

        user = db.get(User, user_id)

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    return TokenOut(
        access_token=create_access_token(
            user.id,
            user.role
        ),
        refresh_token=create_refresh_token(
            user.id
        ),
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post("/forgot-password")
def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):

    email = data.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Do not reveal whether account exists
    if user:

        raw_token = random_token()

        db.add(
            OneTimeToken(
                user_id=user.id,
                token_hash=token_hash(raw_token),
                purpose="password_reset",
                expires_at=datetime.utcnow()
                + timedelta(minutes=30),
            )
        )

        db.commit()

        try:
            send_email(
                user.email,
                "AI Universal Health Card password reset",
                (
                    "Use this password reset token "
                    "within 30 minutes:\n\n"
                    f"{raw_token}"
                ),
            )
        except Exception:
            pass

    return {
        "message": (
            "If the account exists, "
            "password-reset instructions have been sent."
        )
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post("/reset-password")
def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):

    row = (
        db.query(OneTimeToken)
        .filter(
            OneTimeToken.token_hash == token_hash(data.token),
            OneTimeToken.purpose == "password_reset",
            OneTimeToken.used == False,
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Invalid password reset token"
        )

    if row.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Password reset token expired"
        )

    user = db.get(User, row.user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Hash new password
    user.password_hash = hash_password(
        data.new_password
    )

    row.used = True

    db.commit()

    return {
        "message": "Password reset successfully"
    }
