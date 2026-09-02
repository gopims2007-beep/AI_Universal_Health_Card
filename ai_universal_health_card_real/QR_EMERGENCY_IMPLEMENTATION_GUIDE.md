# QR + Emergency Documents Implementation - Testing Guide

## Overview

This implementation adds Google Drive PDF linking to the Emergency QR system. The complete flow is:

1. Patient generates Emergency QR code
2. Patient adds Google Drive PDF links
3. QR contains only the secure public token URL (no patient ID, JWT, or localhost)
4. QR is downloadable as PNG
5. PNG can be shared via WhatsApp
6. Scanning with Google Lens opens public Emergency page
7. Emergency page displays patient info + linked PDF documents
8. Clicking document links opens Google Drive PDFs

---

## Changed Files & Complete Code

### 1. Database Model - `backend/app/db/models.py`

**Changes Made:**

- Added `EmergencyDocument` model to store Google Drive PDF metadata
- Added relationship from `PatientProfile` to `EmergencyDocument`
- Each emergency document links to a patient and contains file name, Google Drive URL, category, and description

**Key Model Details:**

```python
class EmergencyDocument(Base):
    __tablename__ = "emergency_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    emergency_id: Mapped[str] = mapped_column(String(100), index=True)  # emergency_<patient_id>_qr
    file_name: Mapped[str] = mapped_column(String(255))  # Display name
    google_drive_url: Mapped[str] = mapped_column(String(1000))  # Google Drive link
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="emergency_documents")
```

---

### 2. Schemas - `backend/app/schemas.py`

**Changes Made:**

- Added `EmergencyDocumentIn` schema for input validation
- Added `EmergencyDocumentOut` schema for API responses

```python
class EmergencyDocumentIn(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    google_drive_url: str = Field(min_length=1, max_length=1000)
    description: str | None = None
    document_category: str | None = None

class EmergencyDocumentOut(EmergencyDocumentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    emergency_id: str
    created_at: datetime
    updated_at: datetime
```

---

### 3. New API File - `backend/app/api/emergency_docs.py`

**Purpose:** Manage emergency documents (CRUD operations)

**Endpoints:**

#### POST `/api/emergency-docs` - Add Document

```bash
curl -X POST http://localhost:8000/api/emergency-docs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "file_name": "Blood_Test_Report.pdf",
    "google_drive_url": "https://drive.google.com/file/d/1ABC123/view",
    "document_category": "Blood Test",
    "description": "Latest blood test results"
  }'
```

#### GET `/api/emergency-docs` - List Patient's Documents

```bash
curl http://localhost:8000/api/emergency-docs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### GET `/api/emergency-docs/{doc_id}` - Get Specific Document

```bash
curl http://localhost:8000/api/emergency-docs/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### PUT `/api/emergency-docs/{doc_id}` - Update Document

```bash
curl -X PUT http://localhost:8000/api/emergency-docs/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "file_name": "Updated_Blood_Test.pdf",
    "google_drive_url": "https://drive.google.com/file/d/1XYZ789/view",
    "document_category": "Blood Test",
    "description": "Updated blood test results"
  }'
```

#### DELETE `/api/emergency-docs/{doc_id}` - Delete Document

```bash
curl -X DELETE http://localhost:8000/api/emergency-docs/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### GET `/api/emergency-docs/public/{token}` - Get Documents via QR Token (PUBLIC)

This endpoint is used by the emergency page to fetch documents without authentication.

```bash
curl http://localhost:8000/api/emergency-docs/public/secure_token_here
```

---

### 4. Updated Emergency Route - `backend/app/api/emergency.py`

**Changes Made:**

- Imported `EmergencyDocument` model
- Fetches emergency documents for the patient
- Renders emergency documents in the HTML page
- Added CSS styles for document cards
- Added mobile-responsive styling for document display

**Key Features:**

- Displays documents as a list with emoji icons
- Each document shows: category, file name, description
- "Open PDF" button links to Google Drive URL
- Mobile-friendly layout
- No raw JSON displayed to user

---

### 5. Updated Main App - `backend/app/main.py`

**Changes Made:**

- Imported `emergency_docs` router
- Registered `emergency_docs` router in the app

```python
from app.api import (
    auth, profile, reports, qr, emergency, emergency_docs,
    downloads, admin, doctor,
)

app.include_router(emergency_docs.router)
```

---

### 6. Updated Frontend - `frontend/emergency-qr.html`

**Changes Made:**

- Integrated with actual backend API for QR generation
- Added Emergency Documents management section
- Added modal form to add/edit/delete documents
- Added document list display
- Validates Google Drive URLs
- Mobile responsive

**Key Features:**

- QR generation via `/api/qr/generate`
- Document management via `/api/emergency-docs`
- Download QR as PNG
- Preview emergency page
- Revoke QR code
- Add/edit/delete emergency documents
- List all linked documents

---

## Exact Testing Steps

### Prerequisites

- Backend running on `http://localhost:8000`
- Frontend accessible at `http://localhost:8000/emergency-qr.html` or similar
- Logged in as a patient user
- Access to Google Drive and ability to create shareable links

---

### Step 1: Prepare Google Drive PDFs

1. **Create/Upload PDF to Google Drive**
   - Upload or create a PDF file in Google Drive
   - Examples: `Blood_Test_Report.pdf`, `X-Ray_Report.pdf`, etc.

2. **Get Shareable Link**
   - Right-click the file → Share
   - Change to "Anyone with the link can view"
   - Copy the link, e.g., `https://drive.google.com/file/d/1ABC123XYZ/view`

3. **Prepare 2-3 PDFs** for testing

---

### Step 2: Generate Emergency QR Code

1. **Navigate to Emergency QR Page**
   - Go to `http://localhost:8000/emergency-qr.html`
   - Or access via your app's dashboard

2. **Click "Generate QR Code"**
   - Status should show "✅ Emergency QR Code is ready."
   - QR image appears in the container
   - Emergency URL displayed (format: `http://localhost:8000/emergency/TOKEN`)

3. **Verify QR Content**
   - The QR should contain ONLY: `http://localhost:8000/emergency/{secure_token}`
   - No localhost hardcoded URL
   - No patient ID in the QR
   - No JWT token exposed
   - Token is a secure random string (e.g., `aBcDeF123456...`)

---

### Step 3: Add Emergency Documents

1. **Click "➕ Add Document" button**
   - Modal form opens
   - Title shows "Add Emergency Document"

2. **Fill in Document Details**
   - File Name: `Blood_Test_Report.pdf`
   - Google Drive URL: Paste your shareable link
   - Category: `Blood Test` (optional)
   - Description: `Latest blood work results` (optional)

3. **Click "Save Document"**
   - Success message appears
   - Modal closes
   - Document appears in the list below

4. **Repeat for 2-3 more documents**
   - Add `X-Ray_Report.pdf`
   - Add another medical document
   - Verify all appear in the list

5. **Verify Document List**
   - Each shows: 📄 icon, category, name, description
   - Edit and Delete buttons present for each

---

### Step 4: Edit Emergency Documents

1. **Click "Edit" on any document**
   - Modal opens with current data
   - Title shows "Edit Emergency Document"
   - All fields pre-filled

2. **Modify a field**
   - Change description or category
   - Update the Google Drive URL

3. **Click "Save Document"**
   - Document updates in list
   - Changes persist

---

### Step 5: Download QR as PNG

1. **Click "📥 Download QR"**
   - PNG file downloads: `Emergency-Health-Card-QR.png`
   - File size ~10-50KB

2. **Verify PNG Quality**
   - Open the PNG in an image viewer
   - QR is clearly visible
   - Can be scanned with any QR reader

---

### Step 6: Test QR via WhatsApp

1. **Share PNG via WhatsApp** (if testing on device)
   - Send the PNG file via WhatsApp to a contact
   - Alternatively, open the image on the same device

2. **Open in WhatsApp**
   - Receive the message with the QR
   - Tap to expand the image

3. **Tap Google Lens Icon**
   - In WhatsApp image view, tap the Google Lens icon (if available)
   - Or download and use Google Lens/Camera app

---

### Step 7: Scan QR with Google Lens / Phone Camera

1. **Use Google Lens** (preferred method)
   - Open Google Lens app or Google Photos
   - Point camera at the PNG
   - Tap the link when recognized

2. **Use Phone Camera** (alternate)
   - Open native Camera app
   - Point at PNG or QR code displayed on screen
   - Tap notification that appears with the URL

3. **Expected Result**
   - Browser opens to emergency URL
   - Format: `http://localhost:8000/emergency/{TOKEN}`

---

### Step 8: View Emergency Page

1. **Page Loads Without Login**
   - No login required
   - No OTP needed
   - Anyone with the QR can access

2. **Verify Page Content**
   - Header: 🚨 Emergency Health Card
   - Patient Details: Name, Card ID, Blood Group, Allergies
   - Emergency Contact: Name, Phone, Relation
   - Medical Reports: Any uploaded reports with View/Download buttons
   - **Emergency Documents section**: Your linked PDFs!

3. **Verify Document Display**
   - Section title: "📋 Emergency Documents"
   - Each document shows:
     - 📄 icon
     - Category badge (e.g., "BLOOD TEST" in blue)
     - File name (e.g., "Blood_Test_Report.pdf")
     - Description (if provided)
     - "🔗 Open PDF" button

4. **Verify Mobile Responsive**
   - Document cards stack vertically
   - Full-width buttons on mobile
   - Text wraps properly
   - Easy to tap on small screens

---

### Step 9: Click Emergency Documents

1. **Click "🔗 Open PDF" on any document**
   - New tab/window opens
   - Google Drive link loads
   - PDF displays in new tab
   - User can view, download, etc.

2. **Test All Documents**
   - Click each document link
   - Verify each opens the correct Google Drive PDF
   - Verify no errors

---

### Step 10: Test Revoked QR

1. **Go back to Emergency QR page**
   - Click "Revoke QR" button
   - Confirm in dialog

2. **Verify QR Revoked**
   - Status shows "✅ Emergency QR Code revoked successfully."
   - QR container clears
   - Emergency URL shows "QR code revoked."
   - Buttons disabled

3. **Try to Access Revoked URL**
   - Open the old emergency URL in a new tab
   - Should show 404: "QR code is invalid or revoked"
   - Documents no longer accessible via revoked token

---

### Step 11: Generate New QR

1. **Click "Generate QR Code" again**
   - New QR generates (new token)
   - New emergency URL displayed
   - QR image regenerated

2. **Verify New Token**
   - Token is different from previous
   - New emergency URL works
   - Emergency page accessible with new URL

---

### Step 12: Test Document Deletion

1. **Click "Delete" on a document**
   - Confirmation dialog appears
   - Confirm deletion

2. **Verify Deletion**
   - Document removed from list
   - No longer appears on emergency page

3. **Generate New QR (if needed)**
   - Update QR to reflect current documents
   - Scan to verify documents still linked

---

## API Test Commands (cURL)

### Login (get JWT token)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "password123"}'
```

Response includes `access_token`. Use this in subsequent requests.

### Generate QR

```bash
curl -X POST http://localhost:8000/api/qr/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Add Emergency Document

```bash
curl -X POST http://localhost:8000/api/emergency-docs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "file_name": "Blood_Test_Report.pdf",
    "google_drive_url": "https://drive.google.com/file/d/YOUR_FILE_ID/view",
    "document_category": "Blood Test",
    "description": "Latest results"
  }'
```

### List Emergency Documents

```bash
curl http://localhost:8000/api/emergency-docs \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Access Emergency Page (PUBLIC - no auth)

```bash
curl http://localhost:8000/emergency/{token}
```

### Get Emergency Documents via Public Token

```bash
curl http://localhost:8000/api/emergency-docs/public/{token}
```

---

## Expected Behavior

### QR Code Characteristics

- ✅ Contains only public Emergency route URL
- ✅ Token is secure (not patient ID)
- ✅ No localhost hardcoded
- ✅ No JWT token exposed
- ✅ Works when shared via WhatsApp
- ✅ Scannable with Google Lens
- ✅ Downloadable as PNG

### Emergency Page Characteristics

- ✅ No login required
- ✅ No OTP required
- ✅ Shows patient details (name, blood group, allergies)
- ✅ Shows emergency contact
- ✅ Shows medical reports with download options
- ✅ Shows emergency documents with Google Drive links
- ✅ Mobile responsive layout
- ✅ Professional design
- ✅ No raw JSON exposed

### Document Management

- ✅ Add new documents with Google Drive URLs
- ✅ Edit existing documents
- ✅ Delete documents
- ✅ Documents appear on emergency page immediately
- ✅ Clicking links opens Google Drive PDFs
- ✅ Category and description display correctly

### Security

- ✅ Revoked QR blocks public access
- ✅ Only patient can manage own documents
- ✅ No patient ID in QR token
- ✅ No password or JWT exposed

---

## Troubleshooting

### Issue: "QR code not generated yet"

- **Solution:** Ensure backend is running, you're logged in, and click "Generate QR Code"

### Issue: Document not appearing on emergency page

- **Solution:** Ensure you added the document successfully, then scan new QR or refresh emergency page

### Issue: Google Drive link doesn't open

- **Solution:** Verify the Google Drive URL is correct and the file has "Anyone with link" sharing enabled

### Issue: QR not scannable

- **Solution:** Ensure PNG is downloaded correctly, try different QR readers, check resolution

### Issue: Emergency page shows 404

- **Solution:** Verify token is correct, check if QR was revoked, ensure backend is running

### Issue: Mobile page broken

- **Solution:** Clear browser cache, zoom out if needed, try different browser

---

## Files Modified/Created

1. ✅ `backend/app/db/models.py` - Added EmergencyDocument model
2. ✅ `backend/app/schemas.py` - Added EmergencyDocumentIn/Out schemas
3. ✅ `backend/app/api/emergency_docs.py` - Created new file with CRUD endpoints
4. ✅ `backend/app/api/emergency.py` - Updated to display documents
5. ✅ `backend/app/main.py` - Registered emergency_docs router
6. ✅ `frontend/emergency-qr.html` - Complete rewrite with document management

---

## Summary

This implementation provides a complete Google Drive + Emergency QR document flow:

- **QR Generation:** Secure token-based URLs only
- **Document Management:** Add/edit/delete Google Drive PDF links
- **Emergency Page:** Public access to patient info + linked documents
- **Security:** No patient IDs or JWTs in QR, revokable access
- **UX:** Mobile-friendly, professional design, easy document sharing
- **Integration:** Uses existing patient/card infrastructure, no duplicate databases

The system allows patients to share emergency medical information securely via QR codes, with linked Google Drive documents for comprehensive emergency access.
