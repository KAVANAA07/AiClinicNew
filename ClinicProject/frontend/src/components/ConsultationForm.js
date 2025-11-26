import React, { useState } from 'react';
import PrescriptionForm from './PrescriptionForm';
import './ConsultationForm.css';

const ConsultationForm = ({ patient, onSubmit, onCancel }) => {
  const [consultation, setConsultation] = useState({
    notes: '',
    prescription_items: []
  });

  const handleAddPrescription = (prescriptionData) => {
    setConsultation(prev => ({
      ...prev,
      prescription_items: [...prev.prescription_items, prescriptionData]
    }));
  };

  const handleRemovePrescription = (index) => {
    setConsultation(prev => ({
      ...prev,
      prescription_items: prev.prescription_items.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!consultation.notes.trim()) {
      alert('Please enter consultation notes');
      return;
    }
    onSubmit({
      patient: patient.id,
      notes: consultation.notes,
      prescription_items: consultation.prescription_items
    });
  };

  const formatPrescriptionDisplay = (item) => {
    const times = [];
    if (item.timing_morning) {
      const timeStr = item.timing_type === 'custom' && item.morning_time ? 
        ` at ${item.morning_time}` : '';
      const foodStr = item.morning_food ? ` ${item.morning_food} food` : '';
      times.push(`1 morning${timeStr}${foodStr}`);
    }
    if (item.timing_afternoon) {
      const timeStr = item.timing_type === 'custom' && item.afternoon_time ? 
        ` at ${item.afternoon_time}` : '';
      const foodStr = item.afternoon_food ? ` ${item.afternoon_food} food` : '';
      times.push(`1 afternoon${timeStr}${foodStr}`);
    }
    if (item.timing_evening) {
      const timeStr = item.timing_type === 'custom' && item.evening_time ? 
        ` at ${item.evening_time}` : '';
      const foodStr = item.evening_food ? ` ${item.evening_food} food` : '';
      times.push(`1 evening${timeStr}${foodStr}`);
    }
    
    const timingStr = times.length > 0 ? times.join(' and ') : 'as needed';
    let description = `${item.medicine_name} ${item.dosage} - ${timingStr} for ${item.duration_days} days`;
    
    if (item.special_instructions) {
      description += `. ${item.special_instructions}`;
    }
    
    return description;
  };

  return (
    <div className="consultation-form-container">
      <div className="consultation-header">
        <h2>Consultation for {patient.name}</h2>
        <p>Age: {patient.age} | Phone: {patient.phone_number}</p>
      </div>

      <form onSubmit={handleSubmit} className="consultation-form">
        <div className="notes-section">
          <h3>Consultation Notes</h3>
          <textarea
            value={consultation.notes}
            onChange={(e) => setConsultation(prev => ({...prev, notes: e.target.value}))}
            placeholder="Enter consultation notes, diagnosis, examination findings..."
            rows="6"
            required
          />
        </div>

        <div className="prescriptions-section">
          <h3>Prescriptions ({consultation.prescription_items.length})</h3>
          
          {consultation.prescription_items.length > 0 && (
            <div className="prescription-list">
              {consultation.prescription_items.map((item, index) => (
                <div key={index} className="prescription-item">
                  <div className="prescription-content">
                    <p>{formatPrescriptionDisplay(item)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemovePrescription(index)}
                    className="remove-prescription-btn"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <PrescriptionForm onAddPrescription={handleAddPrescription} />
        </div>

        <div className="form-actions">
          <button type="button" onClick={onCancel} className="cancel-btn">
            Cancel
          </button>
          <button type="submit" className="submit-btn">
            Complete Consultation
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConsultationForm;