from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    HTTPException,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import PatientProfile, MedicalReport
from app.core.deps import require_roles, get_current_user
from app.core.config import settings
from app.services.files import save_upload, extract_text
from app.services.ai_analysis import analyze_report


router = APIRouter(
    prefix="/api/reports",
    tags=["Medical Reports"],
)


# =========================================================
# HELPER — GET CURRENT PATIENT
# =========================================================

def get_patient(user, db: Session):
    patient = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found",
        )

    return patient


# =========================================================
# 1. UPLOAD MEDICAL REPORT
# =========================================================

@router.post("/upload")
async def upload_report(
    report_type: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_patient(user, db)

    # Maximum upload size
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Save physical file
    stored_filename, file_path, file_size = await save_upload(
        file,
        settings.upload_dir,
        max_bytes,
    )

    # Extract text from PDF / image
    extracted_text = extract_text(
        file_path,
        file.content_type,
    )

    # Create MySQL record
    report = MedicalReport(
        patient_id=patient.id,
        uploaded_by_id=user.id,
        report_type=report_type.strip()[:50],
        original_filename=file.filename,
        stored_filename=stored_filename,
        mime_type=file.content_type,
        size_bytes=file_size,
        extracted_text=(
            extracted_text[:500000]
            if extracted_text
            else None
        ),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "message": "Medical report uploaded successfully",
        "id": report.id,
        "patient_id": report.patient_id,
        "filename": report.original_filename,
        "report_type": report.report_type,
        "mime_type": report.mime_type,
        "size_bytes": report.size_bytes,
        "extracted_text_characters": (
            len(extracted_text)
            if extracted_text
            else 0
        ),
        "uploaded_at": report.uploaded_at,
    }


# =========================================================
# 2. LIST ALL MEDICAL REPORTS
# =========================================================

@router.get("")
def list_reports(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_patient(user, db)

    reports = (
        db.query(MedicalReport)
        .filter(MedicalReport.patient_id == patient.id)
        .order_by(MedicalReport.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": report.id,
            "patient_id": report.patient_id,
            "report_type": report.report_type,
            "filename": report.original_filename,
            "stored_filename": report.stored_filename,
            "mime_type": report.mime_type,
            "size_bytes": report.size_bytes,
            "uploaded_at": report.uploaded_at,
            "has_extracted_text": bool(
                report.extracted_text
            ),
        }
        for report in reports
    ]


# =========================================================
# 3. VIEW / DOWNLOAD MEDICAL REPORT
# =========================================================

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(MedicalReport, report_id)

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    patient = db.get(
        PatientProfile,
        report.patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found",
        )

    # Patient can access own report.
    # Doctor / hospital / admin can access according to role.
    if (
        user.id != patient.user_id
        and user.role not in {
            "doctor",
            "hospital",
            "admin",
        }
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )

    file_path = (
        Path(settings.upload_dir)
        / report.stored_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored report file not found",
        )

    return FileResponse(
        path=file_path,
        media_type=report.mime_type,
        filename=report.original_filename,
    )


# =========================================================
# 4. AI ANALYZE MEDICAL REPORT
# =========================================================

@router.post("/{report_id}/analyze")
def analyze(
    report_id: int,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_patient(user, db)

    report = db.get(
        MedicalReport,
        report_id,
    )

    if not report or report.patient_id != patient.id:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # Existing AI service
    return analyze_report(
        db,
        report,
    )


# =========================================================
# 5. GET ALL AI ANALYSES FOR REPORT
# =========================================================

@router.get("/{report_id}/analyses")
def analyses(
    report_id: int,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_patient(user, db)

    report = db.get(
        MedicalReport,
        report_id,
    )

    if not report or report.patient_id != patient.id:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report.analyses


# =========================================================
# 6. DELETE MEDICAL REPORT
# =========================================================

@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    patient = get_patient(user, db)

    # Find report
    report = db.get(
        MedicalReport,
        report_id,
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # Ownership check
    if report.patient_id != patient.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to delete this report",
        )

    # Physical file path
    file_path = (
        Path(settings.upload_dir)
        / report.stored_filename
    )

    # Delete database record.
    #
    # MedicalReport.analyses has:
    # cascade="all, delete-orphan"
    #
    # So related AI analyses will also be removed.
    db.delete(report)
    db.commit()

    # Delete physical file after DB deletion
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as error:
            print(
                "Warning: Database record deleted, "
                f"but physical file could not be deleted: {error}"
            )

    return {
        "message": "Medical report deleted successfully",
        "report_id": report_id,
    }