import React, { useState } from 'react';
import EnhancedPrescriptionForm from './EnhancedPrescriptionForm';
import PrescriptionDisplay from './PrescriptionDisplay';
import './EnhancedConsultationForm.css';

const EnhancedConsultationForm = ({ patient, onSave, onCancel }) => {
  const [consultation, setConsultation] = useState({
    patient: patient?.id || '',
    notes: '',
    prescription_items: []
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddPrescription = (prescription) => {
    // Clean empty timing fields before adding
    const cleanedPrescription = { ...prescription };
    
    // Remove empty timing fields
    for (let i = 1; i <= 8; i++) {
      if (!cleanedPrescription[`timing_${i}_time`] || cleanedPrescription[`timing_${i}_time`] === '') {
        delete cleanedPrescription[`timing_${i}_time`];
      }
      if (!cleanedPrescription[`timing_${i}_food`] || cleanedPrescription[`timing_${i}_food`] === '') {
        delete cleanedPrescription[`timing_${i}_food`];
      }
    }
    
    setConsultation(prev => ({
      ...prev,
      prescription_items: [...prev.prescription_items, cleanedPrescription]
    }));
  };

  const handleRemovePrescription = (index) => {
    setConsultation(prev => ({
      ...prev,
      prescription_items: prev.prescription_items.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async () => {
    if (!consultation.notes.trim()) {
      alert('Please enter consultation notes');
      return;
    }

    if (consultation.prescription_items.length === 0) {
      const confirmWithoutPrescription = window.confirm(
        'No prescriptions added. Do you want to close consultation without prescriptions?'
      );
      if (!confirmWithoutPrescription) return;
    }

    const confirmClose = window.confirm(
      'Are you sure you want to close this consultation? This will save it to patient history.'
    );
    if (!confirmClose) return;

    setIsSubmitting(true);
    
    try {
      // Clean prescription data before saving
      const cleanedConsultation = {
        ...consultation,
        prescription_items: consultation.prescription_items.map(prescription => {
          const cleaned = { ...prescription };
          // Remove empty timing fields
          for (let i = 1; i <= 8; i++) {
            if (!cleaned[`timing_${i}_time`]) {
              delete cleaned[`timing_${i}_time`];
            }
            if (!cleaned[`timing_${i}_food`]) {
              delete cleaned[`timing_${i}_food`];
            }
          }
          return cleaned;
        })
      };
      
      await onSave(cleanedConsultation);
    } catch (error) {
      console.error('Error saving consultation:', error);
      alert('Failed to save consultation. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="enhanced-consultation-form">
      <div className="consultation-header">
        <h2>New Consultation</h2>
        {patient && (
          <div className="patient-info">
            <strong>{patient.name}</strong> - Age: {patient.age}
            {patient.phone_number && <span> - {patient.phone_number}</span>}
          </div>
        )}
      </div>

      {/* Consultation Notes */}
      <div className="form-section">
        <h3>Consultation Notes</h3>
        <textarea
          value={consultation.notes}
          onChange={(e) => setConsultation(prev => ({ ...prev, notes: e.target.value }))}
          placeholder="Enter detailed consultation notes, symptoms, diagnosis, recommendations..."
          rows="6"
          required
        />
      </div>

      {/* Prescription Form */}
      <div className="form-section">
        <h3>Add Prescription</h3>
        <EnhancedPrescriptionForm onAddPrescription={handleAddPrescription} />
      </div>

      {/* Prescription Display */}
      {consultation.prescription_items.length > 0 && (
        <div className="form-section">
          <div className="prescriptions-header">
            <h3>Added Prescriptions</h3>
            <button
              type="button"
              className="clear-prescriptions-btn"
              onClick={() => setConsultation(prev => ({ ...prev, prescription_items: [] }))}
            >
              Clear All
            </button>
          </div>
          
          <div className="prescriptions-with-remove">
            {consultation.prescription_items.map((prescription, index) => (
              <div key={index} className="prescription-with-remove">
                <PrescriptionDisplay 
                  prescriptions={[prescription]} 
                  showNaturalLanguage={true}
                />
                <button
                  type="button"
                  className="remove-prescription-btn"
                  onClick={() => handleRemovePrescription(index)}
                >
                  ✕ Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="form-actions">
        <button
          type="button"
          className="cancel-btn"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>
        
        <button
          type="button"
          className="save-btn close-consultation-btn"
          disabled={isSubmitting}
          onClick={handleSubmit}
        >
          {isSubmitting ? 'Closing Consultation...' : 'Close Consultation & Save to History'}
        </button>
      </div>
    </div>
  );
};

export default EnhancedConsultationForm;