# AI Clinic System - Setup Guide for Teammates

## Quick Start (5 minutes)

### 1. Clone Repository
```bash
git clone <your-github-repo-url>
cd AiClinicNew
```

### 2. Backend Setup
```bash
cd ClinicProject
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Start Services
```bash
# Terminal 1 - Django Server
python manage.py runserver

# Terminal 2 - Django-Q Worker (for background tasks)
python manage.py qcluster
```

### 5. Frontend Setup (Optional)
```bash
cd ../frontend
npm install
npm start
```

## System Access

### Admin Panel
- URL: http://localhost:8000/admin/
- Create doctors/receptionists here (patients auto-register)

### API Endpoints
- Login: http://localhost:8000/api/login/
- Patient History Search: http://localhost:8000/api/history-search/
- IVR Endpoints: http://localhost:8000/api/ivr/

## Key Features Implemented

### 🔐 Doctor Restriction System
- Doctors can only search patient history for patients they've previously consulted
- Receptionists and admin have full access
- Test with different user roles

### 📱 IVR-Web Integration
- Phone callers get automatic web accounts
- SMS credentials sent automatically
- Phone number normalization across platforms

### 🔍 Patient History Sync
- Complete medical history from both IVR and web consultations
- Normalized phone number matching
- AI-powered consultation summaries

### 🤖 AI Waiting Time Prediction
- Machine learning model predicts patient waiting times
- Automatic nightly training using historical data
- Real-time predictions when patients arrive
- High accuracy with ~12 minute average error

### ⏰ Smart Slot Management
- Real-time availability checking
- Automatic expired token cancellation
- Future-only slot booking

## Testing the System

### Create Test Data
```bash
python setup_test_data.py
```

### Test Doctor Restriction
```bash
python test_doctor_restriction.py
```

### Test IVR Flow
```bash
python test_ivr_complete.py
```

### Test AI Waiting Time Prediction
```bash
python test_waiting_time_prediction.py
python setup_ml_schedules.py
```

## Environment Variables (.env)
```
DEBUG=True
SECRET_KEY=your-secret-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
AI_BACKEND=hf
```

## Troubleshooting

### Common Issues
1. **Migration errors**: Delete db.sqlite3 and run migrations again
2. **Django-Q not working**: Check qcluster is running in separate terminal
3. **IVR not responding**: Verify Twilio credentials in .env
4. **Patient history not showing**: Check doctor has previous consultations with patient

### Debug Commands
```bash
# Check scheduled tasks
python manage.py shell -c "from django_q.models import Schedule; print(Schedule.objects.all())"

# Test phone normalization
python test_phone_search.py

# Check consultation data
python debug_detailed.py
```

## Project Structure
```
AiClinicNew/
├── ClinicProject/          # Django Backend
│   ├── api/               # Main API app
│   ├── clinic_token_system/ # Django settings
│   └── manage.py
├── frontend/              # React Frontend (optional)
└── test_*.py             # Test scripts
```

## Recent Updates
- ✅ **AI Waiting Time Prediction** - ML model predicts patient waiting times
- ✅ Doctor restriction for patient history search
- ✅ IVR-Web account integration with phone sync
- ✅ AI consultation summarizer (works offline)
- ✅ Real-time slot conflict detection
- ✅ Comprehensive logging system
- ✅ Phone number normalization

## Need Help?
Check the documentation files:
- `WAITING_TIME_PREDICTION_GUIDE.md` - Complete AI prediction system guide
- `DOCTOR_RESTRICTION_SUMMARY.md`
- `PATIENT_HISTORY_SYNC_FIX.md`
- `IVR_WEB_INTEGRATION_SUMMARY.md`