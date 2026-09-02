from io import BytesIO
import secrets

import qrcode

from app.core.config import settings


# =========================================================
# CREATE SECURE QR TOKEN
# =========================================================

def make_qr_token(patient_id: int) -> str:
    """
    Create a random public QR token.

    Patient ID is NOT exposed inside the QR token.
    """

    return secrets.token_urlsafe(32)


# =========================================================
# CREATE EMERGENCY PUBLIC URL
# =========================================================

def emergency_url(token: str) -> str:
    """
    Create the public emergency URL using the current
    PUBLIC_BASE_URL configured in settings.
    """

    base_url = str(settings.public_base_url).strip().rstrip("/")

    if not base_url:
        raise RuntimeError(
            "PUBLIC_BASE_URL is not configured"
        )

    return f"{base_url}/emergency/{token}"


# =========================================================
# GENERATE QR PNG
# =========================================================

def qr_png(url: str) -> bytes:
    """
    Convert emergency URL into PNG QR code.
    """

    if not url or not url.strip():
        raise ValueError(
            "Cannot generate QR code: URL is empty"
        )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image()

    buffer = BytesIO()
    img.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()