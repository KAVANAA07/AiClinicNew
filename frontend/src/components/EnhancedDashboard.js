import React, { useState, useEffect } from 'react';
import './EnhancedDashboard.css';

const EnhancedDashboard = ({ user, token }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
    fetchInsights();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/dashboard/realtime/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch('/api/insights/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setInsights(data);
      }
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    }
  };

  const optimizeQueue = async (doctorId) => {
    try {
      const response = await fetch('/api/queue/smart/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'optimize',
          doctor_id: doctorId
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Queue optimized! ${result.changes_made} changes made.`);
        fetchDashboardData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to optimize queue:', error);
    }
  };

  const sendBulkMessage = async () => {
    const message = prompt('Enter message to send to all waiting patients:');
    if (!message) return;

    try {
      const response = await fetch('/api/communication/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'bulk_announcement',
          message: message,
          target_group: 'waiting'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Message sent to ${result.messages_sent} patients.`);
      }
    } catch (error) {
      console.error('Failed to send bulk message:', error);
    }
  };

  if (loading) {
    return (
      <div className="enhanced-dashboard loading">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  const metrics = dashboardData?.clinic_metrics || {};
  const predictions = dashboardData?.flow_predictions || [];

  return (
    <div className="enhanced-dashboard">
      <div className="dashboard-header">
        <h2>Enhanced Clinic Dashboard</h2>
        <div className="dashboard-tabs">
          <button 
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={activeTab === 'queue' ? 'active' : ''}
            onClick={() => setActiveTab('queue')}
          >
            Queue Management
          </button>
          <button 
            className={activeTab === 'insights' ? 'active' : ''}
            onClick={() => setActiveTab('insights')}
          >
            Insights
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className="overview-tab">
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Today's Patients</h3>
              <div className="metric-value">{metrics.total_patients_today || 0}</div>
            </div>
            <div className="metric-card">
              <h3>Waiting</h3>
              <div className="metric-value waiting">{metrics.waiting_patients || 0}</div>
            </div>
            <div className="metric-card">
              <h3>In Consultation</h3>
              <div className="metric-value active">{metrics.in_consultation || 0}</div>
            </div>
            <div className="metric-card">
              <h3>Completed</h3>
              <div className="metric-value completed">{metrics.completed_today || 0}</div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-container">
              <h3>Hourly Patient Distribution</h3>
              <div className="hourly-chart">
                {metrics.hourly_distribution?.map((hour, index) => (
                  <div key={index} className="hour-bar">
                    <div 
                      className="bar" 
                      style={{ height: `${(hour.patients / 10) * 100}%` }}
                    ></div>
                    <span className="hour-label">{hour.hour}</span>
                    <span className="patient-count">{hour.patients}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="predictions-container">
              <h3>Patient Flow Predictions</h3>
              {predictions.map((prediction, index) => (
                <div key={index} className="prediction-item">
                  <span className="time">{prediction.hour}</span>
                  <span className="predicted-count">{prediction.predicted_patients} patients</span>
                  <span className={`confidence ${prediction.confidence}`}>
                    {prediction.confidence} confidence
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'queue' && (
        <div className="queue-tab">
          <div className="queue-actions">
            <button onClick={sendBulkMessage} className="action-btn">
              Send Bulk Message
            </button>
          </div>

          <div className="doctor-queues">
            <h3>Doctor Queue Status</h3>
            {metrics.doctor_stats?.map((doctor, index) => (
              <div key={index} className="doctor-queue-card">
                <div className="doctor-info">
                  <h4>{doctor.doctor_name}</h4>
                  <span className="specialization">{doctor.specialization}</span>
                </div>
                <div className="queue-metrics">
                  <div className="queue-length">
                    Queue: <strong>{doctor.queue_length}</strong>
                  </div>
                  <div className="predicted-wait">
                    Est. Wait: <strong>{doctor.predicted_wait_time || 'N/A'} min</strong>
                  </div>
                  <div className={`status ${doctor.status}`}>
                    {doctor.status}
                  </div>
                </div>
                <div className="queue-actions">
                  <button 
                    onClick={() => optimizeQueue(doctor.doctor_id)}
                    className="optimize-btn"
                    disabled={doctor.queue_length < 2}
                  >
                    Optimize Queue
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="insights-tab">
          {insights?.bottlenecks?.length > 0 && (
            <div className="bottlenecks-section">
              <h3>⚠️ Bottlenecks Detected</h3>
              {insights.bottlenecks.map((bottleneck, index) => (
                <div key={index} className={`bottleneck-card ${bottleneck.severity}`}>
                  <h4>{bottleneck.doctor_name}</h4>
                  <p>{bottleneck.issue || `Queue length: ${bottleneck.queue_length}`}</p>
                  <p className="recommendation">{bottleneck.recommendation}</p>
                </div>
              ))}
            </div>
          )}

          {insights?.weekly_performance && (
            <div className="performance-section">
              <h3>Weekly Performance Summary</h3>
              <div className="performance-metrics">
                <div className="perf-metric">
                  <span>Completion Rate</span>
                  <strong>{insights.weekly_performance.summary.completion_rate.toFixed(1)}%</strong>
                </div>
                <div className="perf-metric">
                  <span>Avg Wait Time</span>
                  <strong>{insights.weekly_performance.summary.avg_waiting_time_minutes} min</strong>
                </div>
                <div className="perf-metric">
                  <span>Patient Satisfaction</span>
                  <strong>{insights.weekly_performance.summary.patient_satisfaction_score}/100</strong>
                </div>
              </div>

              {insights.weekly_performance.recommendations?.length > 0 && (
                <div className="recommendations">
                  <h4>Recommendations</h4>
                  {insights.weekly_performance.recommendations.map((rec, index) => (
                    <div key={index} className={`recommendation ${rec.priority}`}>
                      <strong>{rec.message}</strong>
                      <p>{rec.action}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="dashboard-footer">
        <span>Last updated: {new Date(dashboardData?.last_updated).toLocaleTimeString()}</span>
        <button onClick={fetchDashboardData} className="refresh-btn">
          Refresh
        </button>
      </div>
    </div>
  );
};

export default EnhancedDashboard;