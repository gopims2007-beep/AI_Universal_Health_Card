from pathlib import Path
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import (
    QRCodeRecord,
    PatientProfile,
    User,
    MedicalHistory,
    MedicalReport,
    EmergencyDocument,
)
from app.core.config import settings


router = APIRouter(tags=["Emergency QR Access"])


# =========================================================
# EMERGENCY QR PATIENT DETAILS
# =========================================================

@router.get(
    "/emergency/{token}",
    response_class=HTMLResponse,
)
def emergency_view(
    token: str,
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
    # Patient
    # -----------------------------------------------------

    patient = db.get(
        PatientProfile,
        qr.patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found",
        )

    # -----------------------------------------------------
    # User
    # -----------------------------------------------------

    user = db.get(
        User,
        patient.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Patient user not found",
        )

    # -----------------------------------------------------
    # Medical History
    # -----------------------------------------------------

    history = (
        db.query(MedicalHistory)
        .filter(
            MedicalHistory.patient_id == patient.id
        )
        .first()
    )

    # -----------------------------------------------------
    # Medical Reports
    # -----------------------------------------------------

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

    # =====================================================
    # SAFE PATIENT DATA
    # =====================================================

    patient_name = escape(
        str(user.full_name or "Not Available")
    )

    card_id = escape(
        str(patient.card_id or "Not Available")
    )

    blood_group = escape(
        str(patient.blood_group or "Not Available")
    )

    emergency_name = escape(
        str(
            patient.emergency_contact_name
            or "Not Available"
        )
    )

    emergency_phone = escape(
        str(
            patient.emergency_contact_phone
            or "Not Available"
        )
    )

    emergency_relation = escape(
        str(
            patient.emergency_contact_relation
            or "Not Available"
        )
    )

    # =====================================================
    # ALLERGIES
    # =====================================================

    allergies = (
        history.allergies
        if history and history.allergies
        else []
    )

    if isinstance(allergies, str):
        allergy_text = allergies
    elif isinstance(allergies, list):
        allergy_text = ", ".join(
            str(item)
            for item in allergies
        )
    else:
        allergy_text = str(allergies)

    if not allergy_text.strip():
        allergy_text = "No known severe allergies"

    allergy_text = escape(
        allergy_text
    )

    # -----------------------------------------------------
    # Emergency Documents
    # -----------------------------------------------------

    documents = (
        db.query(EmergencyDocument)
        .filter(
            EmergencyDocument.patient_id == patient.id
        )
        .order_by(
            EmergencyDocument.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # MEDICAL REPORT HTML
    # =====================================================

    report_cards = ""

    for report in reports:

        report_type = escape(
            str(
                report.report_type
                or "Medical Report"
            )
        )

        filename = escape(
            str(
                report.original_filename
                or "Medical Report"
            )
        )

        if report.uploaded_at:
            uploaded_at = escape(
                report.uploaded_at.strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            )
        else:
            uploaded_at = "Not Available"

        view_url = (
            f"/emergency/{token}/report/"
            f"{report.id}/view"
        )

        download_url = (
            f"/emergency/{token}/report/"
            f"{report.id}/download"
        )

        report_cards += f"""
        <div class="report-card">

            <div class="report-icon">
                📄
            </div>

            <div class="report-info">

                <div class="report-title">
                    {report_type}
                </div>

                <div class="report-file">
                    {filename}
                </div>

                <div class="report-date">
                    Uploaded: {uploaded_at}
                </div>

            </div>

            <div class="report-actions">

                <a
                    class="view-btn"
                    href="{view_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    👁 View PDF
                </a>

                <a
                    class="download-btn"
                    href="{download_url}"
                >
                    📥 Download
                </a>

            </div>

        </div>
        """

    if not report_cards:
        report_cards = """
        <div class="empty-reports">

            <div class="empty-icon">
                📂
            </div>

            <p>
                No medical reports available.
            </p>

        </div>
        """

    # =====================================================
    # EMERGENCY DOCUMENTS HTML
    # =====================================================

    document_cards = ""

    for doc in documents:

        file_name = escape(
            str(doc.file_name or "PDF Document")
        )

        category = escape(
            str(doc.document_category or "Medical Document")
        )

        description = escape(
            str(doc.description or "")
        )

        drive_url = str(doc.google_drive_url).strip()

        if not drive_url.startswith(("http://", "https://")):
            drive_url = "https://" + drive_url

        document_cards += f"""
        <div class="document-card">

            <div class="document-icon">
                📄
            </div>

            <div class="document-info">

                <div class="document-category">
                    {category}
                </div>

                <div class="document-title">
                    {file_name}
                </div>

                <div class="document-desc">
                    {description}
                </div>

            </div>

            <div class="document-actions">

                <a
                    class="open-btn"
                    href="{drive_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    🔗 Open PDF
                </a>

            </div>

        </div>
        """

    if not document_cards:
        document_cards = """
        <div class="empty-documents">

            <div class="empty-icon">
                📋
            </div>

            <p>
                No emergency documents linked.
            </p>

        </div>
        """

    # =====================================================
    # EMERGENCY HTML PAGE
    # =====================================================

    html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="robots"
        content="noindex, nofollow"
    >

    <title>
        Emergency Health Card - {patient_name}
    </title>

    <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;

            font-family:
                Arial,
                Helvetica,
                sans-serif;

            background:
                #f1f5f9;

            color:
                #172033;
        }}

        /* =================================================
           TOP HEADER
        ================================================= */

        .top-bar {{
            background:
                linear-gradient(
                    135deg,
                    #991b1b,
                    #dc2626
                );

            color:
                white;

            padding:
                24px 20px;

            text-align:
                center;

            box-shadow:
                0 3px 12px
                rgba(0, 0, 0, 0.15);
        }}

        .emergency-icon {{
            font-size:
                38px;

            margin-bottom:
                5px;
        }}

        .top-bar h1 {{
            margin:
                0;

            font-size:
                28px;
        }}

        .top-bar p {{
            margin:
                8px 0 0;

            font-size:
                14px;

            opacity:
                0.95;
        }}

        /* =================================================
           MAIN CONTAINER
        ================================================= */

        .container {{
            width:
                min(
                    calc(100% - 30px),
                    1000px
                );

            margin:
                25px auto 50px;
        }}

        /* =================================================
           WARNING
        ================================================= */

        .alert {{
            background:
                #fff7ed;

            border:
                1px solid #fed7aa;

            border-left:
                5px solid #f97316;

            border-radius:
                14px;

            padding:
                16px 18px;

            margin-bottom:
                20px;

            color:
                #9a3412;

            font-size:
                14px;
        }}

        /* =================================================
           CARD
        ================================================= */

        .card {{
            background:
                white;

            border-radius:
                18px;

            padding:
                25px;

            margin-bottom:
                20px;

            box-shadow:
                0 5px 20px
                rgba(
                    15,
                    23,
                    42,
                    0.08
                );
        }}

        .section-title {{
            margin:
                0 0 20px;

            font-size:
                21px;

            color:
                #172033;
        }}

        /* =================================================
           PATIENT HEADER
        ================================================= */

        .patient-header {{
            display:
                flex;

            align-items:
                center;

            gap:
                18px;

            margin-bottom:
                22px;
        }}

        .patient-avatar {{
            width:
                68px;

            height:
                68px;

            min-width:
                68px;

            border-radius:
                50%;

            background:
                #fee2e2;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            font-size:
                32px;
        }}

        .patient-name {{
            margin:
                0;

            font-size:
                26px;

            color:
                #111827;
        }}

        .card-id {{
            margin-top:
                5px;

            color:
                #64748b;

            font-size:
                14px;
        }}

        /* =================================================
           DETAILS GRID
        ================================================= */

        .details-grid {{
            display:
                grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap:
                15px;
        }}

        .detail {{
            background:
                #f8fafc;

            border:
                1px solid #e2e8f0;

            border-radius:
                12px;

            padding:
                16px;
        }}

        .label {{
            color:
                #64748b;

            font-size:
                13px;

            margin-bottom:
                7px;
        }}

        .value {{
            font-weight:
                600;

            font-size:
                16px;

            word-break:
                break-word;
        }}

        .blood {{
            color:
                #b91c1c;

            font-size:
                21px;
        }}

        .allergy-text {{
            color:
                #b45309;
        }}

        /* =================================================
           EMERGENCY CONTACT
        ================================================= */

        .contact-box {{
            background:
                #eff6ff;

            border:
                1px solid #bfdbfe;

            border-radius:
                14px;

            padding:
                19px;
        }}

        .contact-name {{
            font-size:
                19px;

            font-weight:
                700;

            margin-bottom:
                9px;

            color:
                #1e3a8a;
        }}

        .contact-line {{
            margin:
                6px 0;

            color:
                #334155;

            font-size:
                15px;
        }}

        /* =================================================
           REPORT CARD
        ================================================= */

        .report-card {{
            display:
                flex;

            align-items:
                center;

            gap:
                15px;

            border:
                1px solid #e2e8f0;

            border-radius:
                14px;

            padding:
                16px;

            margin-bottom:
                12px;

            transition:
                0.2s ease;

            background:
                #ffffff;
        }}

        .report-card:hover {{
            box-shadow:
                0 4px 14px
                rgba(
                    15,
                    23,
                    42,
                    0.08
                );
        }}

        .report-icon {{
            width:
                48px;

            height:
                48px;

            min-width:
                48px;

            border-radius:
                12px;

            background:
                #fee2e2;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            font-size:
                24px;
        }}

        .report-info {{
            flex:
                1;

            min-width:
                0;
        }}

        .report-title {{
            font-weight:
                700;

            font-size:
                17px;

            color:
                #111827;
        }}

        .report-file {{
            margin-top:
                5px;

            color:
                #475569;

            word-break:
                break-word;

            font-size:
                14px;
        }}

        .report-date {{
            margin-top:
                5px;

            color:
                #94a3b8;

            font-size:
                12px;
        }}

        /* =================================================
           BUTTONS
        ================================================= */

        .report-actions {{
            display:
                flex;

            gap:
                8px;

            flex-wrap:
                wrap;
        }}

        .report-actions a {{
            display:
                inline-block;

            text-decoration:
                none;

            border-radius:
                9px;

            padding:
                10px 14px;

            font-size:
                13px;

            font-weight:
                700;

            white-space:
                nowrap;
        }}

        .view-btn {{
            background:
                #2563eb;

            color:
                white;
        }}

        .view-btn:hover {{
            background:
                #1d4ed8;
        }}

        .download-btn {{
            background:
                #0f172a;

            color:
                white;
        }}

        .download-btn:hover {{
            background:
                #1e293b;
        }}

        /* =================================================
           EMPTY REPORTS
        ================================================= */

        .empty-reports {{
            text-align:
                center;

            color:
                #64748b;

            padding:
                35px 20px;
        }}

        .empty-icon {{
            font-size:
                40px;

            margin-bottom:
                8px;
        }}

        /* =================================================
           DOCUMENT CARD
        ================================================= */

        .document-card {{
            display:
                flex;

            align-items:
                center;

            gap:
                15px;

            border:
                1px solid #e2e8f0;

            border-radius:
                14px;

            padding:
                16px;

            margin-bottom:
                12px;

            transition:
                0.2s ease;

            background:
                #ffffff;
        }}

        .document-card:hover {{
            box-shadow:
                0 4px 14px
                rgba(
                    15,
                    23,
                    42,
                    0.08
                );
        }}

        .document-icon {{
            width:
                48px;

            height:
                48px;

            min-width:
                48px;

            border-radius:
                12px;

            background:
                #dbeafe;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            font-size:
                24px;
        }}

        .document-info {{
            flex:
                1;

            min-width:
                0;
        }}

        .document-category {{
            font-size:
                12px;

            color:
                #2563eb;

            font-weight:
                700;

            text-transform:
                uppercase;

            letter-spacing:
                0.5px;
        }}

        .document-title {{
            margin-top:
                5px;

            font-weight:
                700;

            font-size:
                17px;

            color:
                #111827;

            word-break:
                break-word;
        }}

        .document-desc {{
            margin-top:
                5px;

            color:
                #64748b;

            font-size:
                14px;

            word-break:
                break-word;
        }}

        /* =================================================
           DOCUMENT ACTIONS
        ================================================= */

        .document-actions {{
            display:
                flex;

            gap:
                8px;

            flex-wrap:
                wrap;
        }}

        .open-btn {{
            display:
                inline-block;

            text-decoration:
                none;

            border-radius:
                9px;

            padding:
                10px 14px;

            font-size:
                13px;

            font-weight:
                700;

            white-space:
                nowrap;

            background:
                #2563eb;

            color:
                white;
        }}

        .open-btn:hover {{
            background:
                #1d4ed8;
        }}

        /* =================================================
           EMPTY DOCUMENTS
        ================================================= */

        .empty-documents {{
            text-align:
                center;

            color:
                #64748b;

            padding:
                35px 20px;
        }}

        /* =================================================
           FOOTER
        ================================================= */

        .footer {{
            text-align:
                center;

            color:
                #64748b;

            font-size:
                12px;

            padding:
                10px;
        }}

        /* =================================================
           MOBILE
        ================================================= */

        @media (
            max-width: 700px
        ) {{

            .container {{
                width:
                    calc(100% - 20px);

                margin-top:
                    15px;
            }}

            .card {{
                padding:
                    18px;

                border-radius:
                    15px;
            }}

            .top-bar {{
                padding:
                    20px 15px;
            }}

            .top-bar h1 {{
                font-size:
                    23px;
            }}

            .patient-header {{
                gap:
                    13px;
            }}

            .patient-avatar {{
                width:
                    55px;

                height:
                    55px;

                min-width:
                    55px;

                font-size:
                    26px;
            }}

            .patient-name {{
                font-size:
                    21px;
            }}

            .details-grid {{
                grid-template-columns:
                    1fr;
            }}

            .report-card {{
                align-items:
                    flex-start;

                flex-direction:
                    column;
            }}

            .report-actions {{
                width:
                    100%;
            }}

            .report-actions a {{
                flex:
                    1;

                text-align:
                    center;
            }}

            .document-card {{
                align-items:
                    flex-start;

                flex-direction:
                    column;
            }}

            .document-actions {{
                width:
                    100%;
            }}

            .open-btn {{
                flex:
                    1;

                text-align:
                    center;
            }}

        }}

    </style>

</head>


<body>

    <!-- =================================================
         HEADER
    ================================================= -->

    <header class="top-bar">

        <div class="emergency-icon">
            🚨
        </div>

        <h1>
            Emergency Health Card
        </h1>

        <p>
            Quick access to essential medical information
        </p>

    </header>


    <main class="container">

        <!-- =================================================
             WARNING
        ================================================= -->

        <div class="alert">

            ⚠️
            <strong>
                Emergency read-only view.
            </strong>

            Verify identity and clinical information
            where possible.

        </div>


        <!-- =================================================
             PATIENT DETAILS
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                👤 Patient Details
            </h2>


            <div class="patient-header">

                <div class="patient-avatar">
                    🧑
                </div>

                <div>

                    <h2 class="patient-name">
                        {patient_name}
                    </h2>

                    <div class="card-id">

                        Health Card ID:
                        <strong>
                            {card_id}
                        </strong>

                    </div>

                </div>

            </div>


            <div class="details-grid">

                <div class="detail">

                    <div class="label">
                        Blood Group
                    </div>

                    <div class="value blood">
                        {blood_group}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Severe Allergies
                    </div>

                    <div class="value allergy-text">
                        {allergy_text}
                    </div>

                </div>

            </div>

        </section>


        <!-- =================================================
             EMERGENCY CONTACT
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                📞 Emergency Contact
            </h2>

            <div class="contact-box">

                <div class="contact-name">
                    {emergency_name}
                </div>

                <div class="contact-line">
                    📱
                    <strong>
                        Phone:
                    </strong>
                    {emergency_phone}
                </div>

                <div class="contact-line">
                    👥
                    <strong>
                        Relation:
                    </strong>
                    {emergency_relation}
                </div>

            </div>

        </section>


        <!-- =================================================
             MEDICAL REPORTS
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                📄 Medical Reports
            </h2>

            {report_cards}

        </section>


        <!-- =================================================
             EMERGENCY DOCUMENTS
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                📋 Emergency Documents
            </h2>

            {document_cards}

        </section>


        <!-- =================================================
             FOOTER
        ================================================= -->

        <div class="footer">

            AI Universal Health Card
            • Emergency Read-Only Access

        </div>

    </main>

</body>

</html>
"""

    return HTMLResponse(
        content=html
    )


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

    file_path = (
        Path(settings.upload_dir)
        / report.stored_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored medical report file not found",
        )

    # -----------------------------------------------------
    # Browser view
    # -----------------------------------------------------

    return FileResponse(
        path=file_path,
        media_type=report.mime_type,
        filename=report.original_filename,
        content_disposition_type="inline",
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

    file_path = (
        Path(settings.upload_dir)
        / report.stored_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored medical report file not found",
        )

    # -----------------------------------------------------
    # Force download
    # -----------------------------------------------------

    return FileResponse(
        path=file_path,
        media_type=report.mime_type,
        filename=report.original_filename,
        content_disposition_type="attachment",
    )