# 🧪 SermonAI Testing Guide

## Quick Testing Strategy (Recommended for Today)

### 🎯 **Goal**: Verify signup → upload → transcription flow works end-to-end

### 📋 **Testing Approach**: Integration-Heavy Strategy
- **Layer 1**: Quick validation tests (5 minutes)
- **Layer 2**: Real service integration (10 minutes) 
- **Layer 3**: Your alias email test (15 minutes)

---

## 🚀 **Step-by-Step Execution**

### **Prerequisites** 
```bash
# 1. Ensure your environment is running
# 2. Set your ngrok callback URL in settings.py:
CALLBACK_URL = "https://your-ngrok-url.ngrok.io/api/v1/transcription/callback"

# 3. Create test audio file
python create_test_audio.py
```

### **Step 1: Quick Validation (5 min)**
```bash
# Test core validation logic
cd tests
python -c "
from test_complete_flow import TestCompleteFlow
test = TestCompleteFlow()
test.test_validation_service_basic_logic()
test.test_signup_data_validation({'email': 'test@test.com', 'password': 'Test123!', 'first_name': 'Test', 'last_name': 'User', 'country': 'US', 'organization_name': 'Test Org'})
print('✅ Core validation tests passed')
"
```

### **Step 2: Service Integration (10 min)**
```bash
# Test with real Supabase
pytest tests/test_complete_flow.py::TestCompleteFlow::test_supabase_service_integration -v -s
```

### **Step 3: Your Alias Email Test (15 min)**
```bash
# 1. Edit test_quick_flow.py - replace email with your alias
# 2. Run the test
python tests/test_quick_flow.py

# OR run via pytest
pytest tests/test_quick_flow.py -v -s
```

### **Step 4: Full Journey Test (Optional)**
```bash
# Complete end-to-end with real audio file
pytest tests/test_complete_flow.py::TestCompleteFlow::test_complete_user_journey -v -s
```

---

## 🎯 **Expected Results**

### **✅ Success Indicators**
```
🔹 Testing signup for: your-alias@example.com
✅ Signup successful!
   User ID: abc-123-uuid
   Organization: Your Test Organization  
   Access Token: eyJhbGciOiJIUzI1Ni...

🔹 Testing file upload...
✅ Upload successful!
   Video ID: def-456-uuid
   Request ID: dgm_12345-request-id

🎉 COMPLETE FLOW SUCCESS!
```

### **⚠️ Expected Partial Failures**
- **Fake audio validation fails**: ✅ Good! Validation working
- **Deepgram callback timeout**: ⏳ Normal for test environment
- **File size warnings**: ℹ️ Expected for small test files

### **❌ Concerning Failures**
- Signup fails with database errors
- Authentication token issues
- Supabase connection problems
- File upload crashes

---

## 🔧 **Troubleshooting Common Issues**

### **Issue: Signup fails**
```bash
# Check Supabase connection
python -c "from app.services.supabase_service import supabase_service; print('Supabase connected')"

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### **Issue: File upload fails**
```bash
# Verify file validation
python -c "
from app.services.validation_service import validation_service
from fastapi import UploadFile
from io import BytesIO
file = UploadFile(filename='test.mp3', file=BytesIO(b'test'*1000), content_type='audio/mpeg')
result = validation_service.validate_basic_upload(file)
print(f'Validation result: {result.is_valid}')
"
```

### **Issue: Transcription doesn't start**
```bash
# Check Deepgram API key
python -c "from app.config.settings import settings; print(f'Deepgram key configured: {bool(settings.DEEPGRAM_API_KEY)}')"

# Check callback URL
python -c "from app.config.settings import settings; print(f'Callback URL: {settings.CALLBACK_URL}')"
```

---

## 📊 **Test Data Cleanup**

### **After Testing**
```python
# Optional: Clean up test users/clients
# (You can also leave them for debugging)

# Check created test data in Supabase dashboard:
# - auth.users table
# - public.user_profiles table  
# - public.clients table
# - public.videos table
# - public.transcripts table
```

---

## 🎯 **Success Criteria for V1**

✅ **Must Work**:
- [x] User signup with alias email
- [x] Client creation with organization name
- [x] File upload validation (rejects invalid files)
- [x] Valid file uploads to Supabase storage
- [x] Deepgram transcription job starts
- [x] Database records are consistent

⏳ **Nice to Have** (can fix later):
- [ ] Progress feedback during upload
- [ ] Transcription completion callbacks
- [ ] Status polling endpoints
- [ ] Error recovery mechanisms

---

## 🚀 **Ready for Production Checklist**

Before going live:
- [ ] Replace test emails with real user signups
- [ ] Configure production callback URLs
- [ ] Set up monitoring for transcription jobs
- [ ] Add rate limiting for uploads
- [ ] Test with various file sizes/formats
- [ ] Verify RLS policies work correctly

---

*Run these tests and let me know which step fails (if any). The goal is to verify your core flow works before building additional features!*