import React, { useState, useEffect } from 'react';
import './SmartQueueDashboard.css';

const SmartQueueDashboard = ({ user, token }) => {
  const [queueData, setQueueData] = useState(null);
  const [clinicOverview, setClinicOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueueData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchQueueData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchQueueData = async () => {
    try {
      // Fetch real-time queue data
      const queueResponse = await fetch('/api/queue/realtime/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (queueResponse.ok) {
        const queueData = await queueResponse.json();
        setQueueData(queueData);
      }

      // Fetch clinic overview
      const overviewResponse = await fetch('/api/queue/clinic-overview/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (overviewResponse.ok) {
        const overviewData = await overviewResponse.json();
        setClinicOverview(overviewData);
      }
      
    } catch (error) {
      console.error('Failed to fetch queue data:', error);
    } finally {
      setLoading(false);
    }
  };

  const activateEarlyArrival = async (tokenId) => {
    try {
      const response = await fetch('/api/queue/early-arrival/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token_id: tokenId })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        fetchQueueData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to activate early arrival:', error);
    }
  };

  const runSmartAction = async (action) => {
    try {
      const response = await fetch('/api/queue/actions/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(result.message || 'Action completed successfully');
        fetchQueueData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to run smart action:', error);
    }
  };

  if (loading) {
    return <div className="smart-queue-loading">Loading queue data...</div>;
  }

  return (
    <div className="smart-queue-dashboard">
      <div className="dashboard-header">
        <h2>Smart Queue Management</h2>
        <div className="action-buttons">
          <button 
            onClick={() => runSmartAction('activate_early_arrivals')}
            className="action-btn primary"
          >
            Activate Early Arrivals
          </button>
          <button 
            onClick={() => runSmartAction('detect_early_slots')}
            className="action-btn secondary"
          >
            Detect Early Slots
          </button>
          <button onClick={fetchQueueData} className="refresh-btn">
            Refresh
          </button>
        </div>
      </div>

      {/* Real-time Queue Status */}
      {queueData && (
        <div className="queue-status-section">
          <h3>Current Queue Status</h3>
          <div className="queue-info">
            <div className="queue-stat">
              <span className="label">Total Waiting:</span>
              <span className="value">{queueData.queue_status.total_waiting}</span>
            </div>
            <div className="queue-stat">
              <span className="label">Current Time:</span>
              <span className="value">{queueData.queue_status.current_time}</span>
            </div>
            <div className="queue-stat">
              <span className="label">Can Accept Walk-ins:</span>
              <span className={`value ${queueData.queue_status.can_accept_walkins ? 'yes' : 'no'}`}>
                {queueData.queue_status.can_accept_walkins ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Current Patient */}
          {queueData.queue_status.current_patient && (
            <div className="current-patient">
              <h4>Currently in Consultation</h4>
              <div className="patient-info">
                <span>Token: {queueData.queue_status.current_patient.token_number}</span>
                <span>Time: {queueData.queue_status.current_patient.appointment_time}</span>
                <span>Duration: {queueData.queue_status.current_patient.consultation_duration} min</span>
              </div>
            </div>
          )}

          {/* Next Patients */}
          <div className="next-patients">
            <h4>Next Patients</h4>
            {queueData.queue_status.next_patients.map((patient, index) => (
              <div key={index} className="patient-card">
                <div className="patient-details">
                  <span className="position">#{patient.position}</span>
                  <span className="token">Token: {patient.token_number}</span>
                  <span className="time">{patient.appointment_time}</span>
                  <span className="wait">Wait: {patient.predicted_wait_minutes} min</span>
                  <span className={`status ${patient.status}`}>{patient.status}</span>
                </div>
                {patient.can_arrive_early && (
                  <button 
                    onClick={() => activateEarlyArrival(patient.token_id)}
                    className="early-arrival-btn"
                  >
                    Activate Early Arrival
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clinic Overview */}
      {clinicOverview && (
        <div className="clinic-overview-section">
          <h3>Clinic Overview</h3>
          <div className="overview-stats">
            <div className="stat-card">
              <h4>Today's Patients</h4>
              <span className="stat-value">{clinicOverview.clinic_overview.total_patients_today}</span>
            </div>
            <div className="stat-card">
              <h4>Currently Waiting</h4>
              <span className="stat-value">{clinicOverview.clinic_overview.total_waiting}</span>
            </div>
            <div className="stat-card">
              <h4>Completed Today</h4>
              <span className="stat-value">{clinicOverview.clinic_overview.total_completed}</span>
            </div>
          </div>

          {/* Doctor Status */}
          <div className="doctors-status">
            <h4>Doctors Status</h4>
            {clinicOverview.clinic_overview.doctors_status.map((doctor, index) => (
              <div key={index} className="doctor-card">
                <div className="doctor-info">
                  <h5>{doctor.doctor_name}</h5>
                  <span className="specialization">{doctor.specialization}</span>
                </div>
                <div className="doctor-stats">
                  <span>Today: {doctor.patients_today}</span>
                  <span>Waiting: {doctor.current_waiting}</span>
                  <span>Completed: {doctor.completed_today}</span>
                  <span className={`status ${doctor.status}`}>{doctor.status}</span>
                  {doctor.can_accept_walkins && (
                    <span className="walkin-available">Walk-ins OK</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Early Opportunities */}
          {clinicOverview.early_opportunities && clinicOverview.early_opportunities.length > 0 && (
            <div className="early-opportunities">
              <h4>Early Slot Opportunities</h4>
              {clinicOverview.early_opportunities.map((opportunity, index) => (
                <div key={index} className="opportunity-card">
                  <span>Dr. {opportunity.doctor_name}</span>
                  <span>Slot: {opportunity.original_time}</span>
                  <span>Available: {opportunity.minutes_early} min early</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Analytics */}
      {queueData && queueData.analytics && (
        <div className="analytics-section">
          <h3>Today's Analytics</h3>
          <div className="analytics-stats">
            <div className="stat">
              <span>Completed Consultations:</span>
              <strong>{queueData.analytics.total_completed}</strong>
            </div>
            <div className="stat">
              <span>Average Wait Time:</span>
              <strong>{queueData.analytics.avg_wait_minutes} minutes</strong>
            </div>
          </div>

          {/* Doctor Performance */}
          {Object.keys(queueData.analytics.doctor_performance).length > 0 && (
            <div className="doctor-performance">
              <h4>Doctor Performance</h4>
              {Object.entries(queueData.analytics.doctor_performance).map(([doctorName, performance]) => (
                <div key={doctorName} className="performance-card">
                  <span className="doctor-name">{doctorName}</span>
                  <span>Patients: {performance.total_patients}</span>
                  <span>Avg Wait: {performance.avg_wait_time} min</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="dashboard-footer">
        <span>Last updated: {queueData ? new Date(queueData.last_updated).toLocaleTimeString() : 'Never'}</span>
      </div>
    </div>
  );
};

export default SmartQueueDashboard;