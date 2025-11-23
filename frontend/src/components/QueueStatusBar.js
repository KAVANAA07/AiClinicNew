import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Simple SVG icons
const Activity = () => <svg style={{width: '16px', height: '16px'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/></svg>;
const Clock = () => <svg style={{width: '16px', height: '16px'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>;
const Users = () => <svg style={{width: '16px', height: '16px'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
const CheckCircle = () => <svg style={{width: '16px', height: '16px'}} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></svg>;

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

const QueueStatusBar = ({ doctorId }) => {
  const [queueStats, setQueueStats] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    pending: 0,
    avgWaitTime: 0
  });
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState('');

  const fetchQueueStats = useCallback(async () => {
    try {
      const response = await apiClient.get(`/doctor-flow/${doctorId}/`);
      if (response.data.success) {
        setQueueStats({
          total: response.data.flow_analysis.total_appointments,
          completed: response.data.flow_analysis.completed,
          inProgress: response.data.flow_analysis.in_progress,
          pending: response.data.flow_analysis.pending,
          avgWaitTime: Math.round(response.data.flow_analysis.average_delay)
        });
        setIsLive(true);
        setError('');
      }
    } catch (error) {
      console.error('Error fetching queue stats:', error);
      setIsLive(false);
      setError('Unable to fetch queue stats');
    }
  }, [doctorId]);

  useEffect(() => {
    if (doctorId) {
      fetchQueueStats();
      const interval = setInterval(fetchQueueStats, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [doctorId, fetchQueueStats]);

  const completionRate = queueStats.total > 0 ? (queueStats.completed / queueStats.total) * 100 : 0;

  if (error) {
    return (
      <div className="card" style={{padding: '15px', marginBottom: '15px', textAlign: 'center', color: 'var(--error-color)'}}>
        {error}
      </div>
    );
  }

  return (
    <div className="card" style={{padding: '15px', marginBottom: '15px', background: 'white', border: '1px solid var(--light-gray)'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px'}}>
        <h3 style={{margin: 0, fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-color)'}}>Queue Status</h3>
        <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isLive ? '#4caf50' : '#f44336',
            animation: isLive ? 'pulse 2s infinite' : 'none'
          }}></div>
          <span style={{fontSize: '0.8rem', color: 'var(--medium-gray)'}}>{isLive ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{marginBottom: '15px'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--dark-gray)', marginBottom: '5px'}}>
          <span>Progress Today</span>
          <span>{Math.round(completionRate)}%</span>
        </div>
        <div style={{width: '100%', height: '8px', backgroundColor: 'var(--light-gray)', borderRadius: '4px', overflow: 'hidden'}}>
          <div style={{
            height: '100%',
            backgroundColor: 'var(--primary-color)',
            width: `${completionRate}%`,
            transition: 'width 0.5s ease',
            borderRadius: '4px'
          }}></div>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px'}}>
        <div style={{textAlign: 'center'}}>
          <div style={{display: 'flex', justifyContent: 'center', marginBottom: '5px', color: 'var(--primary-color)'}}>
            <Users />
          </div>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>{queueStats.total}</p>
          <p style={{margin: 0, fontSize: '0.7rem', color: 'var(--medium-gray)'}}>Total</p>
        </div>
        
        <div style={{textAlign: 'center'}}>
          <div style={{display: 'flex', justifyContent: 'center', marginBottom: '5px', color: '#4caf50'}}>
            <CheckCircle />
          </div>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>{queueStats.completed}</p>
          <p style={{margin: 0, fontSize: '0.7rem', color: 'var(--medium-gray)'}}>Done</p>
        </div>
        
        <div style={{textAlign: 'center'}}>
          <div style={{display: 'flex', justifyContent: 'center', marginBottom: '5px', color: '#ff9800'}}>
            <Activity />
          </div>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>{queueStats.inProgress}</p>
          <p style={{margin: 0, fontSize: '0.7rem', color: 'var(--medium-gray)'}}>Active</p>
        </div>
        
        <div style={{textAlign: 'center'}}>
          <div style={{display: 'flex', justifyContent: 'center', marginBottom: '5px', color: 'var(--dark-gray)'}}>
            <Clock />
          </div>
          <p style={{margin: 0, fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-color)'}}>{queueStats.avgWaitTime}m</p>
          <p style={{margin: 0, fontSize: '0.7rem', color: 'var(--medium-gray)'}}>Avg Wait</p>
        </div>
      </div>
    </div>
  );
};

export default QueueStatusBar;