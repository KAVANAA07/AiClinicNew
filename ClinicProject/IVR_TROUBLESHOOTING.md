# IVR System Troubleshooting Guide

## ✅ SYSTEM STATUS
- **IVR Endpoints**: Working correctly (tested)
- **Database**: Has required data (1 state, 1 district, 5 clinics, 6 doctors)
- **Logging**: Comprehensive logging enabled
- **Django Server**: Ready for IVR calls

## 🔧 SETUP CHECKLIST

### 1. Django Server
```bash
# Make sure Django is running
python manage.py runserver 0.0.0.0:8000
```

### 2. Ngrok Setup
```bash
# Start ngrok (in separate terminal)
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
```

### 3. Twilio Webhook Configuration
1. Go to Twilio Console → Phone Numbers → Manage → Active Numbers
2. Click your phone number
3. Set webhook URL to: `https://your-ngrok-url.ngrok-free.app/api/ivr/welcome/`
4. Make sure it's set to HTTP POST
5. Save configuration

## 🚨 COMMON ISSUES & FIXES

### Issue 1: "Application Error" on Call
**Cause**: Webhook URL not configured correctly
**Fix**: 
- Ensure webhook URL ends with `/api/ivr/welcome/`
- Use HTTPS ngrok URL, not HTTP
- Verify ngrok is running and pointing to port 8000

### Issue 2: Call Connects but No Response
**Cause**: Django server not running or wrong port
**Fix**:
- Check Django is running: `python manage.py runserver 0.0.0.0:8000`
- Verify ngrok points to correct port: `ngrok http 8000`

### Issue 3: "System Error" Message
**Cause**: Database missing required data
**Fix**: Run setup script
```bash
python setup_test_data.py
```

### Issue 4: Ngrok URL Changes
**Cause**: Free ngrok URLs change on restart
**Fix**: 
- Get new ngrok URL: check terminal where ngrok is running
- Update Twilio webhook with new URL
- Or use paid ngrok for static URLs

## 📋 TESTING STEPS

### Step 1: Test Django Server
```bash
# Test IVR endpoint directly
curl -X POST http://localhost:8000/api/ivr/welcome/ -d "From=+1234567890"
```

### Step 2: Test Ngrok
```bash
# Test through ngrok
curl -X POST https://your-ngrok-url.ngrok-free.app/api/ivr/welcome/ -d "From=+1234567890"
```

### Step 3: Test Twilio
- Call your Twilio phone number
- Should hear: "Welcome to ClinicFlow AI. Please select a state..."

## 📞 EXPECTED CALL FLOW

1. **Welcome**: "Welcome to ClinicFlow AI. Please select a state. For [State], press 1."
2. **State Selection**: "You selected [State]. Please select a district. For [District], press 1."
3. **District Selection**: "You selected [District]. Please select a clinic. For [Clinic], press 1."
4. **Clinic Selection**: "You selected [Clinic]. For next available doctor, press 1. For specialization, press 2."
5. **Booking Confirmation**: "The next available slot is with Doctor [Name] at [Time] on [Date]. Press 1 to confirm, press 2 to cancel."

## 🔍 DEBUGGING

### Check Django Logs
When someone calls, you should see:
```
[12:16:33] INFO api.ivr: IVR Welcome called - Method: POST, From: +1234567890
[12:16:33] INFO api.ivr: IVR Welcome: Generated response with 1 states
```

### Check Ngrok Logs
Ngrok terminal should show:
```
POST /api/ivr/welcome/ 200 OK
```

### Check Twilio Logs
1. Go to Twilio Console → Monitor → Logs → Errors
2. Look for webhook errors or timeouts

## ⚡ QUICK FIX COMMANDS

```bash
# 1. Restart everything
python manage.py runserver 0.0.0.0:8000
# In new terminal:
ngrok http 8000

# 2. Test IVR system
python test_ivr_endpoints.py

# 3. Setup test data if needed
python setup_test_data.py

# 4. Check current ngrok URL
# Look at ngrok terminal for: https://xxxxx.ngrok-free.app
```

## 📱 FINAL VERIFICATION

1. ✅ Django server running on port 8000
2. ✅ Ngrok running and showing HTTPS URL  
3. ✅ Twilio webhook set to: `https://your-ngrok-url.ngrok-free.app/api/ivr/welcome/`
4. ✅ Call your Twilio number
5. ✅ Should hear welcome message

**If you still get "Application Error":**
- Check Twilio webhook URL is exactly: `https://your-ngrok-url.ngrok-free.app/api/ivr/welcome/`
- Verify ngrok URL hasn't changed
- Check Django terminal for error messages
- Test endpoint directly with curl first