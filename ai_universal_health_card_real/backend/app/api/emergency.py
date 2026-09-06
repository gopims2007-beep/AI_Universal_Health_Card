from datetime import date
from html import escape
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
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
from app.services.storage import download_report as download_storage_report


router = APIRouter(tags=["Emergency QR Access"])


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe(value, default="Not Available"):
    """
    Safely convert database values into HTML-safe text.
    """
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return escape(text)


def format_date(value):
    """
    Format date as DD-MM-YYYY.
    """
    if not value:
        return "Not Available"

    try:
        return value.strftime("%d-%m-%Y")
    except Exception:
        return safe(value)


def calculate_age(dob):
    """
    Calculate patient's current age from date of birth.
    """
    if not dob:
        return "Not Available"

    try:
        today = date.today()

        age = (
            today.year
            - dob.year
            - ((today.month, today.day) < (dob.month, dob.day))
        )

        return str(age)

    except Exception:
        return "Not Available"


def list_to_text(value):
    """
    Convert JSON list / string / other value into readable text.
    """
    if value is None:
        return "Not Available"

    if isinstance(value, list):
        if not value:
            return "Not Available"

        items = []

        for item in value:
            if isinstance(item, dict):
                parts = []

                for key, val in item.items():
                    if val is not None and str(val).strip():
                        parts.append(
                            f"{key}: {val}"
                        )

                if parts:
                    items.append(" | ".join(parts))
            else:
                items.append(str(item))

        return ", ".join(items) if items else "Not Available"

    if isinstance(value, dict):
        if not value:
            return "Not Available"

        parts = []

        for key, val in value.items():
            if val is not None and str(val).strip():
                parts.append(
                    f"{key}: {val}"
                )

        return ", ".join(parts) if parts else "Not Available"

    text = str(value).strip()

    return text if text else "Not Available"


def html_list(value):
    """
    Convert list/dict/string into HTML bullet list.
    """
    if value is None:
        return """
        <div class="empty-data">
            Not Available
        </div>
        """

    if isinstance(value, list):

        if not value:
            return """
            <div class="empty-data">
                Not Available
            </div>
            """

        html = "<ul class='data-list'>"

        for item in value:

            if isinstance(item, dict):

                item_parts = []

                for key, val in item.items():

                    if val is not None and str(val).strip():

                        item_parts.append(
                            f"<strong>{escape(str(key))}:</strong> "
                            f"{escape(str(val))}"
                        )

                if item_parts:
                    html += (
                        "<li>"
                        + " | ".join(item_parts)
                        + "</li>"
                    )

            else:

                html += (
                    "<li>"
                    + escape(str(item))
                    + "</li>"
                )

        html += "</ul>"

        return html

    if isinstance(value, dict):

        if not value:
            return """
            <div class="empty-data">
                Not Available
            </div>
            """

        html = "<ul class='data-list'>"

        for key, val in value.items():

            if val is not None and str(val).strip():

                html += (
                    "<li>"
                    f"<strong>{escape(str(key))}:</strong> "
                    f"{escape(str(val))}"
                    "</li>"
                )

        html += "</ul>"

        return html

    text = str(value).strip()

    if not text:
        return """
        <div class="empty-data">
            Not Available
        </div>
        """

    return (
        "<div class='text-data'>"
        + escape(text)
        + "</div>"
    )


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

    # =====================================================
    # 1. VALIDATE QR TOKEN
    # =====================================================

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

    # =====================================================
    # 2. GET PATIENT PROFILE
    # =====================================================

    patient = db.get(
        PatientProfile,
        qr.patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found",
        )

    # =====================================================
    # 3. GET USER
    # =====================================================

    user = db.get(
        User,
        patient.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Patient user not found",
        )

    # =====================================================
    # 4. GET MEDICAL HISTORY
    # =====================================================

    history = (
        db.query(MedicalHistory)
        .filter(
            MedicalHistory.patient_id == patient.id
        )
        .first()
    )

    # =====================================================
    # 5. GET MEDICAL REPORTS
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

    # =====================================================
    # 6. GET EMERGENCY DOCUMENTS
    # =====================================================

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
    # 7. PATIENT BASIC INFORMATION
    # =====================================================

    patient_name = safe(
        user.full_name
    )

    card_id = safe(
        patient.card_id
    )

    date_of_birth = safe(
        format_date(patient.date_of_birth)
    )

    age = safe(
        calculate_age(patient.date_of_birth)
    )

    gender = safe(
        patient.gender
    )

    phone = safe(
        user.phone
    )

    email = safe(
        user.email
    )

    blood_group = safe(
        patient.blood_group
    )

    height = (
        f"{patient.height_cm:g} cm"
        if patient.height_cm is not None
        else "Not Available"
    )

    weight = (
        f"{patient.weight_kg:g} kg"
        if patient.weight_kg is not None
        else "Not Available"
    )

    bmi = (
        f"{patient.bmi:.2f}"
        if patient.bmi is not None
        else "Not Available"
    )

    address = safe(
        patient.address
    )

    # =====================================================
    # 8. EMERGENCY CONTACT
    # =====================================================

    emergency_name = safe(
        patient.emergency_contact_name
    )

    emergency_phone = safe(
        patient.emergency_contact_phone
    )

    emergency_relation = safe(
        patient.emergency_contact_relation
    )

    # =====================================================
    # 9. MEDICAL HISTORY
    # =====================================================

    diseases = (
        history.diseases
        if history
        else None
    )

    allergies = (
        history.allergies
        if history
        else None
    )

    medications = (
        history.current_medications
        if history
        else None
    )

    surgery_history = (
        history.surgery_history
        if history
        else None
    )

    vaccination_records = (
        history.vaccination_records
        if history
        else None
    )

    insurance_details = (
        history.insurance_details
        if history
        else None
    )

    medical_notes = (
        safe(history.notes)
        if history and history.notes
        else "Not Available"
    )

    # =====================================================
    # 10. ALLERGIES TEXT
    # =====================================================

    allergy_text = list_to_text(
        allergies
    )

    if allergy_text == "Not Available":
        allergy_text = "No known allergies"

    allergy_text = safe(
        allergy_text
    )

    # =====================================================
    # 11. MEDICAL REPORT CARDS
    # =====================================================

    report_cards = ""

    for report in reports:

        report_type = safe(
            report.report_type,
            "Medical Report",
        )

        filename = safe(
            report.original_filename,
            "Medical Report",
        )

        if report.uploaded_at:

            uploaded_at = safe(
                report.uploaded_at.strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            )

        else:

            uploaded_at = "Not Available"

        view_url = (
            f"/emergency/{escape(token)}/report/"
            f"{report.id}/view"
        )

        download_url = (
            f"/emergency/{escape(token)}/report/"
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
                    👁 View
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
            📂
            <p>
                No medical reports available.
            </p>
        </div>
        """

    # =====================================================
    # 12. EMERGENCY DOCUMENT CARDS
    # =====================================================

    document_cards = ""

    for doc in documents:

        file_name = safe(
            doc.file_name,
            "PDF Document",
        )

        category = safe(
            doc.document_category,
            "Medical Document",
        )

        description = safe(
            doc.description,
            "",
        )

        drive_url = str(
            doc.google_drive_url or ""
        ).strip()

        if drive_url:

            if not drive_url.startswith(
                ("http://", "https://")
            ):
                drive_url = (
                    "https://" + drive_url
                )

            drive_url = escape(
                drive_url,
                quote=True,
            )

        else:

            drive_url = "#"

        document_cards += f"""
        <div class="document-card">

            <div class="document-icon">
                📋
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
                    🔗 Open
                </a>

            </div>

        </div>
        """

    if not document_cards:

        document_cards = """
        <div class="empty-documents">
            📋
            <p>
                No emergency documents linked.
            </p>
        </div>
        """

    # =====================================================
    # 13. EMERGENCY HTML PAGE
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
                linear-gradient(
                    135deg,
                    #eef2ff,
                    #f8fafc
                );

            color: #172033;
        }}


        /* ================================================
           HEADER
        ================================================ */

        .top-bar {{
            background:
                linear-gradient(
                    135deg,
                    #991b1b,
                    #dc2626
                );

            color: white;

            padding: 28px 20px;

            text-align: center;

            box-shadow:
                0 5px 20px
                rgba(0, 0, 0, 0.15);
        }}

        .emergency-icon {{
            font-size: 42px;
            margin-bottom: 5px;
        }}

        .top-bar h1 {{
            margin: 0;
            font-size: 30px;
        }}

        .top-bar p {{
            margin: 8px 0 0;
            font-size: 14px;
            opacity: 0.95;
        }}


        /* ================================================
           CONTAINER
        ================================================ */

        .container {{
            width: min(
                calc(100% - 30px),
                1050px
            );

            margin: 25px auto 60px;
        }}


        /* ================================================
           WARNING
        ================================================ */

        .alert {{
            background: #fff7ed;

            border:
                1px solid #fed7aa;

            border-left:
                5px solid #f97316;

            border-radius: 14px;

            padding: 16px 18px;

            margin-bottom: 20px;

            color: #9a3412;

            font-size: 14px;
        }}


        /* ================================================
           CARD
        ================================================ */

        .card {{
            background: white;

            border-radius: 20px;

            padding: 25px;

            margin-bottom: 20px;

            box-shadow:
                0 8px 30px
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

            font-size: 22px;

            color: #172033;
        }}


        /* ================================================
           PATIENT HEADER
        ================================================ */

        .patient-header {{
            display: flex;

            align-items: center;

            gap: 18px;

            margin-bottom: 22px;
        }}

        .patient-avatar {{
            width: 75px;

            height: 75px;

            min-width: 75px;

            border-radius: 50%;

            background:
                linear-gradient(
                    135deg,
                    #fee2e2,
                    #fecaca
                );

            display: flex;

            align-items: center;

            justify-content: center;

            font-size: 35px;
        }}

        .patient-name {{
            margin: 0;

            font-size: 28px;

            color: #111827;
        }}

        .card-id {{
            margin-top: 6px;

            color: #64748b;

            font-size: 14px;
        }}


        /* ================================================
           DETAILS GRID
        ================================================ */

        .details-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap: 15px;
        }}

        .detail {{
            background: #f8fafc;

            border:
                1px solid #e2e8f0;

            border-radius: 13px;

            padding: 17px;
        }}

        .label {{
            color: #64748b;

            font-size: 13px;

            margin-bottom: 7px;
        }}

        .value {{
            font-weight: 700;

            font-size: 16px;

            word-break: break-word;

            color: #172033;
        }}

        .blood {{
            color: #b91c1c;

            font-size: 22px;
        }}

        .allergy-text {{
            color: #b45309;
        }}


        /* ================================================
           ADDRESS
        ================================================ */

        .address-box {{
            background: #f8fafc;

            border:
                1px solid #e2e8f0;

            border-radius: 13px;

            padding: 18px;

            line-height: 1.6;

            white-space: pre-wrap;
        }}


        /* ================================================
           EMERGENCY CONTACT
        ================================================ */

        .contact-box {{
            background:
                linear-gradient(
                    135deg,
                    #eff6ff,
                    #dbeafe
                );

            border:
                1px solid #bfdbfe;

            border-radius: 15px;

            padding: 20px;
        }}

        .contact-name {{
            font-size: 20px;

            font-weight: 800;

            margin-bottom: 10px;

            color: #1e3a8a;
        }}

        .contact-line {{
            margin: 7px 0;

            color: #334155;

            font-size: 15px;
        }}


        /* ================================================
           MEDICAL HISTORY
        ================================================ */

        .history-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap: 15px;
        }}

        .history-box {{
            border:
                1px solid #e2e8f0;

            background: #ffffff;

            border-radius: 14px;

            padding: 18px;
        }}

        .history-title {{
            font-size: 16px;

            font-weight: 800;

            margin-bottom: 12px;

            color: #1e293b;
        }}

        .data-list {{
            margin: 0;

            padding-left: 20px;

            color: #475569;

            line-height: 1.7;
        }}

        .data-list li {{
            margin-bottom: 5px;
        }}

        .text-data {{
            color: #475569;

            line-height: 1.6;

            white-space: pre-wrap;
        }}

        .empty-data {{SS
            color: #94a3b8;

            font-style: italic;
        }}


        /* ================================================
           REPORTS
        ================================================ */

        .report-card {{
            display: flex;

            align-items: center;

            gap: 15px;

            border:
                1px solid #e2e8f0;

            border-radius: 14px;

            padding: 16px;

            margin-bottom: 12px;

            background: white;
        }}

        .report-icon {{
            width: 50px;

            height: 50px;

            min-width: 50px;

            border-radius: 12px;

            background: #fee2e2;

            display: flex;

            align-items: center;

            justify-content: center;

            font-size: 25px;
        }}

        .report-info {{
            flex: 1;

            min-width: 0;
        }}

        .report-title {{
            font-weight: 800;

            font-size: 17px;

            color: #111827;
        }}

        .report-file {{
            margin-top: 5px;

            color: #475569;

            word-break: break-word;

            font-size: 14px;
        }}

        .report-date {{
            margin-top: 5px;

            color: #94a3b8;

            font-size: 12px;
        }}

        .report-actions {{
            display: flex;

            gap: 8px;

            flex-wrap: wrap;
        }}

        .report-actions a {{
            display: inline-block;

            text-decoration: none;

            border-radius: 9px;

            padding: 10px 14px;

            font-size: 13px;

            font-weight: 700;

            white-space: nowrap;
        }}

        .view-btn {{
            background: #2563eb;

            color: white;
        }}

        .download-btn {{
            background: #0f172a;

            color: white;
        }}


        /* ================================================
           DOCUMENTS
        ================================================ */

        .document-card {{
            display: flex;

            align-items: center;

            gap: 15px;

            border:
                1px solid #e2e8f0;

            border-radius: 14px;

            padding: 16px;

            margin-bottom: 12px;

            background: white;
        }}

        .document-icon {{
            width: 50px;

            height: 50px;

            min-width: 50px;

            border-radius: 12px;

            background: #dbeafe;

            display: flex;

            align-items: center;

            justify-content: center;

            font-size: 25px;
        }}

        .document-info {{
            flex: 1;

            min-width: 0;
        }}

        .document-category {{
            font-size: 12px;

            color: #2563eb;

            font-weight: 800;

            text-transform: uppercase;

            letter-spacing: 0.5px;
        }}

        .document-title {{
            margin-top: 5px;

            font-weight: 800;

            font-size: 17px;

            color: #111827;

            word-break: break-word;
        }}

        .document-desc {{
            margin-top: 5px;

            color: #64748b;

            font-size: 14px;

            word-break: break-word;
        }}

        .open-btn {{
            display: inline-block;

            text-decoration: none;

            border-radius: 9px;

            padding: 10px 14px;

            font-size: 13px;

            font-weight: 700;

            background: #2563eb;

            color: white;
        }}


        /* ================================================
           EMPTY
        ================================================ */

        .empty-reports,
        .empty-documents {{
            text-align: center;

            color: #64748b;

            padding: 35px 20px;
        }}


        /* ================================================
           FOOTER
        ================================================ */

        .footer {{
            text-align: center;

            color: #64748b;

            font-size: 12px;

            padding: 15px;
        }}


        /* ================================================
           MOBILE
        ================================================ */

        @media (max-width: 700px) {{

            .container {{
                width:
                    calc(100% - 20px);

                margin-top: 15px;
            }}

            .card {{
                padding: 18px;

                border-radius: 16px;
            }}

            .top-bar {{
                padding: 22px 15px;
            }}

            .top-bar h1 {{
                font-size: 23px;
            }}

            .patient-header {{
                gap: 13px;
            }}

            .patient-avatar {{
                width: 58px;

                height: 58px;

                min-width: 58px;

                font-size: 27px;
            }}

            .patient-name {{
                font-size: 21px;
            }}

            .details-grid {{
                grid-template-columns: 1fr;
            }}

            .history-grid {{
                grid-template-columns: 1fr;
            }}

            .report-card {{
                align-items: flex-start;

                flex-direction: column;
            }}

            .report-actions {{
                width: 100%;
            }}

            .report-actions a {{
                flex: 1;

                text-align: center;
            }}

            .document-card {{
                align-items: flex-start;

                flex-direction: column;
            }}

            .document-actions {{
                width: 100%;
            }}

            .open-btn {{
                display: block;

                text-align: center;
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
             BASIC PATIENT INFORMATION
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                👤 Patient Information
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
                        Date of Birth
                    </div>

                    <div class="value">
                        {date_of_birth}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Age
                    </div>

                    <div class="value">
                        {age}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Gender
                    </div>

                    <div class="value">
                        {gender}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Mobile
                    </div>

                    <div class="value">
                        {phone}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Email
                    </div>

                    <div class="value">
                        {email}
                    </div>

                </div>


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
                        Height
                    </div>

                    <div class="value">
                        {height}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        Weight
                    </div>

                    <div class="value">
                        {weight}
                    </div>

                </div>


                <div class="detail">

                    <div class="label">
                        BMI
                    </div>

                    <div class="value">
                        {bmi}
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
             ADDRESS
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                🏠 Address
            </h2>

            <div class="address-box">
                {address}
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
             MEDICAL HISTORY
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                🏥 Medical History
            </h2>


            <div class="history-grid">


                <div class="history-box">

                    <div class="history-title">
                        🦠 Diseases / Conditions
                    </div>

                    {html_list(diseases)}

                </div>


                <div class="history-box">

                    <div class="history-title">
                        ⚠️ Allergies
                    </div>

                    {html_list(allergies)}

                </div>


                <div class="history-box">

                    <div class="history-title">
                        💊 Current Medications
                    </div>

                    {html_list(medications)}

                </div>


                <div class="history-box">

                    <div class="history-title">
                        🏥 Surgery History
                    </div>

                    {html_list(surgery_history)}

                </div>


                <div class="history-box">

                    <div class="history-title">
                        💉 Vaccination Records
                    </div>

                    {html_list(vaccination_records)}

                </div>


                <div class="history-box">

                    <div class="history-title">
                        🛡️ Insurance Details
                    </div>

                    {html_list(insurance_details)}

                </div>


            </div>

        </section>


        <!-- =================================================
             MEDICAL NOTES
        ================================================= -->

        <section class="card">

            <h2 class="section-title">
                📝 Medical Notes
            </h2>

            <div class="address-box">
                {medical_notes}
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
# VIEW MEDICAL PDF
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
# DOWNLOAD MEDICAL PDF
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