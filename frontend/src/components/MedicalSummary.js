import React, { useState, useEffect, useCallback } from 'react';
import './MedicalSummary.css';

const MedicalSummary = ({ phoneNumber, patientId, onClose }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedConsultation, setSelectedConsultation] = useState(null);

  const fetchMedicalSummary = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      if (phoneNumber) params.append('phone', phoneNumber);
      if (patientId) params.append('patient_id', patientId);

      const response = await fetch(`/api/medical-summary/?${params}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to fetch medical summary');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [phoneNumber, patientId]);

  useEffect(() => {
    fetchMedicalSummary();
  }, [fetchMedicalSummary]);

  const fetchConsultationDetail = async (consultationId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/consultation/${consultationId}/`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedConsultation(data);
      } else {
        console.error('Failed to fetch consultation details');
      }
    } catch (err) {
      console.error('Error fetching consultation:', err);
    }
  };



  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Extract medical information from consultation notes using professional medical terminology
  const extractInfoFromNotes = (notes) => {
    const sentences = notes.split(/[.!?]/).filter(s => s.trim());
    
    const result = {
      complaints: [],
      diagnoses: [],
      medications: [],
      vitals: [],
      labTests: [],
      allergies: [],
      riskFactors: [],
      comorbidities: []
    };

    sentences.forEach(sentence => {
      const sentenceLower = sentence.toLowerCase().trim();
      
      // Chief Complaints (CC)
      if (sentenceLower.includes('complaint') || sentenceLower.includes('pain') || 
          sentenceLower.includes('fever') || sentenceLower.includes('headache') ||
          sentenceLower.includes('symptom') || sentenceLower.includes('problem') ||
          sentenceLower.includes('presents with') || sentenceLower.includes('chief complaint')) {
        result.complaints.push(sentence.trim());
      }
      
      // Clinical Diagnoses
      if (sentenceLower.includes('diagnos') || sentenceLower.includes('condition') ||
          sentenceLower.includes('disease') || sentenceLower.includes('disorder') ||
          sentenceLower.includes('impression') || sentenceLower.includes('assessment')) {
        result.diagnoses.push(sentence.trim());
      }
      
      // Pharmacotherapy (Medications)
      if (sentenceLower.includes('prescrib') || sentenceLower.includes('medicin') ||
          sentenceLower.includes('tablet') || sentenceLower.includes('capsule') ||
          sentenceLower.includes('mg') || sentenceLower.includes('dose') ||
          sentenceLower.includes('therapy') || sentenceLower.includes('treatment')) {
        result.medications.push(sentence.trim());
      }
      
      // Vital Parameters
      if (sentenceLower.includes('bp') || sentenceLower.includes('blood pressure') ||
          sentenceLower.includes('temperature') || sentenceLower.includes('pulse') ||
          sentenceLower.includes('weight') || sentenceLower.includes('height') ||
          sentenceLower.includes('hr') || sentenceLower.includes('spo2') ||
          sentenceLower.includes('oxygen saturation')) {
        result.vitals.push(sentence.trim());
      }
      
      // Laboratory Studies
      if (sentenceLower.includes('test') || sentenceLower.includes('lab') ||
          sentenceLower.includes('x-ray') || sentenceLower.includes('scan') ||
          sentenceLower.includes('blood work') || sentenceLower.includes('urine') ||
          sentenceLower.includes('cbc') || sentenceLower.includes('glucose') ||
          sentenceLower.includes('hba1c') || sentenceLower.includes('creatinine')) {
        result.labTests.push(sentence.trim());
      }
      
      // Known Allergens
      if (sentenceLower.includes('allerg') || sentenceLower.includes('adverse') ||
          sentenceLower.includes('reaction') || sentenceLower.includes('intolerance') ||
          sentenceLower.includes('hypersensitivity')) {
        result.allergies.push(sentence.trim());
      }
      
      // Risk Factors
      if (sentenceLower.includes('smoking') || sentenceLower.includes('alcohol') ||
          sentenceLower.includes('family history') || sentenceLower.includes('obesity') ||
          sentenceLower.includes('sedentary') || sentenceLower.includes('risk factor')) {
        result.riskFactors.push(sentence.trim());
      }
      
      // Comorbidities
      if (sentenceLower.includes('diabetes') || sentenceLower.includes('hypertension') ||
          sentenceLower.includes('cardiac') || sentenceLower.includes('renal') ||
          sentenceLower.includes('hepatic') || sentenceLower.includes('copd') ||
          sentenceLower.includes('asthma') || sentenceLower.includes('comorbid')) {
        result.comorbidities.push(sentence.trim());
      }
    });

    return result;
  };

  if (loading) {
    return (
      <div className="medical-summary-overlay">
        <div className="medical-summary-modal">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading medical summary...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="medical-summary-overlay">
        <div className="medical-summary-modal">
          <div className="error-message">
            <h3>Error</h3>
            <p>{error}</p>
            <button onClick={onClose} className="btn-close">Close</button>
          </div>
        </div>
      </div>
    );
  }

  if (selectedConsultation) {
    return (
      <div className="medical-summary-overlay">
        <div className="medical-summary-modal consultation-detail">
          <div className="modal-header">
            <h2>Consultation Details</h2>
            <button onClick={() => setSelectedConsultation(null)} className="btn-back">
              ← Back to Summary
            </button>
            <button onClick={onClose} className="btn-close">×</button>
          </div>
          
          <div className="consultation-content">
            <div className="consultation-info">
              <h3>Date: {formatDate(selectedConsultation.date)}</h3>
              <p><strong>Doctor:</strong> {selectedConsultation.doctor.name}</p>
              <p><strong>Specialization:</strong> {selectedConsultation.doctor.specialization}</p>
            </div>
            
            <div className="consultation-notes">
              <h4>Clinical Notes</h4>
              <div className="notes-content">
                {selectedConsultation.medical_structure ? (
                  <div className="structured-notes">
                    {selectedConsultation.medical_structure.chief_complaint && (
                      <div className="note-section">
                        <h5>Chief Complaint</h5>
                        <p>{selectedConsultation.medical_structure.chief_complaint}</p>
                      </div>
                    )}
                    {selectedConsultation.medical_structure.physical_examination && (
                      <div className="note-section">
                        <h5>Physical Examination</h5>
                        <p>{selectedConsultation.medical_structure.physical_examination}</p>
                      </div>
                    )}
                    {selectedConsultation.medical_structure.assessment && (
                      <div className="note-section">
                        <h5>Assessment</h5>
                        <p>{selectedConsultation.medical_structure.assessment}</p>
                      </div>
                    )}
                    {selectedConsultation.medical_structure.plan && (
                      <div className="note-section">
                        <h5>Plan</h5>
                        <p>{selectedConsultation.medical_structure.plan}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p>{selectedConsultation.notes}</p>
                )}
              </div>
            </div>
            
            {selectedConsultation.prescription_items && selectedConsultation.prescription_items.length > 0 && (
              <div className="prescriptions-section">
                <h4>Prescriptions</h4>
                <div className="prescriptions-list">
                  {selectedConsultation.prescription_items.map((prescription, index) => (
                    <div key={index} className="prescription-item">
                      <div className="prescription-header">
                        <h5>{prescription.medicine_name}</h5>
                        <span className="dosage">{prescription.dosage}</span>
                      </div>
                      <div className="prescription-details">
                        <p><strong>Duration:</strong> {prescription.duration_days} days</p>
                        <div className="timing">
                          <strong>Timing:</strong>
                          {prescription.timing_morning && <span className="timing-badge">Morning</span>}
                          {prescription.timing_afternoon && <span className="timing-badge">Afternoon</span>}
                          {prescription.timing_evening && <span className="timing-badge">Evening</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="medical-summary-overlay">
      <div className="medical-summary-modal prescription-format">
        <div className="prescription-header">
          <div className="clinic-info">
            <h1>📋 MEDICAL SUMMARY</h1>
            <p className="clinic-subtitle">Comprehensive Patient History</p>
          </div>
          <button onClick={onClose} className="btn-close">×</button>
        </div>
        
        {/* Patient Information - Prescription Style */}
        <div className="patient-prescription-info">
          <div className="patient-details-row">
            <div className="detail-item">
              <strong>Patient Name:</strong> {summary.patient_info.name}
            </div>
            <div className="detail-item">
              <strong>Age:</strong> {summary.patient_info.age} years
            </div>
            <div className="detail-item">
              <strong>Phone:</strong> {summary.patient_info.phone_number}
            </div>
            <div className="detail-item">
              <strong>Total Visits:</strong> {summary.total_consultations}
            </div>
          </div>
          <div className="summary-date">
            <strong>Summary Generated:</strong> {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </div>
        </div>

        {/* Medical Summary Table */}
        <div className="prescription-section">
          <div className="section-header">
            <h3>📋 COMPLETE MEDICAL SUMMARY</h3>
            <div className="section-line"></div>
          </div>
          
          <div className="medical-table-container">
            <table className="medical-summary-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Physician</th>
                  <th>Chief Complaint (CC)</th>
                  <th>Clinical Diagnosis</th>
                  <th>Pharmacotherapy</th>
                  <th>Vital Parameters</th>
                  <th>Laboratory Studies</th>
                  <th>Known Allergens</th>
                  <th>Risk Factors</th>
                  <th>Comorbidities</th>
                  <th>Source Note</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_consultations.map((consultation, index) => {
                  const extractedInfo = extractInfoFromNotes(consultation.notes_preview || consultation.notes || '');
                  return (
                    <tr key={index}>
                      <td>{formatDate(consultation.date)}</td>
                      <td><span className="physician-name">Dr. {consultation.doctor_name}</span></td>
                      <td>
                        {extractedInfo.complaints.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.complaints.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item cc-item">{item}</div>
                            ))}
                            {extractedInfo.complaints.length > 2 && <div className="more-items">+{extractedInfo.complaints.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">Not documented</span>}
                      </td>
                      <td>
                        {extractedInfo.diagnoses.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.diagnoses.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item diagnosis-item">{item}</div>
                            ))}
                            {extractedInfo.diagnoses.length > 2 && <div className="more-items">+{extractedInfo.diagnoses.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">Pending</span>}
                      </td>
                      <td>
                        {extractedInfo.medications.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.medications.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item medication-item">{item}</div>
                            ))}
                            {extractedInfo.medications.length > 2 && <div className="more-items">+{extractedInfo.medications.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">None prescribed</span>}
                      </td>
                      <td>
                        {extractedInfo.vitals.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.vitals.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item vital-item">{item}</div>
                            ))}
                            {extractedInfo.vitals.length > 2 && <div className="more-items">+{extractedInfo.vitals.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">Not recorded</span>}
                      </td>
                      <td>
                        {extractedInfo.labTests.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.labTests.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item lab-item">{item}</div>
                            ))}
                            {extractedInfo.labTests.length > 2 && <div className="more-items">+{extractedInfo.labTests.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">None ordered</span>}
                      </td>
                      <td>
                        {extractedInfo.allergies.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.allergies.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item allergy-alert">{item}</div>
                            ))}
                            {extractedInfo.allergies.length > 2 && <div className="more-items">+{extractedInfo.allergies.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">NKDA</span>}
                      </td>
                      <td>
                        {extractedInfo.riskFactors.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.riskFactors.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item risk-item">{item}</div>
                            ))}
                            {extractedInfo.riskFactors.length > 2 && <div className="more-items">+{extractedInfo.riskFactors.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">None identified</span>}
                      </td>
                      <td>
                        {extractedInfo.comorbidities.length > 0 ? (
                          <div className="info-cell">
                            {extractedInfo.comorbidities.slice(0, 2).map((item, i) => (
                              <div key={i} className="info-item comorbidity-item">{item}</div>
                            ))}
                            {extractedInfo.comorbidities.length > 2 && <div className="more-items">+{extractedInfo.comorbidities.length - 2} more</div>}
                          </div>
                        ) : <span className="no-data">None documented</span>}
                      </td>
                      <td>
                        <button 
                          onClick={() => fetchConsultationDetail(consultation.id)}
                          className="view-note-btn"
                          title="Access Complete Clinical Documentation"
                        >
                          📋 Source Note
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer - Prescription Style */}
        <div className="prescription-footer">
          <div className="footer-info">
            <p><strong>Medical Summary System</strong> | Generated using AI-powered analysis</p>
            <p><small>This summary is for medical reference only. Please consult with healthcare providers for medical decisions.</small></p>
          </div>
          <div className="footer-signature">
            <div className="signature-line"></div>
            <p>Digital Medical Summary</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MedicalSummary;