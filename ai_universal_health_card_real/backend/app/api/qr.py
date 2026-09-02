from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import PatientProfile, QRCodeRecord
from app.core.deps import require_roles
from app.services.qr import make_qr_token, emergency_url, qr_png


router = APIRouter(
    prefix="/api/qr",
    tags=["QR Code"]
)


# =========================================================
# GENERATE QR
# =========================================================

@router.post("/generate")
def generate_qr(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    # Find patient profile
    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    # Find existing active QR
    active = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.patient_id == patient.id,
            QRCodeRecord.revoked == False
        )
        .first()
    )

    # -----------------------------------------------------
    # IMPORTANT FIX
    # Rebuild URL using current PUBLIC_BASE_URL
    # instead of returning old stored URL.
    # -----------------------------------------------------

    if active:
        current_url = emergency_url(active.qr_token)

        active.emergency_url = current_url

        db.commit()
        db.refresh(active)

        return {
            "token": active.qr_token,
            "emergency_url": current_url
        }

    # -----------------------------------------------------
    # Create NEW QR
    # -----------------------------------------------------

    token = make_qr_token(patient.id)

    current_url = emergency_url(token)

    row = QRCodeRecord(
        patient_id=patient.id,
        qr_token=token,
        emergency_url=current_url,
        revoked=False
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "token": row.qr_token,
        "emergency_url": row.emergency_url
    }


# =========================================================
# QR PNG
# =========================================================

@router.get("/png")
def qr_png_endpoint(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    row = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.patient_id == patient.id,
            QRCodeRecord.revoked == False
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Generate QR code first"
        )

    # Always use current URL
    row.emergency_url = emergency_url(row.qr_token)

    db.commit()
    db.refresh(row)

    return StreamingResponse(
        BytesIO(qr_png(row.emergency_url)),
        media_type="image/png",
        headers={
            "Content-Disposition":
                "attachment; filename=health-card-qr.png"
        }
    )


# =========================================================
# REVOKE QR
# =========================================================

@router.post("/revoke")
def revoke_qr(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    rows = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.patient_id == patient.id,
            QRCodeRecord.revoked == False
        )
        .all()
    )

    if not rows:
        return {
            "message": "No active QR codes found"
        }

    for row in rows:
        row.revoked = True

    db.commit()

    return {
        "message": "Active QR codes revoked"
    }