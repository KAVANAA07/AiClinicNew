# Home Page Waiting Time Integration Guide

## 🎯 **What You Get**

Your home page will now display:
- **Real-time waiting times** for all clinics and doctors
- **AI predictions** based on actual clinic data
- **Queue positions** and expected consultation times
- **Next available slots** for immediate booking
- **Personal waiting info** for logged-in patients

## 📊 **API Endpoints Created**

### 1. Public Clinic Dashboard
```http
GET /api/waiting-time/dashboard/
```
**Response:**
```json
{
  "success": true,
  "clinics": [
    {
      "clinic_id": 1,
      "clinic_name": "City Medical Center",
      "total_queue_length": 12,
      "average_waiting_time_minutes": 35,
      "doctors": [
        {
          "doctor_id": 1,
          "doctor_name": "Dr. Smith",
          "specialization": "Cardiology",
          "current_queue_length": 4,
          "predicted_waiting_time_minutes": 45,
          "actual_avg_waiting_time_today": 38,
          "next_available_slot": {
            "display_text": "Today at 3:30 PM",
            "minutes_from_now": 120
          },
          "expected_consultation_start": [
            {"token_id": 123, "expected_start": "2:45 PM", "minutes_from_now": 15},
            {"token_id": 124, "expected_start": "3:00 PM", "minutes_from_now": 30}
          ],
          "status": "available"
        }
      ]
    }
  ]
}
```

### 2. My Token Waiting Time (Authenticated)
```http
GET /api/waiting-time/my-token/
Authorization: Token <user_token>
```
**Response:**
```json
{
  "token_number": "C-3",
  "doctor_name": "Dr. Smith",
  "appointment_time": "3:30 PM",
  "queue_position": 3,
  "predicted_waiting_time_minutes": 25,
  "expected_consultation_start": {
    "expected_start": "3:45 PM",
    "minutes_from_now": 35
  },
  "appointment_delay_minutes": 15,
  "message": "You're #3 in queue. Expected consultation: 3:45 PM. Running 15 minutes behind schedule."
}
```

## 🖥️ **Frontend Integration Examples**

### React Component for Home Page
```jsx
import React, { useState, useEffect } from 'react';

const WaitingTimeDashboard = () => {
  const [clinics, setClinics] = useState([]);
  const [myToken, setMyToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load clinic waiting times (public)
    fetch('/api/waiting-time/dashboard/')
      .then(response => response.json())
      .then(data => {
        setClinics(data.clinics || []);
        setLoading(false);
      });

    // Load my token info if logged in
    const token = localStorage.getItem('authToken');
    if (token) {
      fetch('/api/waiting-time/my-token/', {
        headers: { 'Authorization': `Token ${token}` }
      })
        .then(response => response.json())
        .then(data => setMyToken(data))
        .catch(() => setMyToken(null));
    }
  }, []);

  if (loading) return <div>Loading waiting times...</div>;

  return (
    <div className="waiting-time-dashboard">
      {/* My Token Status */}
      {myToken && (
        <div className="my-token-card">
          <h3>Your Appointment Status</h3>
          <div className="token-info">
            <span className="token-number">{myToken.token_number}</span>
            <span className="doctor">Dr. {myToken.doctor_name}</span>
          </div>
          <div className="waiting-info">
            <div className="queue-position">
              Position #{myToken.queue_position} in queue
            </div>
            <div className="expected-time">
              Expected: {myToken.expected_consultation_start?.expected_start}
            </div>
            <div className="message">{myToken.message}</div>
          </div>
        </div>
      )}

      {/* Clinic Waiting Times */}
      <div className="clinics-grid">
        {clinics.map(clinic => (
          <div key={clinic.clinic_id} className="clinic-card">
            <h3>{clinic.clinic_name}</h3>
            <div className="clinic-stats">
              <span>Total Queue: {clinic.total_queue_length}</span>
              <span>Avg Wait: {clinic.average_waiting_time_minutes} min</span>
            </div>
            
            <div className="doctors-list">
              {clinic.doctors.map(doctor => (
                <div key={doctor.doctor_id} className="doctor-card">
                  <div className="doctor-header">
                    <h4>Dr. {doctor.doctor_name}</h4>
                    <span className="specialization">{doctor.specialization}</span>
                  </div>
                  
                  <div className="waiting-stats">
                    <div className="stat">
                      <label>Current Wait:</label>
                      <span className="wait-time">
                        {doctor.predicted_waiting_time_minutes} min
                      </span>
                    </div>
                    
                    <div className="stat">
                      <label>Queue:</label>
                      <span>{doctor.current_queue_length} patients</span>
                    </div>
                    
                    {doctor.next_available_slot && (
                      <div className="stat">
                        <label>Next Slot:</label>
                        <span>{doctor.next_available_slot.display_text}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className={`status ${doctor.status}`}>
                    {doctor.status === 'available' ? '🟢 Available' : '🔴 Busy'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WaitingTimeDashboard;
```

### CSS Styling
```css
.waiting-time-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.my-token-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 30px;
}

.token-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.token-number {
  font-size: 24px;
  font-weight: bold;
  background: rgba(255,255,255,0.2);
  padding: 8px 16px;
  border-radius: 20px;
}

.waiting-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.clinics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.clinic-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.doctor-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  background: #fafafa;
}

.waiting-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin: 10px 0;
}

.stat {
  text-align: center;
}

.stat label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.wait-time {
  font-size: 18px;
  font-weight: bold;
  color: #2196F3;
}

.status.available {
  color: #4CAF50;
  font-weight: bold;
}

.status.busy {
  color: #FF5722;
  font-weight: bold;
}
```

## 📱 **Mobile-Friendly Widget**
```jsx
const MobileWaitingWidget = ({ clinic }) => (
  <div className="mobile-waiting-widget">
    <h4>{clinic.clinic_name}</h4>
    <div className="quick-stats">
      <span className="avg-wait">{clinic.average_waiting_time_minutes}min avg</span>
      <span className="queue-count">{clinic.total_queue_length} in queue</span>
    </div>
    
    <div className="doctors-quick">
      {clinic.doctors.slice(0, 3).map(doctor => (
        <div key={doctor.doctor_id} className="doctor-quick">
          <span className="name">Dr. {doctor.doctor_name}</span>
          <span className="wait">{doctor.predicted_waiting_time_minutes}min</span>
        </div>
      ))}
    </div>
  </div>
);
```

## 🔄 **Real-time Updates**
```javascript
// Auto-refresh waiting times every 2 minutes
useEffect(() => {
  const interval = setInterval(() => {
    fetch('/api/waiting-time/dashboard/')
      .then(response => response.json())
      .then(data => setClinics(data.clinics || []));
  }, 120000); // 2 minutes

  return () => clearInterval(interval);
}, []);
```

## 🎨 **Key Features Displayed**

### For All Users (Public)
- **Clinic waiting times** - Average wait per clinic
- **Doctor availability** - Individual doctor wait times
- **Queue lengths** - How many patients waiting
- **Next available slots** - When can I book?
- **Real-time status** - Available/Busy indicators

### For Logged-in Patients
- **My queue position** - "You're #3 in line"
- **Expected consultation time** - "Expected at 3:45 PM"
- **Appointment delays** - "Running 15 minutes behind"
- **Personalized messages** - Clear status updates

## 🚀 **Implementation Steps**

1. **Add to your home page component**
2. **Style with provided CSS**
3. **Test with sample data**
4. **Add real-time updates**
5. **Customize for your design**

## 📊 **Sample Data Structure**
The API returns exactly what patients need to know:
- **"Dr. Smith: 25 min wait, 4 in queue"**
- **"Next slot: Today at 3:30 PM"**
- **"You're #3, expected at 3:45 PM"**

This gives patients **real clarity** about waiting times based on **actual clinic data**, not just appointment slots!