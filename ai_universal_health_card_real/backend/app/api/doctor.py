from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import PatientProfile, User, MedicalHistory
from app.core.deps import require_roles

router = APIRouter(prefix="/api/doctor", tags=["Doctor / Hospital"])

@router.get("/search")
def search_patient(card_id: str, user=Depends(require_roles("doctor", "hospital", "admin")), db: Session = Depends(get_db)):
    patient = db.query(PatientProfile).filter(PatientProfile.card_id == card_id).first()
    if not patient:
        return {"found": False}
    owner = db.get(User, patient.user_id)
    return {
        "found": True,
        "patient": {"card_id": patient.card_id, "name": owner.full_name, "blood_group": patient.blood_group},
        "message": "Further medical-record access should be protected by explicit patient consent.",
    }
