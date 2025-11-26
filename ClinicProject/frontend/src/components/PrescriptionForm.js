import React, { useState } from 'react';
import './PrescriptionForm.css';

const PrescriptionForm = ({ onAddPrescription }) => {
  const [prescription, setPrescription] = useState({
    medicine_name: '',
    dosage: '',
    duration_days: '',
    timing_type: 'M', // Default to Morning
    timing_morning: true,
    timing_afternoon: false,
    timing_evening: false,
    morning_time: '',
    afternoon_time: '',
    evening_time: '',
    morning_food: 'after',
    afternoon_food: 'after', 
    evening_food: 'after',
    special_instructions: ''
  });

  const handleTimingTypeChange = (type) => {
    let newState = { ...prescription, timing_type: type };
    
    // Set defaults based on timing type
    switch(type) {
      case 'M':
        newState = { ...newState, timing_morning: true, timing_afternoon: false, timing_evening: false };
        break;
      case 'A':
        newState = { ...newState, timing_morning: false, timing_afternoon: true, timing_evening: false };
        break;
      case 'N':
        newState = { ...newState, timing_morning: false, timing_afternoon: false, timing_evening: true };
        break;
      case 'custom':
        // Keep current selections for custom
        break;
    }
    
    setPrescription(newState);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prescription.medicine_name && prescription.dosage && prescription.duration_days) {
      onAddPrescription(prescription);
      // Reset form
      setPrescription({
        medicine_name: '',
        dosage: '',
        duration_days: '',
        timing_type: 'M',
        timing_morning: true,
        timing_afternoon: false,
        timing_evening: false,
        morning_time: '',
        afternoon_time: '',
        evening_time: '',
        morning_food: 'after',
        afternoon_food: 'after',
        evening_food: 'after',
        special_instructions: ''
      });
    }
  };

  const getTimingPreview = () => {
    const times = [];
    if (prescription.timing_morning) {
      const timeStr = prescription.timing_type === 'custom' && prescription.morning_time ? 
        ` at ${prescription.morning_time}` : '';
      const foodStr = prescription.morning_food ? ` ${prescription.morning_food} food` : '';
      times.push(`1 morning${timeStr}${foodStr}`);
    }
    if (prescription.timing_afternoon) {
      const timeStr = prescription.timing_type === 'custom' && prescription.afternoon_time ? 
        ` at ${prescription.afternoon_time}` : '';
      const foodStr = prescription.afternoon_food ? ` ${prescription.afternoon_food} food` : '';
      times.push(`1 afternoon${timeStr}${foodStr}`);
    }
    if (prescription.timing_evening) {
      const timeStr = prescription.timing_type === 'custom' && prescription.evening_time ? 
        ` at ${prescription.evening_time}` : '';
      const foodStr = prescription.evening_food ? ` ${prescription.evening_food} food` : '';
      times.push(`1 evening${timeStr}${foodStr}`);
    }
    return times.length > 0 ? times.join(' and ') : 'as needed';
  };

  return (
    <div className="prescription-form">
      <h3>Add Prescription</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <input
            type="text"
            placeholder="Medicine Name"
            value={prescription.medicine_name}
            onChange={(e) => setPrescription({...prescription, medicine_name: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Dosage (e.g., 500mg)"
            value={prescription.dosage}
            onChange={(e) => setPrescription({...prescription, dosage: e.target.value})}
            required
          />
          <input
            type="number"
            placeholder="Days"
            value={prescription.duration_days}
            onChange={(e) => setPrescription({...prescription, duration_days: e.target.value})}
            required
          />
        </div>

        <div className="timing-section">
          <h4>Timing Options</h4>
          <div className="timing-buttons">
            <button
              type="button"
              className={prescription.timing_type === 'M' ? 'active' : ''}
              onClick={() => handleTimingTypeChange('M')}
            >
              Morning Only (M)
            </button>
            <button
              type="button"
              className={prescription.timing_type === 'A' ? 'active' : ''}
              onClick={() => handleTimingTypeChange('A')}
            >
              Afternoon Only (A)
            </button>
            <button
              type="button"
              className={prescription.timing_type === 'N' ? 'active' : ''}
              onClick={() => handleTimingTypeChange('N')}
            >
              Night Only (N)
            </button>
            <button
              type="button"
              className={prescription.timing_type === 'custom' ? 'active' : ''}
              onClick={() => handleTimingTypeChange('custom')}
            >
              Custom Timing
            </button>
          </div>

          {prescription.timing_type === 'custom' && (
            <div className="custom-timing">
              <div className="timing-checkboxes">
                <label>
                  <input
                    type="checkbox"
                    checked={prescription.timing_morning}
                    onChange={(e) => setPrescription({...prescription, timing_morning: e.target.checked})}
                  />
                  Morning
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={prescription.timing_afternoon}
                    onChange={(e) => setPrescription({...prescription, timing_afternoon: e.target.checked})}
                  />
                  Afternoon
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={prescription.timing_evening}
                    onChange={(e) => setPrescription({...prescription, timing_evening: e.target.checked})}
                  />
                  Evening
                </label>
              </div>

              <div className="custom-times">
                {prescription.timing_morning && (
                  <input
                    type="time"
                    placeholder="Morning Time"
                    value={prescription.morning_time}
                    onChange={(e) => setPrescription({...prescription, morning_time: e.target.value})}
                  />
                )}
                {prescription.timing_afternoon && (
                  <input
                    type="time"
                    placeholder="Afternoon Time"
                    value={prescription.afternoon_time}
                    onChange={(e) => setPrescription({...prescription, afternoon_time: e.target.value})}
                  />
                )}
                {prescription.timing_evening && (
                  <input
                    type="time"
                    placeholder="Evening Time"
                    value={prescription.evening_time}
                    onChange={(e) => setPrescription({...prescription, evening_time: e.target.value})}
                  />
                )}
              </div>
            </div>
          )}
        </div>

        <div className="food-timing-section">
          <h4>Food Instructions</h4>
          <div className="food-timing-grid">
            {prescription.timing_morning && (
              <div className="food-timing-item">
                <label>Morning Dose:</label>
                <select
                  value={prescription.morning_food}
                  onChange={(e) => setPrescription({...prescription, morning_food: e.target.value})}
                >
                  <option value="before">Before Food</option>
                  <option value="after">After Food</option>
                  <option value="with">With Food</option>
                </select>
              </div>
            )}
            {prescription.timing_afternoon && (
              <div className="food-timing-item">
                <label>Afternoon Dose:</label>
                <select
                  value={prescription.afternoon_food}
                  onChange={(e) => setPrescription({...prescription, afternoon_food: e.target.value})}
                >
                  <option value="before">Before Food</option>
                  <option value="after">After Food</option>
                  <option value="with">With Food</option>
                </select>
              </div>
            )}
            {prescription.timing_evening && (
              <div className="food-timing-item">
                <label>Evening Dose:</label>
                <select
                  value={prescription.evening_food}
                  onChange={(e) => setPrescription({...prescription, evening_food: e.target.value})}
                >
                  <option value="before">Before Food</option>
                  <option value="after">After Food</option>
                  <option value="with">With Food</option>
                </select>
              </div>
            )}
          </div>
        </div>

        <div className="instructions-section">
          <textarea
            placeholder="Special Instructions (optional)"
            value={prescription.special_instructions}
            onChange={(e) => setPrescription({...prescription, special_instructions: e.target.value})}
            rows="3"
          />
        </div>

        <div className="prescription-preview">
          <h4>Preview:</h4>
          <p className="preview-text">
            {prescription.medicine_name && prescription.dosage ? 
              `${prescription.medicine_name} ${prescription.dosage} - ${getTimingPreview()} for ${prescription.duration_days || '?'} days` :
              'Fill in medicine details to see preview'
            }
          </p>
        </div>

        <button type="submit" className="add-prescription-btn">
          Add Prescription
        </button>
      </form>
    </div>
  );
};

export default PrescriptionForm;