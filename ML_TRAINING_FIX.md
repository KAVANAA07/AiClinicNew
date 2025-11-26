# ML Training Error Fix

## Problem
The ML training task was failing with:
```
AttributeError: 'Token' object has no attribute 'appointment_date'. Did you mean: 'appointment_time'?
```

## Root Cause
Several files were referencing `appointment_date` field which doesn't exist in the Token model. The correct field is `date`.

## Files Fixed

### 1. api/live_dashboard_views.py
- Changed `token__appointment_date=today` → `token__date=today`
- Changed `appointment_date=today` → `date=today` in multiple filter queries
- Changed `status='in_progress'` → `status='in_consultancy'` (correct status name)

### 2. api/queue_update_signals.py
- Changed `appointment_date=instance.appointment_date` → `appointment_date=instance.date`

### 3. api/waiting_time_predictor.py
- Added try-catch blocks around token processing
- Fixed variable naming conflicts (`today` → `today_date`)

## Result
✅ ML training now works without errors
✅ Background tasks can run successfully
✅ Waiting time predictions are functional

## Token Model Fields Reference
- `date` - The appointment date (DateField)
- `appointment_time` - The appointment time (TimeField)
- `created_at` - When token was created (DateTimeField)
- `completed_at` - When consultation completed (DateTimeField)

**Note**: There is NO `appointment_date` field in the Token model.