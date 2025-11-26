import React, { useState } from 'react';
import './EnhancedPrescriptionForm.css';

const EnhancedPrescriptionForm = ({ onAddPrescription }) => {
  const [prescription, setPrescription] = useState({
    medicine_name: '',
    dosage: '',
    duration_days: '',
    timing_type: 'M', // M, A, N, frequency, or custom
    timing_morning: true,
    timing_afternoon: false,
    timing_evening: false,
    timing_night: false,
    frequency_per_day: 1,
    timing_1_time: '',
    timing_2_time: '',
    timing_3_time: '',
    timing_4_time: '',
    timing_5_time: '',
    timing_6_time: '',
    timing_7_time: '',
    timing_8_time: '',
    timing_1_food: '',
    timing_2_food: '',
    timing_3_food: '',
    timing_4_food: '',
    timing_5_food: '',
    timing_6_food: '',
    timing_7_food: '',
    timing_8_food: '',
    morning_time: '08:00',
    afternoon_time: '13:00',
    evening_time: '20:00',
    night_time: '22:00',
    morning_food: 'after',
    afternoon_food: 'after',
    evening_food: 'after',
    night_food: 'after',
    special_instructions: ''
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!prescription.medicine_name || !prescription.dosage || !prescription.duration_days) {
      alert('Please fill in medicine name, dosage, and duration');
      return;
    }
    
    if (prescription.timing_type === 'frequency' && (!prescription.frequency_per_day || prescription.frequency_per_day < 1)) {
      alert('Please enter valid frequency per day (1-8 times)');
      return;
    }
    
    if (prescription.timing_type !== 'frequency' && !prescription.timing_morning && !prescription.timing_afternoon && !prescription.timing_evening && !prescription.timing_night) {
      alert('Please select at least one timing (Morning/Afternoon/Evening/Night)');
      return;
    }

    // Create a copy of the prescription to avoid reference issues
    const prescriptionToAdd = { ...prescription };
    
    // Call the parent callback to add prescription
    if (onAddPrescription) {
      onAddPrescription(prescriptionToAdd);
    }
    
    // Reset form after successful addition
    setPrescription({
      medicine_name: '',
      dosage: '',
      duration_days: '',
      timing_type: 'M',
      timing_morning: true,
      timing_afternoon: false,
      timing_evening: false,
      timing_night: false,
      frequency_per_day: 1,
      timing_1_time: '',
      timing_2_time: '',
      timing_3_time: '',
      timing_4_time: '',
      timing_5_time: '',
      timing_6_time: '',
      timing_7_time: '',
      timing_8_time: '',
      timing_1_food: '',
      timing_2_food: '',
      timing_3_food: '',
      timing_4_food: '',
      timing_5_food: '',
      timing_6_food: '',
      timing_7_food: '',
      timing_8_food: '',
      morning_time: '08:00',
      afternoon_time: '13:00',
      evening_time: '20:00',
      night_time: '22:00',
      morning_food: 'after',
      afternoon_food: 'after',
      evening_food: 'after',
      night_food: 'after',
      special_instructions: ''
    });
    setShowAdvanced(false);
  };

  const handleChange = (field, value) => {
    setPrescription(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTimingTypeChange = (type) => {
    let newState = { ...prescription, timing_type: type };
    
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
      case 'frequency':
        newState = { ...newState, timing_morning: false, timing_afternoon: false, timing_evening: false, frequency_per_day: 1 };
        break;
      case 'custom':
        // Keep current selections
        break;
      default:
        // Default case for ESLint
        break;
    }
    
    setPrescription(newState);
  };

  const getPreviewText = () => {
    if (!prescription.medicine_name || !prescription.dosage || !prescription.duration_days) {
      return 'Fill in medicine details to see preview';
    }
    
    if (prescription.timing_type === 'frequency') {
      const timingDetails = [];
      for (let i = 1; i <= prescription.frequency_per_day; i++) {
        const time = prescription[`timing_${i}_time`];
        const food = prescription[`timing_${i}_food`];
        const timeStr = time ? ` at ${time}` : '';
        const foodStr = food ? ` ${food} food` : '';
        timingDetails.push(`dose ${i}${timeStr}${foodStr}`);
      }
      const detailStr = timingDetails.length > 0 ? timingDetails.join(', ') : `${prescription.frequency_per_day} times per day`;
      return `${prescription.medicine_name} ${prescription.dosage} - ${detailStr} for ${prescription.duration_days} days`;
    }
    
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
    if (prescription.timing_night) {
      const timeStr = prescription.timing_type === 'custom' && prescription.night_time ? 
        ` at ${prescription.night_time}` : '';
      const foodStr = prescription.night_food ? ` ${prescription.night_food} food` : '';
      times.push(`1 night${timeStr}${foodStr}`);
    }
    
    const timingStr = times.length > 0 ? times.join(' and ') : 'as needed';
    return `${prescription.medicine_name} ${prescription.dosage} - ${timingStr} for ${prescription.duration_days} days`;
  };

  return (
    <div className="enhanced-prescription-form">
      <h3>Add Prescription</h3>
      
      <form onSubmit={handleSubmit}>
        {/* Basic Fields */}
        <div className="basic-fields">
          <input
            type="text"
            value={prescription.medicine_name}
            onChange={(e) => handleChange('medicine_name', e.target.value)}
            placeholder="Medicine name (e.g., Paracetamol)"
            required
          />
          <input
            type="text"
            value={prescription.dosage}
            onChange={(e) => handleChange('dosage', e.target.value)}
            placeholder="Dosage (e.g., 500mg)"
            required
          />
          <input
            type="number"
            value={prescription.duration_days}
            onChange={(e) => handleChange('duration_days', e.target.value)}
            placeholder="Days"
            min="1"
            max="30"
            required
          />
        </div>

        {/* Timing Selection */}
        <div className="timing-section">
          <label>Timing Options:</label>
          <div className="timing-buttons">
            <button
              type="button"
              className={`timing-btn ${prescription.timing_type === 'M' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleTimingTypeChange('M');
              }}
            >
              Morning Only (M)
            </button>
            <button
              type="button"
              className={`timing-btn ${prescription.timing_type === 'A' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleTimingTypeChange('A');
              }}
            >
              Afternoon Only (A)
            </button>
            <button
              type="button"
              className={`timing-btn ${prescription.timing_type === 'N' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleTimingTypeChange('N');
              }}
            >
              Night Only (N)
            </button>
            <button
              type="button"
              className={`timing-btn ${prescription.timing_type === 'frequency' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleTimingTypeChange('frequency');
              }}
            >
              Times Per Day
            </button>
            <button
              type="button"
              className={`timing-btn ${prescription.timing_type === 'custom' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                handleTimingTypeChange('custom');
              }}
            >
              Custom Timing
            </button>
          </div>
          
          {prescription.timing_type === 'frequency' && (
            <div className="frequency-input">
              <label>Times per day:</label>
              <input
                type="number"
                min="1"
                max="8"
                value={prescription.frequency_per_day || 1}
                onChange={(e) => handleChange('frequency_per_day', parseInt(e.target.value))}
                placeholder="e.g., 4"
              />
              <small>Enter how many times per day (1-8 times)</small>
              
              {prescription.frequency_per_day > 0 && (
                <div className="frequency-timing-slots">
                  <h4>Set timing for each dose:</h4>
                  {Array.from({ length: prescription.frequency_per_day }, (_, index) => (
                    <div key={index} className="timing-slot">
                      <label>Dose {index + 1}:</label>
                      <input
                        type="time"
                        value={prescription[`timing_${index + 1}_time`] || ''}
                        onChange={(e) => handleChange(`timing_${index + 1}_time`, e.target.value)}
                      />
                      <select
                        value={prescription[`timing_${index + 1}_food`] || ''}
                        onChange={(e) => handleChange(`timing_${index + 1}_food`, e.target.value)}
                      >
                        <option value="">Select food timing</option>
                        <option value="before">Before food</option>
                        <option value="after">After food</option>
                        <option value="with">With food</option>
                      </select>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {prescription.timing_type === 'custom' && (
            <div className="custom-timing-checkboxes">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={prescription.timing_morning}
                  onChange={(e) => handleChange('timing_morning', e.target.checked)}
                />
                Morning
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={prescription.timing_afternoon}
                  onChange={(e) => handleChange('timing_afternoon', e.target.checked)}
                />
                Afternoon
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={prescription.timing_evening}
                  onChange={(e) => handleChange('timing_evening', e.target.checked)}
                />
                Evening
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={prescription.timing_night}
                  onChange={(e) => handleChange('timing_night', e.target.checked)}
                />
                Night
              </label>
            </div>
          )}
        </div>
        
        {/* Preview */}
        <div className="prescription-preview">
          <strong>Preview:</strong> {getPreviewText()}
        </div>

        {/* Advanced Options Toggle */}
        <button
          type="button"
          className="toggle-advanced"
          onClick={(e) => {
            e.preventDefault();
            setShowAdvanced(!showAdvanced);
          }}
        >
          {showAdvanced ? '▼ Hide Advanced Options' : '▶ Show Advanced Options'}
        </button>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="advanced-options">
            {/* Custom Times */}
            {prescription.timing_morning && (
              <div className="timing-detail">
                <label>Morning Time:</label>
                <input
                  type="time"
                  value={prescription.morning_time}
                  onChange={(e) => handleChange('morning_time', e.target.value)}
                />
                <select
                  value={prescription.morning_food}
                  onChange={(e) => handleChange('morning_food', e.target.value)}
                >
                  <option value="">Select food timing</option>
                  <option value="before">Before food</option>
                  <option value="after">After food</option>
                  <option value="with">With food</option>
                </select>
              </div>
            )}

            {prescription.timing_afternoon && (
              <div className="timing-detail">
                <label>Afternoon Time:</label>
                <input
                  type="time"
                  value={prescription.afternoon_time}
                  onChange={(e) => handleChange('afternoon_time', e.target.value)}
                />
                <select
                  value={prescription.afternoon_food}
                  onChange={(e) => handleChange('afternoon_food', e.target.value)}
                >
                  <option value="">Select food timing</option>
                  <option value="before">Before food</option>
                  <option value="after">After food</option>
                  <option value="with">With food</option>
                </select>
              </div>
            )}

            {prescription.timing_evening && (
              <div className="timing-detail">
                <label>Evening Time:</label>
                <input
                  type="time"
                  value={prescription.evening_time}
                  onChange={(e) => handleChange('evening_time', e.target.value)}
                />
                <select
                  value={prescription.evening_food}
                  onChange={(e) => handleChange('evening_food', e.target.value)}
                >
                  <option value="">Select food timing</option>
                  <option value="before">Before food</option>
                  <option value="after">After food</option>
                  <option value="with">With food</option>
                </select>
              </div>
            )}

            {prescription.timing_night && (
              <div className="timing-detail">
                <label>Night Time:</label>
                <input
                  type="time"
                  value={prescription.night_time}
                  onChange={(e) => handleChange('night_time', e.target.value)}
                />
                <select
                  value={prescription.night_food}
                  onChange={(e) => handleChange('night_food', e.target.value)}
                >
                  <option value="">Select food timing</option>
                  <option value="before">Before food</option>
                  <option value="after">After food</option>
                  <option value="with">With food</option>
                </select>
              </div>
            )}

            {/* Special Instructions */}
            <div className="form-group">
              <label>Special Instructions:</label>
              <textarea
                value={prescription.special_instructions}
                onChange={(e) => handleChange('special_instructions', e.target.value)}
                placeholder="e.g., Take with plenty of water, avoid alcohol"
                rows="2"
              />
            </div>
          </div>
        )}

        <button type="submit" className="add-prescription-btn">
          Add Medication
        </button>
      </form>
    </div>
  );
};

export default EnhancedPrescriptionForm;