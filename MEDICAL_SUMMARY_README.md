# Medical Summary System

A comprehensive medical summary system that structures patient consultation history like a prescription with proper categorization, risk alerts, and consultation links.

## Features

### 🏥 Medical Structure
- **Prescriptions**: Complete medication history with risk assessment
- **Laboratory Tests**: Ordered tests and results
- **Diagnoses**: Medical conditions with severity levels
- **Allergies**: Allergen warnings with high-risk alerts
- **Vital Signs**: Blood pressure, temperature, pulse, weight
- **Procedures**: Surgeries, treatments, and therapies

### 🚨 Risk Management
- **Allergy Alerts**: Automatic high-risk flagging for all allergies
- **Medication Risks**: 
  - HIGH: Warfarin, insulin, morphine, chemotherapy drugs
  - MEDIUM: Aspirin, antibiotics, steroids
  - LOW: Standard medications
- **Controlled Substances**: Special flagging for controlled medications
- **Critical Diagnoses**: Severity assessment for medical conditions

### 🔗 Consultation Links
- Every summary item links to the original consultation
- Click any prescription, diagnosis, or test to view full consultation notes
- Structured consultation notes with medical sections

### 📱 Professional Interface
- Medical-grade styling with proper visual hierarchy
- Responsive design for mobile and desktop
- Real-time data with live updates
- Professional icons and color coding

## API Endpoints

### Medical Summary
```
GET /api/medical-summary/?phone=+1234567890
GET /api/medical-summary/?patient_id=123
```

**Response Structure:**
```json
{
  "patient_info": {
    "name": "John Doe",
    "age": 35,
    "phone_number": "+1234567890",
    "patient_id": 123
  },
  "summary_generated_at": "2024-01-15T10:30:00Z",
  "total_consultations": 5,
  "risk_alerts": [
    {
      "type": "ALLERGY_ALERT",
      "severity": "HIGH",
      "message": "ALLERGY ALERT: Penicillin allergy noted",
      "date": "2024-01-10",
      "consultation_id": 45
    }
  ],
  "medical_categories": {
    "prescriptions": [
      {
        "medicine_name": "Ibuprofen",
        "dosage": "400mg",
        "duration_days": 5,
        "timing": {
          "morning": true,
          "afternoon": false,
          "evening": true
        },
        "date": "2024-01-10",
        "doctor": "Dr. Smith",
        "consultation_id": 45,
        "risk_level": "MEDIUM",
        "is_controlled_substance": false
      }
    ],
    "diagnoses": [
      {
        "diagnosis": "Acute migraine with aura",
        "date": "2024-01-10",
        "doctor": "Dr. Smith",
        "consultation_id": 45,
        "severity": "MEDIUM"
      }
    ],
    "allergies": [
      {
        "allergen": "Patient allergic to penicillin",
        "date": "2024-01-05",
        "doctor": "Dr. Johnson",
        "consultation_id": 42,
        "risk_level": "HIGH"
      }
    ],
    "laboratory_tests": [],
    "vital_signs": [],
    "procedures": []
  },
  "recent_consultations": [
    {
      "id": 45,
      "date": "2024-01-10",
      "doctor_name": "Dr. Smith",
      "doctor_specialization": "Neurology",
      "notes_preview": "Patient presents with severe headache...",
      "link": "/api/consultation/45/",
      "has_prescriptions": true
    }
  ],
  "consultation_links": [
    {
      "consultation_id": 45,
      "date": "2024-01-10",
      "doctor": "Dr. Smith",
      "link": "/api/consultation/45/"
    }
  ]
}
```

### Consultation Detail
```
GET /api/consultation/45/
```

**Response Structure:**
```json
{
  "id": 45,
  "date": "2024-01-10",
  "notes": "Patient presents with severe headache and fever...",
  "doctor": {
    "id": 12,
    "name": "Dr. Smith",
    "specialization": "Neurology"
  },
  "patient": {
    "id": 123,
    "name": "John Doe",
    "age": 35,
    "phone_number": "+1234567890"
  },
  "prescription_items": [
    {
      "id": 67,
      "medicine_name": "Ibuprofen",
      "dosage": "400mg",
      "duration_days": 5,
      "timing_morning": true,
      "timing_afternoon": false,
      "timing_evening": true
    }
  ],
  "medical_structure": {
    "chief_complaint": "Severe headache and fever",
    "history_of_present_illness": "Patient reports onset 2 days ago...",
    "physical_examination": "Blood pressure 140/90, temperature 101.5F",
    "assessment": "Acute migraine with possible viral syndrome",
    "plan": "Prescribed ibuprofen, follow up in 1 week",
    "prescriptions": [
      {
        "medicine_name": "Ibuprofen",
        "dosage": "400mg",
        "duration_days": 5,
        "timing": {
          "morning": true,
          "afternoon": false,
          "evening": true
        }
      }
    ],
    "follow_up": "Return if symptoms worsen"
  }
}
```

## Frontend Integration

### Doctor Dashboard Integration
The medical summary is integrated into the doctor dashboard with:

1. **Search Integration**: Medical Summary button in the patient search section
2. **Queue Integration**: Summary button for each patient in the queue
3. **Modal Display**: Professional overlay modal for viewing summaries

### Usage in Doctor Dashboard
```javascript
// Search section
<button onClick={() => {
  setMedicalSummaryPhone(searchPhone.trim());
  setShowMedicalSummary(true);
}}>
  📋 Medical Summary
</button>

// Queue table
<button onClick={() => {
  setMedicalSummaryPhone(token.patient?.phone_number || '');
  setShowMedicalSummary(true);
}}>
  Summary
</button>

// Modal component
{showMedicalSummary && (
  <MedicalSummary 
    phoneNumber={medicalSummaryPhone}
    onClose={() => {
      setShowMedicalSummary(false);
      setMedicalSummaryPhone('');
    }}
  />
)}
```

## Risk Assessment Logic

### Medication Risk Levels
- **HIGH RISK**: Warfarin, heparin, insulin, morphine, fentanyl, chemotherapy drugs, methotrexate, lithium, digoxin
- **MEDIUM RISK**: Aspirin, ibuprofen, acetaminophen, prednisone, antibiotics, steroids
- **LOW RISK**: All other medications

### Controlled Substances
- Morphine, oxycodone, fentanyl, codeine, tramadol
- Lorazepam, diazepam, alprazolam, clonazepam

### Diagnosis Severity
- **HIGH**: Severe, critical, emergency, acute, cancer, tumor
- **MEDIUM**: Moderate, chronic, persistent
- **LOW**: All other conditions

## Installation & Setup

### Backend Setup
1. Add the medical summary views to your Django project:
```python
# urls.py
from .medical_summary_views import MedicalSummaryView, ConsultationDetailView

urlpatterns = [
    path('medical-summary/', MedicalSummaryView.as_view(), name='medical-summary'),
    path('consultation/<int:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
]
```

### Frontend Setup
1. Add the MedicalSummary component to your React app
2. Import and integrate into doctor dashboard
3. Add CSS styling for professional appearance

### Testing
Run the test script to verify functionality:
```bash
python test_medical_summary.py
```

## Security & Permissions

### Doctor Access Control
- Doctors can only view consultations they have conducted
- Phone number search restricted to patients they have treated
- Full access control with Django authentication

### Data Privacy
- Patient phone numbers are normalized for search
- Sensitive medical data is properly categorized
- Risk alerts highlight critical information

## Customization

### Adding New Risk Categories
Extend the risk assessment logic in `medical_summary_views.py`:

```python
def assess_medication_risk(self, medicine_name):
    medicine_lower = medicine_name.lower()
    
    # Add your custom high-risk medications
    custom_high_risk = ['your_medication']
    
    for med in custom_high_risk:
        if med in medicine_lower:
            return 'HIGH'
    
    # Continue with existing logic...
```

### Custom Medical Categories
Add new categories to the summary structure:

```python
'medical_categories': {
    'prescriptions': [],
    'laboratory_tests': [],
    'medications': [],
    'diagnoses': [],
    'allergies': [],
    'vital_signs': [],
    'procedures': [],
    'custom_category': []  # Add your custom category
}
```

## Browser Support
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Performance
- Optimized for large patient histories
- Efficient database queries with proper indexing
- Responsive design for mobile devices
- Real-time updates without page refresh

## Future Enhancements
- AI-powered medical insights
- Drug interaction checking
- Automated risk scoring
- Integration with external medical databases
- Multi-language support
- Export to PDF functionality