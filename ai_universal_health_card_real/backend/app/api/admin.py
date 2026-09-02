from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, MedicalReport, AuditLog
from app.core.deps import require_roles

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/overview")
def overview(user=Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "reports": db.query(MedicalReport).count(),
        "audit_events": db.query(AuditLog).count(),
        "message": "Counts are calculated from the live database. No seed/demo data is included.",
    }
