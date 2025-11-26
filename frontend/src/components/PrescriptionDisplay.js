import React from 'react';
import './PrescriptionDisplay.css';

const PrescriptionDisplay = ({ prescriptions, showNaturalLanguage = true }) => {
  if (!prescriptions || prescriptions.length === 0) {
    return (
      <div className="prescription-display">
        <h4>Prescriptions</h4>
        <p className="no-prescriptions">No prescriptions added yet.</p>
      </div>
    );
  }

  return (
    <div className="prescription-display">
      <h4>Prescriptions ({prescriptions.length})</h4>
      
      <div className="prescriptions-list">
        {prescriptions.map((prescription, index) => (
          <div key={prescription.id || index} className="prescription-item">
            {showNaturalLanguage && prescription.natural_description ? (
              // Natural language display
              <div className="natural-description">
                <p>{prescription.natural_description}</p>
              </div>
            ) : (
              // Structured display
              <div className="structured-description">
                <div className="medicine-header">
                  <strong>{prescription.medicine_name}</strong>
                  <span className="dosage">{prescription.dosage}</span>
                  <span className="duration">{prescription.duration_days} days</span>
                </div>
                
                <div className="timing-info">
                  {prescription.timing_morning && (
                    <span className="timing-badge morning">
                      Morning
                      {prescription.morning_time && ` (${prescription.morning_time})`}
                      {prescription.morning_food && ` - ${prescription.morning_food} food`}
                    </span>
                  )}
                  
                  {prescription.timing_afternoon && (
                    <span className="timing-badge afternoon">
                      Afternoon
                      {prescription.afternoon_time && ` (${prescription.afternoon_time})`}
                      {prescription.afternoon_food && ` - ${prescription.afternoon_food} food`}
                    </span>
                  )}
                  
                  {prescription.timing_evening && (
                    <span className="timing-badge evening">
                      Evening
                      {prescription.evening_time && ` (${prescription.evening_time})`}
                      {prescription.evening_food && ` - ${prescription.evening_food} food`}
                    </span>
                  )}
                </div>
                
                {prescription.special_instructions && (
                  <div className="special-instructions">
                    <strong>Instructions:</strong> {prescription.special_instructions}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PrescriptionDisplay;