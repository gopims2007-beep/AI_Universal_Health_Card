from pathlib import Path
import re, json, joblib
from sqlalchemy.orm import Session
from app.db.models import AIAnalysis, MedicalReport

DISCLAIMER = (
    "This AI output is decision support only. It is not a diagnosis, treatment plan, "
    "or substitute for a qualified healthcare professional. Verify findings clinically."
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "models" / "disease_risk.joblib"

def _extract_insights(text: str):
    t = text or ""
    patterns = [
        r"\b(?:HbA1c|A1C)\s*[:=-]?\s*\d+(?:\.\d+)?\s*%?",
        r"\b(?:glucose|sugar)\s*[:=-]?\s*\d+(?:\.\d+)?\s*(?:mg/dL)?",
        r"\b(?:BP|blood pressure)\s*[:=-]?\s*\d{2,3}\s*/\s*\d{2,3}",
        r"\b(?:hemoglobin|haemoglobin|Hb)\s*[:=-]?\s*\d+(?:\.\d+)?\s*(?:g/dL)?",
        r"\b(?:cholesterol|LDL|HDL|triglycerides)\s*[:=-]?\s*\d+(?:\.\d+)?\s*(?:mg/dL)?",
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, t, flags=re.I))
    return list(dict.fromkeys(found))[:30]

def analyze_report(db: Session, report: MedicalReport):
    text = report.extracted_text or ""
    insights = _extract_insights(text)

    model_name = "text-extraction/no-trained-model"
    status = "completed"
    risk_label = None
    risk_score = None
    recommendations = [
        "Review the uploaded report with a qualified healthcare professional.",
        "Confirm abnormal values using the laboratory's reference ranges.",
    ]

    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
            # A trained project model must expose a predict_proba interface.
            # It is intentionally not fed invented features.
            if not hasattr(model, "predict_proba"):
                raise ValueError("Model does not support probability prediction")
            model_name = "scikit-learn-trained-project-model"
            status = "model_ready_but_feature_mapping_required"
            recommendations.append("Configure the feature mapping for the trained dataset before clinical risk scoring.")
        except Exception as exc:
            status = "model_error"
            recommendations.append("The trained model could not be loaded; no risk score was generated.")

    summary = (
        f"Extracted {len(text)} characters from the uploaded report. "
        f"Detected {len(insights)} structured-looking medical values. "
        "No clinical conclusion is asserted automatically."
    )
    if not text:
        summary = "No machine-readable report text was available. No AI risk prediction was generated."

    analysis = AIAnalysis(
        report_id=report.id,
        model_name=model_name,
        status=status,
        summary=summary,
        key_insights=insights,
        risk_label=risk_label,
        risk_score=risk_score,
        recommendations=recommendations,
        disclaimer=DISCLAIMER,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
