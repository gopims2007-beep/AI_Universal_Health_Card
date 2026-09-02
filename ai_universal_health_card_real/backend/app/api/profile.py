from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import PatientProfile, MedicalHistory
from app.schemas import ProfileUpdate, HistoryIn, HistoryOut
from app.core.deps import require_roles


router = APIRouter(
    prefix="/api/patient",
    tags=["Patient Profile"]
)


# --------------------------------------------------
# GET PATIENT PROFILE
# --------------------------------------------------
@router.get("/profile")
def get_profile(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    p = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
        },
        "profile": p,
    }


# --------------------------------------------------
# UPDATE PATIENT PROFILE
# --------------------------------------------------
@router.put("/profile")
def update_profile(
    data: ProfileUpdate,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    p = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(p, key, value)

    # Automatically calculate BMI
    if p.height_cm and p.weight_kg:
        p.bmi = round(
            p.weight_kg / ((p.height_cm / 100) ** 2),
            2
        )

    db.commit()
    db.refresh(p)

    return p


# --------------------------------------------------
# GET MEDICAL HISTORY
# --------------------------------------------------
@router.get(
    "/history",
    response_model=HistoryOut | None
)
def get_history(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    p = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    history = (
        db.query(MedicalHistory)
        .filter(MedicalHistory.patient_id == p.id)
        .first()
    )

    return history


# --------------------------------------------------
# UPDATE MEDICAL HISTORY
# --------------------------------------------------
@router.put(
    "/history",
    response_model=HistoryOut
)
def update_history(
    data: HistoryIn,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    p = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    h = (
        db.query(MedicalHistory)
        .filter(MedicalHistory.patient_id == p.id)
        .first()
    )

    if not h:
        h = MedicalHistory(patient_id=p.id)
        db.add(h)

    update_data = data.model_dump()

    for key, value in update_data.items():
        setattr(h, key, value)

    db.commit()
    db.refresh(h)

    return h


# --------------------------------------------------
# PATIENT DASHBOARD
# --------------------------------------------------
@router.get("/dashboard")
def dashboard(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db),
):
    p = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == user.id)
        .first()
    )

    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    h = (
        db.query(MedicalHistory)
        .filter(MedicalHistory.patient_id == p.id)
        .first()
    )

    reports_count = len(p.reports)

    return {
        "card_id": p.card_id,
        "full_name": user.full_name,
        "blood_group": p.blood_group,
        "bmi": p.bmi,
        "reports_count": reports_count,
        "allergies": h.allergies if h else [],
        "recent_records": "Live database records only",
    }