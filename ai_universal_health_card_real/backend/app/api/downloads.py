from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import PatientProfile, MedicalHistory
from app.core.deps import require_roles
from app.services.healthcard import build_health_card_pdf
from app.services.qr import qr_png, emergency_url
from app.db.models import QRCodeRecord

router = APIRouter(prefix="/api/downloads", tags=["Downloads"])

@router.get("/health-card.pdf")
def health_card(user=Depends(require_roles("patient")), db: Session = Depends(get_db)):
    patient = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient.id).first()
    data = build_health_card_pdf(patient, user, history)
    return StreamingResponse(BytesIO(data), media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="digital-health-card.pdf"'})

@router.get("/qr.png")
def health_qr(user=Depends(require_roles("patient")), db: Session = Depends(get_db)):
    patient = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    row = db.query(QRCodeRecord).filter(QRCodeRecord.patient_id == patient.id, QRCodeRecord.revoked == False).first()
    if not row:
        raise HTTPException(404, "Generate QR code first")
    return StreamingResponse(BytesIO(qr_png(row.emergency_url)), media_type="image/png",
                             headers={"Content-Disposition": 'attachment; filename="health-card-qr.png"'})
