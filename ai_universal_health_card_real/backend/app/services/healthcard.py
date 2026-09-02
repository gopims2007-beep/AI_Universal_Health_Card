from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def build_health_card_pdf(patient, user, history):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 55

    c.setTitle("Digital Health Card")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(45, y, "AI Universal Health Card")
    y -= 35

    c.setFont("Helvetica", 11)
    rows = [
        ("Card ID", patient.card_id),
        ("Name", user.full_name),
        ("Date of Birth", str(patient.date_of_birth or "")),
        ("Gender", patient.gender or ""),
        ("Blood Group", patient.blood_group or ""),
        ("BMI", f"{patient.bmi:.2f}" if patient.bmi else ""),
        ("Emergency Contact", patient.emergency_contact_name or ""),
        ("Emergency Phone", patient.emergency_contact_phone or ""),
    ]
    for label, value in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(160, y, value[:90])
        y -= 20

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(45, y, "Emergency Medical Information")
    y -= 22
    c.setFont("Helvetica", 10)
    allergies = ", ".join(history.allergies or []) if history else ""
    diseases = ", ".join(history.diseases or []) if history else ""
    meds = ", ".join(history.current_medications or []) if history else ""
    for label, value in [("Allergies", allergies), ("Diseases", diseases), ("Medications", meds)]:
        c.drawString(45, y, f"{label}:")
        y -= 16
        for line in [value[i:i+100] for i in range(0, len(value), 100)] or [""]:
            c.drawString(65, y, line)
            y -= 14
        y -= 5

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(45, 45, "Software-generated record. Verify information with authorized healthcare professionals.")
    c.save()
    return buf.getvalue()
