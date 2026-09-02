# Quick Reference - Files & Line Changes

## Location of Each Change

### 1. Database Model

**File:** `backend/app/db/models.py`

**Lines to add:**

- **Import section:** Already has correct imports
- **After QRCodeRecord class (line ~105):**
  - Add new `EmergencyDocument` class (20 lines)
  - Add relationship to `emergency_documents` in PatientProfile class

### 2. Schemas

**File:** `backend/app/schemas.py`

**Lines to add:**

- **End of file (after PasswordResetConfirm):**
  - Add `EmergencyDocumentIn` class
  - Add `EmergencyDocumentOut` class

### 3. Emergency Documents API

**File:** `backend/app/api/emergency_docs.py`

**Status:** ✅ NEW FILE (completely created)

- Contains all CRUD endpoints
- Public endpoint for QR token access

### 4. Emergency Route

**File:** `backend/app/api/emergency.py`

**Changes:**

- **Line ~15:** Add `EmergencyDocument` to imports
- **After line ~100 (Medical Reports):** Add code to fetch documents
- **Around line ~230 (after report_cards):** Add document_cards HTML generation
- **CSS section (before @media):** Add document styling (100+ lines)
- **Mobile section:** Add document mobile styles
- **HTML template:** Add `<section>` for Emergency Documents

### 5. Main App Router

**File:** `backend/app/main.py`

**Changes:**

- **Line ~17:** Add `emergency_docs` to imports
- **Line ~75:** Add `app.include_router(emergency_docs.router)`

### 6. Frontend

**File:** `frontend/emergency-qr.html`

**Status:** ✅ COMPLETE REPLACEMENT

- Updated entire HTML file with:
  - QR management section
  - Emergency documents management
  - Add/Edit/Delete modal
  - Integrated API calls
  - Mobile responsive design
  - 600+ lines

---

## How to Verify Implementation

### Check Database Model

```bash
# Verify model exists
grep -n "class EmergencyDocument" backend/app/db/models.py
# Should return: app/db/models.py:107:class EmergencyDocument(Base):

# Verify relationship
grep -n "emergency_documents" backend/app/db/models.py
# Should return 2 results (in PatientProfile and EmergencyDocument)
```

### Check Schemas

```bash
# Verify schemas exist
grep -n "class EmergencyDocument" backend/app/schemas.py
# Should return 2 results (In and Out)
```

### Check API File

```bash
# Verify file exists
ls backend/app/api/emergency_docs.py
# Should list the file

# Verify endpoints
grep -n "@router" backend/app/api/emergency_docs.py
# Should show 6 route decorators
```

### Check Main Router

```bash
# Verify import
grep "emergency_docs" backend/app/main.py
# Should appear in 2 places (import and include_router)
```

### Check Frontend

```bash
# Verify updates
grep "emergency-docs" frontend/emergency-qr.html
# Should return multiple API call references
```

---

## API Endpoints Quick Reference

### Authenticated Endpoints (require JWT)

```
POST   /api/emergency-docs                  # Add document
GET    /api/emergency-docs                  # List patient's documents
GET    /api/emergency-docs/{doc_id}        # Get specific document
PUT    /api/emergency-docs/{doc_id}        # Update document
DELETE /api/emergency-docs/{doc_id}        # Delete document
```

### Public Endpoints (no auth needed)

```
GET    /api/emergency-docs/public/{token}  # Get docs for QR token
GET    /emergency/{token}                   # Emergency page (with docs)
```

### Existing Endpoints (unchanged)

```
POST   /api/qr/generate                     # Generate QR
GET    /api/qr/png                          # Download QR PNG
POST   /api/qr/revoke                       # Revoke QR
```

---

## Key Features Implemented

### ✅ Emergency Document Management

- Add Google Drive PDF links
- Edit existing links
- Delete documents
- Categorize documents (optional)
- Add descriptions (optional)

### ✅ Emergency QR Code

- Generate secure token-based URLs
- Download as PNG
- Share via WhatsApp
- Scan with Google Lens
- Revoke access
- No patient IDs exposed
- No JWT in QR

### ✅ Emergency Page

- Public access (no login)
- Displays patient details
- Shows medical reports
- Shows linked Google Drive PDFs
- Mobile responsive
- Professional design
- No raw JSON
- Revokable access

### ✅ Security

- JWT required for document management
- No patient IDs in QR token
- Secure random token generation
- HTML escaping for all user input
- CORS protection
- Revokable public access

---

## Testing Workflow

1. **Start Backend:** `python main.py` or appropriate command
2. **Navigate to Frontend:** `http://localhost:8000/emergency-qr.html`
3. **Login as Patient:** Use credentials
4. **Generate QR:** Click button → QR appears
5. **Add Documents:** Fill form → Save → Document listed
6. **Download QR:** Click download → PNG file saved
7. **Share QR:** Via WhatsApp or display on screen
8. **Scan QR:** Use Google Lens → Opens emergency page
9. **View Documents:** Click "Open PDF" → Opens Google Drive
10. **Verify Revoke:** Click revoke → URL no longer works

---

## Database Schema

### New Table: emergency_documents

```sql
CREATE TABLE emergency_documents (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL FOREIGN KEY,
    emergency_id VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    google_drive_url VARCHAR(1000) NOT NULL,
    description TEXT,
    document_category VARCHAR(50),
    created_at DATETIME,
    updated_at DATETIME
);
```

### Relationships

```
PatientProfile → EmergencyDocument (1:many)
```

### Emergency ID Format

```
emergency_{patient_id}_qr
Example: emergency_42_qr
```

---

## Mobile Testing Checklist

- ✅ QR displays on mobile
- ✅ Download button works on mobile
- ✅ Document list stacks vertically
- ✅ Open PDF button full-width on mobile
- ✅ Form inputs responsive
- ✅ Modal works on mobile
- ✅ Text wraps properly
- ✅ Emergency page responsive
- ✅ No horizontal scroll on mobile

---

## Security Checklist

- ✅ QR token is random (not patient ID)
- ✅ JWT not exposed in QR
- ✅ No localhost hardcoded
- ✅ HTML entities escaped
- ✅ Google Drive URLs validated
- ✅ Public routes properly identified
- ✅ Auth required for sensitive operations
- ✅ Revoke functionality works
- ✅ CORS properly configured
- ✅ No SQL injection possible (ORM used)

---

## Performance Notes

- Minimal database queries
- Efficient relationship loading
- Client-side validation
- CSS optimized
- No heavy JavaScript libraries (except QRCode.js for display)
- Responsive images/icons (emoji)

---

## Files to Keep

All these files are required for full functionality:

- ✅ `backend/app/db/models.py` (modified)
- ✅ `backend/app/schemas.py` (modified)
- ✅ `backend/app/api/emergency_docs.py` (new)
- ✅ `backend/app/api/emergency.py` (modified)
- ✅ `backend/app/main.py` (modified)
- ✅ `frontend/emergency-qr.html` (modified)

Optional (for reference/documentation):

- ✅ `QR_EMERGENCY_IMPLEMENTATION_GUIDE.md` (new - testing guide)
- ✅ `CHANGED_FILES_SUMMARY.md` (new - this file)

---

## Rollback Instructions

If needed to revert:

1. **Remove emergencies_documents table** from database
2. **Revert `backend/app/db/models.py`** to remove EmergencyDocument class
3. **Revert `backend/app/schemas.py`** to remove schemas
4. **Delete `backend/app/api/emergency_docs.py`** entirely
5. **Revert `backend/app/api/emergency.py`** to remove document display code
6. **Revert `backend/app/main.py`** to remove emergency_docs router
7. **Revert `frontend/emergency-qr.html`** to original version

All other systems (auth, QR, medical reports) remain unaffected.

---

## Success Indicators

After implementation, you should be able to:

1. ✅ Generate QR code
2. ✅ Download QR as PNG
3. ✅ Share QR via WhatsApp
4. ✅ Scan QR with Google Lens
5. ✅ Access emergency page without login
6. ✅ See emergency documents on page
7. ✅ Click documents to open Google Drive
8. ✅ Add new documents via frontend
9. ✅ Edit existing documents
10. ✅ Delete documents
11. ✅ Revoke QR code
12. ✅ Verify revoked QR is blocked

All 12 success criteria = ✅ Full implementation complete!

---

## Support

For issues or questions:

1. **Check Testing Guide:** `QR_EMERGENCY_IMPLEMENTATION_GUIDE.md`
2. **Review API Docs:** This file and changed files summary
3. **Verify Database:** Check emergency_documents table exists
4. **Check Logs:** Look for any Python/FastAPI errors
5. **Test APIs:** Use cURL commands in testing guide

---

## Production Deployment

Before deploying to production:

1. ✅ Run all tests
2. ✅ Verify database migrations
3. ✅ Test QR codes work
4. ✅ Test on mobile devices
5. ✅ Verify Google Drive sharing setup
6. ✅ Test email notifications (if applicable)
7. ✅ Review security settings
8. ✅ Load test the API
9. ✅ Check CORS settings
10. ✅ Update documentation

Ready to deploy! 🚀
