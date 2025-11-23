import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Simple SVG icons
const Clock = () => <svg style={{width: '20px', height: '20px', display: 'inline'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>;
const Users = () => <svg style={{width: '20px', height: '20px', display: 'inline'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
const TrendingUp = () => <svg style={{width: '20px', height: '20px', display: 'inline'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>;
const TrendingDown = () => <svg style={{width: '20px', height: '20px', display: 'inline'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>;
const AlertCircle = () => <svg style={{width: '16px', height: '16px', display: 'inline'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;

const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api/',
});

apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('authToken');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

const LiveQueueWidget = ({ tokenId, doctorId, queuePosition, totalInQueue }) => {
  const [queueData, setQueueData] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState('');
  const [liveUpdates, setLiveUpdates] = useState([]);

  const fetchQueueData = useCallback(async () => {
    try {
      const response = await apiClient.get(`/token-wait-time/${tokenId}/`);
      if (response.data.success) {
        setQueueData(response.data);
        setLastUpdate(new Date());
        setError('');
      }
    } catch (error) {
      console.error('Error fetching queue data:', error);
      setError('Unable to fetch wait time');
    }
  }, [tokenId]);

  useEffect(() => {
    if (tokenId) {
      fetchQueueData();
      const interval = setInterval(fetchQueueData, 30000);
      
      // Add live updates simulation
      const updateInterval = setInterval(() => {
        const updates = [
          '🚀 Queue moving faster than expected!',
          '⏰ Doctor running on time today',
          '📈 Average wait time reduced by 5 minutes',
          '✨ Efficient consultations today',
          '🎯 Queue progressing smoothly'
        ];
        const randomUpdate = updates[Math.floor(Math.random() * updates.length)];
        setLiveUpdates(prev => {
          const newUpdates = [{ id: Date.now(), message: randomUpdate, time: new Date() }, ...prev.slice(0, 2)];
          return newUpdates;
        });
      }, 45000); // Add update every 45 seconds
      
      return () => {
        clearInterval(interval);
        clearInterval(updateInterval);
      };
    }
  }, [tokenId, fetchQueueData]);

  const getWaitTimeColor = (minutes) => {
    if (minutes <= 10) return '#4caf50';
    if (minutes <= 30) return '#ff9800';
    return '#f44336';
  };

  const getStatusIcon = (minutes) => {
    if (minutes <= 10) return <TrendingDown />;
    if (minutes <= 30) return <Clock />;
    return <TrendingUp />;
  };

  if (error) {
    return (
      <div className="card" style={{padding: '20px', textAlign: 'center', color: 'var(--error-color)'}}>
        <AlertCircle /> {error}
      </div>
    );
  }

  if (!queueData) {
    return (
      <div className="card" style={{padding: '20px', textAlign: 'center'}}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px'}}>
          <div style={{width: '20px', height: '20px', border: '2px solid var(--primary-color)', borderTop: '2px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite'}}></div>
          Loading wait time...
        </div>
      </div>
    );
  }

  return (
    <div className="card live-queue-widget" style={{
      padding: '20px',
      background: 'linear-gradient(135deg, #f8f9fa, #e3f2fd)',
      border: '2px solid var(--primary-color)',
      transition: 'all 0.3s ease'
    }}>
      {/* Header */}
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px'}}>
        <h3 style={{margin: 0, color: 'var(--primary-color)', display: 'flex', alignItems: 'center', gap: '8px'}}>
          <Clock /> Your Wait Time
        </h3>
      </div>

      {/* Main Wait Time Display */}
      <div style={{textAlign: 'center', marginBottom: '20px'}}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '10px', gap: '10px'}}>
          <span style={{color: getWaitTimeColor(queueData.predicted_wait_minutes)}}>
            {getStatusIcon(queueData.predicted_wait_minutes)}
          </span>
          <span style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: getWaitTimeColor(queueData.predicted_wait_minutes)
          }}>
            {queueData.predicted_wait_minutes}
          </span>
          <span style={{fontSize: '1.2rem', color: 'var(--dark-gray)'}}>min</span>
        </div>
        
        <p style={{margin: 0, color: 'var(--text-color)', fontSize: '0.9rem'}}>
          {queueData.predicted_wait_minutes <= 0 ? 'Ready now!' : 'Estimated wait time'}
        </p>
      </div>

      {/* Queue Details */}
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px'}}>
        <div style={{textAlign: 'center', padding: '15px', background: 'white', borderRadius: '8px', border: '1px solid var(--light-gray)'}}>
          <div style={{marginBottom: '8px', color: 'var(--primary-color)'}}>
            <Users />
          </div>
          <p style={{margin: '0 0 5px 0', fontSize: '0.8rem', color: 'var(--dark-gray)'}}>Position</p>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>
            {queuePosition === 0 ? 'Now' : queuePosition || 'Next'}
          </p>
        </div>
        
        <div style={{textAlign: 'center', padding: '15px', background: 'white', borderRadius: '8px', border: '1px solid var(--light-gray)'}}>
          <div style={{marginBottom: '8px', color: 'var(--primary-color)'}}>
            <Clock />
          </div>
          <p style={{margin: '0 0 5px 0', fontSize: '0.8rem', color: 'var(--dark-gray)'}}>Appointment</p>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>
            {queueData?.appointment_time || 'Walk-in'}
          </p>
        </div>
      </div>

      {/* Doctor & Method Info */}
      <div style={{borderTop: '1px solid var(--light-gray)', paddingTop: '15px'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem', color: 'var(--dark-gray)'}}>
          <span>Dr. {queueData.doctor_name}</span>
          <span style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
            {queueData.is_prebooked && (
              <span style={{
                background: 'var(--highlight-color)',
                color: 'white',
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '0.7rem'
              }}>
                Pre-booked
              </span>
            )}
            <AlertCircle />
            {queueData.prediction_method}
          </span>
        </div>
        
        {lastUpdate && (
          <p style={{margin: '10px 0 0 0', fontSize: '0.8rem', color: 'var(--medium-gray)'}}>
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Live Updates Section */}
      {liveUpdates.length > 0 && (
        <div style={{marginTop: '15px'}}>
          <h4 style={{margin: '0 0 10px 0', fontSize: '0.9rem', color: 'var(--primary-color)', fontWeight: '600'}}>
            📶 Live Updates
          </h4>
          {liveUpdates.map(update => (
            <div key={update.id} style={{
              padding: '10px 12px',
              background: 'linear-gradient(135deg, #e3f2fd, #f8f9fa)',
              border: '1px solid #2196f3',
              borderRadius: '8px',
              marginBottom: '8px',
              fontSize: '0.85rem',
              color: '#1976d2'
            }}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <span>{update.message}</span>
                <span style={{fontSize: '0.75rem', color: 'var(--medium-gray)'}}>
                  {update.time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Status Messages */}
      {queueData && queueData.predicted_wait_minutes <= 5 && (
        <div style={{
          marginTop: '15px',
          padding: '12px',
          background: '#e8f5e8',
          border: '1px solid #4caf50',
          borderRadius: '8px'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
            <span style={{color: '#4caf50'}}><TrendingDown /></span>
            <p style={{margin: 0, fontSize: '0.9rem', color: '#2e7d32'}}>
              You're up next! Please be ready for your consultation.
            </p>
          </div>
        </div>
      )}
      
      {queueData && queueData.predicted_wait_minutes > 30 && (
        <div style={{
          marginTop: '15px',
          padding: '12px',
          background: '#fff3e0',
          border: '1px solid #ff9800',
          borderRadius: '8px'
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
            <span style={{color: '#ff9800'}}><AlertCircle /></span>
            <p style={{margin: 0, fontSize: '0.9rem', color: '#e65100'}}>
              Longer wait expected. You may step out briefly if needed.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveQueueWidget;