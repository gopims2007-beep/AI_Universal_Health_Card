from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import (
    QRCodeRecord,
    PatientProfile,
    User,
    MedicalHistory,
    MedicalReport,
)
from app.core.config import settings
from app.services.storage import download_report as download_storage_report


router = APIRouter(tags=["Emergency QR Access"])


# =========================================================
# EMERGENCY QR PATIENT DETAILS
# =========================================================

@router.get("/emergency/{token}")
def emergency_view(
    token: str,
    db: Session = Depends(get_db),
):
    qr = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.qr_token == token,
            QRCodeRecord.revoked == False,
        )
        .first()
    )

    if not qr:
        raise HTTPException(
            status_code=404,
            detail="QR code is invalid or revoked",
        )

    patient = db.get(
        PatientProfile,
        qr.patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found",
        )

    user = db.get(
        User,
        patient.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Patient user not found",
        )

    history = (
        db.query(MedicalHistory)
        .filter(
            MedicalHistory.patient_id == patient.id
        )
        .first()
    )

    # =====================================================
    # MEDICAL REPORTS
    # =====================================================

    reports = (
        db.query(MedicalReport)
        .filter(
            MedicalReport.patient_id == patient.id
        )
        .order_by(
            MedicalReport.uploaded_at.desc()
        )
        .all()
    )

    report_list = []

    for report in reports:

        report_list.append(
            {
                "id": report.id,
                "report_type": report.report_type,
                "filename": report.original_filename,
                "mime_type": report.mime_type,
                "size_bytes": report.size_bytes,
                "uploaded_at": report.uploaded_at,
                "view_url": (
                    f"/emergency/{token}/report/"
                    f"{report.id}/view"
                ),
                "download_url": (
                    f"/emergency/{token}/report/"
                    f"{report.id}/download"
                ),
            }
        )

    # =====================================================
    # EMERGENCY RESPONSE
    # =====================================================

    return {
        "card_id": patient.card_id,

        "patient_name": user.full_name,

        "blood_group": patient.blood_group,

        "severe_allergies": (
            history.allergies
            if history
            else []
        ),

        "emergency_contact": {
            "name": patient.emergency_contact_name,
            "phone": patient.emergency_contact_phone,
            "relation": patient.emergency_contact_relation,
        },

        "medical_reports": report_list,

        "notice": (
            "Emergency read-only view. "
            "Verify identity and clinical information "
            "where possible."
        ),
    }


# =========================================================
# VIEW MEDICAL PDF THROUGH EMERGENCY QR
# =========================================================

@router.get(
    "/emergency/{token}/report/{report_id}/view"
)
def emergency_view_report(
    token: str,
    report_id: int,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # Validate QR
    # -----------------------------------------------------

    qr = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.qr_token == token,
            QRCodeRecord.revoked == False,
        )
        .first()
    )

    if not qr:
        raise HTTPException(
            status_code=404,
            detail="QR code is invalid or revoked",
        )

    # -----------------------------------------------------
    # Find report
    # -----------------------------------------------------

    report = (
        db.query(MedicalReport)
        .filter(
            MedicalReport.id == report_id,
            MedicalReport.patient_id == qr.patient_id,
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Medical report not found",
        )

    # -----------------------------------------------------
    # Physical file
    # -----------------------------------------------------

    try:
        file_data = download_storage_report(report.stored_filename)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Stored medical report file not found in Supabase Storage",
        )

    # -----------------------------------------------------
    # Browser view
    # -----------------------------------------------------

    return StreamingResponse(
        BytesIO(file_data),
        media_type=report.mime_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{report.original_filename}"'
            )
        },
    )


# =========================================================
# DOWNLOAD MEDICAL REPORT THROUGH EMERGENCY QR
# =========================================================

@router.get(
    "/emergency/{token}/report/{report_id}/download"
)
def emergency_download_report(
    token: str,
    report_id: int,
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # Validate QR
    # -----------------------------------------------------

    qr = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.qr_token == token,
            QRCodeRecord.revoked == False,
        )
        .first()
    )

    if not qr:
        raise HTTPException(
            status_code=404,
            detail="QR code is invalid or revoked",
        )

    # -----------------------------------------------------
    # Find report belonging to QR patient
    # -----------------------------------------------------

    report = (
        db.query(MedicalReport)
        .filter(
            MedicalReport.id == report_id,
            MedicalReport.patient_id == qr.patient_id,
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Medical report not found",
        )

    # -----------------------------------------------------
    # Physical file
    # -----------------------------------------------------

    try:
        file_data = download_storage_report(report.stored_filename)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Stored medical report file not found in Supabase Storage",
        )

    # -----------------------------------------------------
    # Force download
    # -----------------------------------------------------

    return StreamingResponse(
        BytesIO(file_data),
        media_type=report.mime_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{report.original_filename}"'
            )
        },
    )