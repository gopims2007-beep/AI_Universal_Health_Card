# API Endpoints

## Module 1 — Home
- `GET /`

## Module 2 — User Registration
- `POST /api/auth/register`
- `GET /api/auth/verify-email?token=...`

## Module 3 — User Login
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

## Module 4 — Patient Dashboard
- `GET /api/patient/dashboard`

## Module 5 — Patient Profile
- `GET /api/patient/profile`
- `PUT /api/patient/profile`
- `GET /api/downloads/health-card.pdf`

## Module 6 — Medical History
- `GET /api/patient/history`
- `PUT /api/patient/history`

## Module 7 — Medical Reports
- `POST /api/reports/upload`
- `GET /api/reports`
- `GET /api/reports/{report_id}/download`

## Module 8 — AI Medical Report Analysis
- `POST /api/reports/{report_id}/analyze`
- `GET /api/reports/{report_id}/analyses`

## Module 9 — QR
- `POST /api/qr/generate`
- `GET /api/qr/png`
- `POST /api/qr/revoke`
- `GET /emergency/{token}` (public read-only emergency view)

## Additional roles
- `GET /api/doctor/search?card_id=...`
- `GET /api/admin/overview`
