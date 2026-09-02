# 🚀 Quick Start Guide - QR Emergency Documents

## In 5 Minutes

### 1. Apply Database Changes

```bash
# The database table is created automatically on app startup
# OR run this Python snippet:
from app.db.session import Base, engine
Base.metadata.create_all(bind=engine)
```

### 2. Restart Your Backend

```bash
python main.py
# or your normal start command
```

### 3. Access Emergency QR Page

Open in browser:

```
http://localhost:8000/emergency-qr.html
```

### 4. Generate QR Code

- Click **"Generate QR Code"** button
- QR image appears

### 5. Add Documents

- Click **"➕ Add Document"**
- Fill in:
  - File Name: `Blood_Test_Report.pdf`
  - Google Drive URL: `https://drive.google.com/file/d/.../view`
  - Category: `Blood Test` (optional)
  - Description: Your notes (optional)
- Click **"Save Document"**

### 6. Download & Share QR

- Click **"📥 Download QR"** → Gets PNG file
- Share via WhatsApp or display on screen

### 7. Scan QR

- Use Google Lens or phone camera
- Opens emergency page automatically
- Shows patient info + your linked PDFs

### 8. Click PDF Links

- "🔗 Open PDF" opens Google Drive
- Patient can view/download PDF

**Done!** ✅

---

## What Changed?

**6 Files Modified/Created:**

| File                                | Change                        |
| ----------------------------------- | ----------------------------- |
| `backend/app/db/models.py`          | Added EmergencyDocument model |
| `backend/app/schemas.py`            | Added validation schemas      |
| `backend/app/api/emergency_docs.py` | NEW - API endpoints           |
| `backend/app/api/emergency.py`      | Updated to show docs          |
| `backend/app/main.py`               | Registered router             |
| `frontend/emergency-qr.html`        | Complete rewrite              |

**What Stayed the Same:**

- ✅ All existing auth/login
- ✅ All existing medical reports
- ✅ All existing QR security
- ✅ All existing AI features
- ✅ All existing dashboard

---

## Security Summary

✅ **QR Contains:**

- Only public URL: `https://PUBLIC_BASE_URL/emergency/{TOKEN}`
- Secure random token (not patient ID)
- No JWT, no password, no patient ID

✅ **Emergency Page:**

- No login required
- Public access via QR token
- Revokable anytime
- Secure patient data display

✅ **Document Links:**

- Only Google Drive URLs
- Stored with patient data
- Patient controls access
- Responder can open PDFs

---

## Testing Checklist

✅ Generate QR
✅ Download QR as PNG
✅ Share QR
✅ Scan QR with Google Lens
✅ Emergency page loads
✅ See patient details
✅ See emergency documents
✅ Click to open Google Drive
✅ Edit documents
✅ Delete documents
✅ Revoke QR
✅ Generate new QR

**All checked = Ready!**

---

## API Endpoints Quick Reference

### Patient (Authenticated)

```
POST   /api/emergency-docs              Add document
GET    /api/emergency-docs              List documents
PUT    /api/emergency-docs/{id}        Update document
DELETE /api/emergency-docs/{id}        Delete document
```

### Public (No Login)

```
GET    /emergency/{token}              View emergency page
GET    /api/emergency-docs/public/{token}  Get documents for QR
```

---

## Common Tasks

### Add a Google Drive PDF

1. Go to Emergency QR page
2. Click "➕ Add Document"
3. Paste Google Drive link
4. Click "Save Document"

### Share QR via WhatsApp

1. Click "📥 Download QR"
2. Open WhatsApp
3. Send the PNG file
4. Recipient scans with Google Lens

### Delete a Document

1. Find document in list
2. Click "Delete" button
3. Confirm deletion
4. Document removed

### Revoke QR

1. Click "Revoke QR" button
2. Confirm in dialog
3. Old QR no longer works
4. Generate new QR if needed

---

## Troubleshooting

**QR not generating?**

- Check backend is running
- Verify you're logged in
- Check browser console for errors

**Documents not appearing?**

- Refresh emergency page
- Verify document was saved
- Check backend logs

**Google Drive link not opening?**

- Check URL is correct
- Verify file sharing is enabled
- Try in incognito mode

**Mobile not working?**

- Clear browser cache
- Try different browser
- Check zoom level

---

## Documentation

Three detailed guides available:

1. **QR_EMERGENCY_IMPLEMENTATION_GUIDE.md** - Complete testing procedures
2. **CHANGED_FILES_SUMMARY.md** - All code changes explained
3. **QUICK_REFERENCE.md** - Developer reference

---

## Testing Flow

```
Patient Dashboard
    ↓
Generate QR → Download PNG → Share via WhatsApp
    ↓
Scanner uses Google Lens
    ↓
Opens Emergency Page (no login)
    ↓
Shows patient info + linked PDFs
    ↓
Click PDF link
    ↓
Opens Google Drive in new tab
```

---

## Files Included

- ✅ Database model (EmergencyDocument)
- ✅ API endpoints (6 routes)
- ✅ Frontend UI (add/edit/delete)
- ✅ Emergency page (with documents)
- ✅ Security (tokens, validation)
- ✅ Mobile responsive
- ✅ Documentation (3 guides)

---

## Before Going Live

- [ ] Test all features
- [ ] Test on mobile
- [ ] Test QR scanning
- [ ] Test Google Drive links
- [ ] Review documentation
- [ ] Check security
- [ ] Monitor logs
- [ ] Backup database

---

## Support

- Check troubleshooting in main guide
- Review code comments
- Look at API examples
- Check database schema

---

## Success Indicators

✅ QR generates  
✅ QR downloads as PNG  
✅ Scans with Google Lens  
✅ Emergency page loads  
✅ Documents appear  
✅ Links work  
✅ Mobile responsive  
✅ Edit/delete works  
✅ Revoke works

**All 9 = Production Ready!** 🎉

---

## Next Steps

1. Review the implementation
2. Follow testing guide
3. Deploy to staging
4. Test thoroughly
5. Deploy to production
6. Announce to users

---

**Questions? See the comprehensive guides included.**

**Ready to go!** 🚀
