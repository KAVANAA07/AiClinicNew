import React, { useState } from 'react';
import EnhancedConsultationForm from './EnhancedConsultationForm';
import PrescriptionDisplay from './PrescriptionDisplay';

// Example of how to integrate the enhanced prescription system into your existing App.js

const PrescriptionIntegrationExample = () => {
  const [showConsultationForm, setShowConsultationForm] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);

  // Example patient data
  const examplePatient = {
    id: 7,
    name: 'John Doe',
    age: 35,
    phone_number: '+1234567890'
  };

  // Example consultation history with enhanced prescriptions
  const exampleConsultations = [
    {
      id: 1,
      date: '2024-11-24',
      notes: 'Patient complained of fever and headache. Diagnosed with viral fever.',
      doctor: { name: 'Dr. Smith' },
      prescription_items: [
        {
          id: 1,
          medicine_name: 'Paracetamol',
          dosage: '500mg',
          duration_days: 3,
          timing_morning: true,
          timing_afternoon: true,
          timing_evening: true,
          natural_description: 'Paracetamol 500mg - 1 morning and 1 afternoon and 1 evening for 3 days'
        },
        {
          id: 2,
          medicine_name: 'Amoxicillin',
          dosage: '250mg',
          duration_days: 5,
          timing_morning: true,
          timing_evening: true,
          morning_time: '07:30',
          evening_time: '21:00',
          morning_food: 'before',
          evening_food: 'after',
          natural_description: 'Amoxicillin 250mg - 1 morning at 07:30 AM before food and 1 evening at 09:00 PM after food for 5 days'
        }
      ]
    }
  ];

  const handleSaveConsultation = async (consultationData) => {
    try {
      // Your existing API call logic
      const response = await fetch('/api/consultations/create/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
      });

      if (response.ok) {
        alert('Consultation saved successfully!');
        setShowConsultationForm(false);
        // Refresh consultations list
      } else {
        throw new Error('Failed to save consultation');
      }
    } catch (error) {
      console.error('Error saving consultation:', error);
      throw error;
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Enhanced Prescription System Demo</h1>
      
      {/* Button to show consultation form */}
      <button 
        onClick={() => {
          setSelectedPatient(examplePatient);
          setShowConsultationForm(true);
        }}
        style={{
          background: '#007bff',
          color: 'white',
          border: 'none',
          padding: '12px 24px',
          borderRadius: '6px',
          fontSize: '16px',
          cursor: 'pointer',
          marginBottom: '20px'
        }}
      >
        Start New Consultation
      </button>

      {/* Enhanced Consultation Form */}
      {showConsultationForm && (
        <EnhancedConsultationForm
          patient={selectedPatient}
          onSave={handleSaveConsultation}
          onCancel={() => setShowConsultationForm(false)}
        />
      )}

      {/* Example of displaying consultation history */}
      <div style={{ marginTop: '40px' }}>
        <h2>Patient History</h2>
        {exampleConsultations.map(consultation => (
          <div key={consultation.id} style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px',
            background: '#f8f9fa'
          }}>
            <div style={{ marginBottom: '15px' }}>
              <strong>Date:</strong> {consultation.date} | 
              <strong> Doctor:</strong> {consultation.doctor.name}
            </div>
            
            <div style={{ marginBottom: '15px' }}>
              <strong>Notes:</strong> {consultation.notes}
            </div>

            {/* Enhanced Prescription Display */}
            <PrescriptionDisplay 
              prescriptions={consultation.prescription_items}
              showNaturalLanguage={true}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default PrescriptionIntegrationExample;