# Patient History Sync Fix - IVR and Web Integration

## Problem
When doctors were consulting patients who came through IVR, they couldn't see the patient's past history because the system wasn't properly syncing IVR patients with existing web accounts. The patient history views only showed consultations for the specific patient record being viewed, not all patients with the same phone number.

## Root Cause
The patient history lookup views (`PatientHistorySearchView` and `PatientHistoryView`) were using exact patient matches instead of normalized phone number matching. This meant:

1. IVR patients (phone: ` 918217612080`) and web patients (phone: `+918217612080`) were treated as separate entities
2. Doctors could only see consultations for the specific patient record, not the complete medical history
3. Phone number format differences prevented proper account syncing

## Solution Implemented

### 1. Updated PatientHistorySearchView
**File**: `api/views.py`

**Before**: 
```python
# Find the patient by phone number
patient = Patient.objects.get(phone_number=phone_number)
consultations = Consultation.objects.filter(patient=patient).order_by('-date')
```

**After**:
```python
# Find patients by normalized phone number (handles IVR/web sync)
normalized_phone = normalize_phone_number(phone_number)
matching_patients = []

for patient in Patient.objects.all():
    if normalize_phone_number(patient.phone_number) == normalized_phone:
        matching_patients.append(patient.id)

# Get consultations from ALL matching patients (IVR + web accounts)
consultations = Consultation.objects.filter(
    patient_id__in=matching_patients
).order_by('-date')
```

### 2. Updated PatientHistoryView
**File**: `api/views.py`

**Before**:
```python
def get_queryset(self):
    patient_id = self.kwargs.get('patient_id')
    if patient_id: 
        return Consultation.objects.filter(patient__id=patient_id).order_by('-date')
    return Consultation.objects.none()
```

**After**:
```python
def get_queryset(self):
    patient_id = self.kwargs.get('patient_id')
    if patient_id:
        # Get the patient and find all patients with same normalized phone number
        try:
            patient = Patient.objects.get(id=patient_id)
            normalized_phone = normalize_phone_number(patient.phone_number)
            
            # Find all patients with same phone number (IVR + web accounts)
            matching_patients = []
            for p in Patient.objects.all():
                if normalize_phone_number(p.phone_number) == normalized_phone:
                    matching_patients.append(p.id)
            
            # Return consultations from ALL matching patients
            return Consultation.objects.filter(patient_id__in=matching_patients).order_by('-date')
        except Patient.DoesNotExist:
            return Consultation.objects.none()
    return Consultation.objects.none()
```

### 3. Enhanced Response Format
The `PatientHistorySearchView` now returns:
```json
{
    "consultations": [...],
    "patient_info": {
        "name": "Patient Name",
        "phone_number": "+918217612080", 
        "age": 30
    },
    "total_patients_found": 2
}
```

## Testing Results

### Test Case: Phone Number ` 918217612080`
- **IVR Patient**: ID 29, Name: "IVR Patient 2080", Phone: ` 918217612080`
- **Web Patient**: ID 7, Name: "jasmith", Phone: `+918217612080`

### Before Fix
- Doctor searching for patient history would only see consultations for one patient record
- IVR consultations were invisible when viewing web patient
- Web consultations were invisible when viewing IVR patient

### After Fix
- **PatientHistorySearchView**: Returns 2 consultations from both patients
- **PatientHistoryView**: Shows complete history regardless of which patient ID is accessed
- **Total consultations visible**: 2 (1 from web patient + 1 from IVR patient)

## API Endpoints Affected

1. **GET /api/history-search/?phone={phone_number}**
   - Used by doctors to search patient history by phone number
   - Now returns complete history from all linked accounts

2. **GET /api/history/{patient_id}/**
   - Used to view specific patient's consultation history
   - Now shows complete history including linked IVR/web consultations

## Benefits

1. **Complete Medical History**: Doctors now see the full patient history regardless of how the patient accessed the system (IVR or web)

2. **Seamless Integration**: No manual linking required - phone number normalization handles the sync automatically

3. **Better Patient Care**: Doctors have access to all previous consultations, prescriptions, and medical notes

4. **Consistent Experience**: Whether patient came via IVR or web, doctors see the same complete history

## Phone Number Normalization
The existing `normalize_phone_number()` function handles:
- Removing country codes (+91, +1)
- Removing spaces and special characters
- Standardizing to 10-digit format
- Examples:
  - ` 918217612080` → `8217612080`
  - `+918217612080` → `8217612080`
  - `918217612080` → `8217612080`

## Backward Compatibility
- Existing functionality remains unchanged
- No database schema changes required
- All existing patient records and consultations preserved
- API response format enhanced but backward compatible

## Status: ✅ COMPLETED
The fix has been implemented and tested successfully. Doctors can now see complete patient history including IVR consultations when consulting patients.