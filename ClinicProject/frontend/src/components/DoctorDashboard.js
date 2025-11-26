import React, { useState, useEffect } from 'react';
import ConsultationForm from './ConsultationForm';
import './DoctorDashboard.css';

const DoctorDashboard = () => {
  const [tokens, setTokens] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showConsultationForm, setShowConsultationForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTokens();
  }, []);

  const fetchTokens = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/tokens/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTokens(data);
      }
    } catch (error) {
      console.error('Error fetching tokens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartConsultation = (token) => {
    setSelectedPatient(token.patient);
    setShowConsultationForm(true);
  };

  const handleConsultationSubmit = async (consultationData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/consultations/create/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
      });

      if (response.ok) {
        alert('Consultation completed successfully!');
        setShowConsultationForm(false);
        setSelectedPatient(null);
        fetchTokens(); // Refresh the token list
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || 'Failed to create consultation'}`);
      }
    } catch (error) {
      console.error('Error creating consultation:', error);
      alert('Error creating consultation');
    }
  };

  const handleCancelConsultation = () => {
    setShowConsultationForm(false);
    setSelectedPatient(null);
  };

  const updateTokenStatus = async (tokenId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/tokens/${tokenId}/update_status/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        fetchTokens(); // Refresh the list
      }
    } catch (error) {
      console.error('Error updating token status:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (showConsultationForm && selectedPatient) {
    return (
      <ConsultationForm
        patient={selectedPatient}
        onSubmit={handleConsultationSubmit}
        onCancel={handleCancelConsultation}
      />
    );
  }

  return (
    <div className="doctor-dashboard">
      <div className="dashboard-header">
        <h1>Doctor Dashboard</h1>
        <p>Manage your patient queue and consultations</p>
      </div>

      <div className="tokens-section">
        <h2>Today's Patients ({tokens.length})</h2>
        
        {tokens.length === 0 ? (
          <div className="no-tokens">
            <p>No patients in queue today</p>
          </div>
        ) : (
          <div className="tokens-grid">
            {tokens.map((token) => (
              <div key={token.id} className={`token-card ${token.status}`}>
                <div className="token-header">
                  <h3>{token.patient.name}</h3>
                  <span className={`status-badge ${token.status}`}>
                    {token.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                
                <div className="token-details">
                  <p><strong>Token:</strong> {token.token_number || 'Walk-in'}</p>
                  <p><strong>Age:</strong> {token.patient.age}</p>
                  <p><strong>Phone:</strong> {token.patient.phone_number}</p>
                  {token.appointment_time && (
                    <p><strong>Time:</strong> {token.appointment_time}</p>
                  )}
                </div>

                <div className="token-actions">
                  {token.status === 'waiting' && (
                    <button
                      onClick={() => updateTokenStatus(token.id, 'in_consultancy')}
                      className="action-btn start-btn"
                    >
                      Start Consultation
                    </button>
                  )}
                  
                  {token.status === 'confirmed' && (
                    <button
                      onClick={() => updateTokenStatus(token.id, 'in_consultancy')}
                      className="action-btn start-btn"
                    >
                      Start Consultation
                    </button>
                  )}
                  
                  {token.status === 'in_consultancy' && (
                    <button
                      onClick={() => handleStartConsultation(token)}
                      className="action-btn complete-btn"
                    >
                      Complete Consultation
                    </button>
                  )}
                  
                  {token.status !== 'completed' && token.status !== 'cancelled' && (
                    <button
                      onClick={() => updateTokenStatus(token.id, 'skipped')}
                      className="action-btn skip-btn"
                    >
                      Skip
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DoctorDashboard;