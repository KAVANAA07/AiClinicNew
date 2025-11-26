# Twilio IVR Setup Guide

## Problem: Call ends immediately without saying anything

This happens when Twilio cannot reach your webhook URL. Here's how to fix it:

## Step 1: Make sure Django server is running
```bash
python manage.py runserver
```

## Step 2: Start ngrok to expose your local server
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://6fe50d311dd7.ngrok-free.app -> http://localhost:8000
```

## Step 3: Configure Twilio Phone Number

1. Go to https://console.twilio.com/
2. Click on "Phone Numbers" → "Manage" → "Active numbers"
3. Click on your phone number (+12154340068)
4. Scroll to "Voice Configuration"
5. Set "A CALL COMES IN" to:
   - **Webhook**: `https://YOUR-NGROK-URL.ngrok-free.app/api/ivr/welcome/`
   - **HTTP Method**: POST
6. Click "Save"

## Step 4: Test the IVR

### Option A: Call the Twilio number
Call +12154340068 from your phone

### Option B: Test locally
```bash
python test_ivr.py
```

## Step 5: Check logs

Watch Django server logs for:
```
[INFO] api.ivr: IVR Welcome called - Method: POST, From: +1234567890
```

## Common Issues:

### 1. Call ends immediately
- **Cause**: Twilio cannot reach webhook URL
- **Fix**: Make sure ngrok URL is correct in Twilio console

### 2. "Sorry, no clinics are configured"
- **Cause**: No State/District/Clinic data in database
- **Fix**: Add data via Django admin

### 3. CSRF verification failed
- **Cause**: Django CSRF protection blocking Twilio
- **Fix**: Already handled with @csrf_exempt decorator

### 4. ngrok URL changes
- **Cause**: Free ngrok URLs change on restart
- **Fix**: Update Twilio webhook URL each time ngrok restarts

## Quick Test Commands:

```bash
# Test if endpoint is accessible
curl -X POST https://YOUR-NGROK-URL.ngrok-free.app/api/ivr/welcome/

# Check Django logs
python manage.py runserver

# Check if States exist
python manage.py shell
>>> from api.models import State
>>> State.objects.all()
```

## Current Configuration:
- Twilio Phone: +12154340068
- IVR Endpoint: /api/ivr/welcome/
- Method: POST
- CSRF: Exempt

## Need Help?
Check Django server logs for detailed error messages.
