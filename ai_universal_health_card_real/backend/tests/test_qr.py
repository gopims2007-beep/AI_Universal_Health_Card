from app.services.qr import emergency_url, qr_png

def test_qr_generation():
    url = emergency_url("test-token")
    data = qr_png(url)
    assert url.endswith("/emergency/test-token")
    assert data.startswith(b"\x89PNG")
