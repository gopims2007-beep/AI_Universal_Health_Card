from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import PatientProfile, EmergencyDocument, QRCodeRecord
from app.core.deps import require_roles
from app.schemas import EmergencyDocumentIn, EmergencyDocumentOut


router = APIRouter(
    prefix="/api/emergency-docs",
    tags=["Emergency Documents"]
)


# =========================================================
# GENERATE EMERGENCY ID
# =========================================================

def generate_emergency_id(patient_id: int) -> str:
    """
    Generate unique Emergency ID based on patient_id.
    Format: emergency_<patient_id>_qr
    """
    return f"emergency_{patient_id}_qr"


# =========================================================
# ADD EMERGENCY DOCUMENT
# =========================================================

@router.post("", response_model=EmergencyDocumentOut)
def add_emergency_document(
    doc_data: EmergencyDocumentIn,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    """
    Add a new Google Drive PDF document to emergency profile.
    """
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

    # Generate emergency ID based on patient_id
    emergency_id = generate_emergency_id(patient.id)

    # Create new emergency document
    doc = EmergencyDocument(
        patient_id=patient.id,
        emergency_id=emergency_id,
        file_name=doc_data.file_name,
        google_drive_url=doc_data.google_drive_url,
        description=doc_data.description,
        document_category=doc_data.document_category
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc


# =========================================================
# LIST EMERGENCY DOCUMENTS
# =========================================================

@router.get("", response_model=list[EmergencyDocumentOut])
def list_emergency_documents(
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    """
    Get all emergency documents for the patient.
    """
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

    docs = (
        db.query(EmergencyDocument)
        .filter(EmergencyDocument.patient_id == patient.id)
        .order_by(EmergencyDocument.created_at.desc())
        .all()
    )

    return docs


# =========================================================
# GET EMERGENCY DOCUMENT BY ID
# =========================================================

@router.get("/{doc_id}", response_model=EmergencyDocumentOut)
def get_emergency_document(
    doc_id: int,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    """
    Get a specific emergency document.
    """
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

    doc = (
        db.query(EmergencyDocument)
        .filter(
            EmergencyDocument.id == doc_id,
            EmergencyDocument.patient_id == patient.id
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return doc


# =========================================================
# UPDATE EMERGENCY DOCUMENT
# =========================================================

@router.put("/{doc_id}", response_model=EmergencyDocumentOut)
def update_emergency_document(
    doc_id: int,
    doc_data: EmergencyDocumentIn,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    """
    Update an existing emergency document.
    """
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

    doc = (
        db.query(EmergencyDocument)
        .filter(
            EmergencyDocument.id == doc_id,
            EmergencyDocument.patient_id == patient.id
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    doc.file_name = doc_data.file_name
    doc.google_drive_url = doc_data.google_drive_url
    doc.description = doc_data.description
    doc.document_category = doc_data.document_category

    db.commit()
    db.refresh(doc)

    return doc


# =========================================================
# DELETE EMERGENCY DOCUMENT
# =========================================================

@router.delete("/{doc_id}")
def delete_emergency_document(
    doc_id: int,
    user=Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    """
    Delete an emergency document.
    """
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

    doc = (
        db.query(EmergencyDocument)
        .filter(
            EmergencyDocument.id == doc_id,
            EmergencyDocument.patient_id == patient.id
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    db.delete(doc)
    db.commit()

    return {
        "message": "Document deleted successfully"
    }


# =========================================================
# GET PUBLIC EMERGENCY DOCUMENTS (via QR token)
# =========================================================

@router.get("/public/{token}")
def get_emergency_documents_public(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get emergency documents for a patient using QR token.
    This is the PUBLIC endpoint used by emergency page.
    """
    # Validate QR token
    qr = (
        db.query(QRCodeRecord)
        .filter(
            QRCodeRecord.qr_token == token,
            QRCodeRecord.revoked == False
        )
        .first()
    )

    if not qr:
        raise HTTPException(
            status_code=404,
            detail="QR code is invalid or revoked"
        )

    # Get emergency documents
    docs = (
        db.query(EmergencyDocument)
        .filter(EmergencyDocument.patient_id == qr.patient_id)
        .order_by(EmergencyDocument.created_at.desc())
        .all()
    )

    return {
        "emergency_id": f"emergency_{qr.patient_id}_qr",
        "documents": [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "google_drive_url": doc.google_drive_url,
                "description": doc.description,
                "document_category": doc.document_category,
                "created_at": doc.created_at.isoformat()
            }
            for doc in docs
        ]
    }
