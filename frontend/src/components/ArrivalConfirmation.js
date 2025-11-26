import React, { useState, useEffect } from 'react';

const ArrivalConfirmation = ({ token, onConfirm }) => {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [canConfirm, setCanConfirm] = useState(false);

  useEffect(() => {
    checkConfirmationWindow();
  }, [token]);

  const checkConfirmationWindow = () => {
    if (!token || !token.appointment_time) {
      setCanConfirm(false);
      return;
    }

    const now = new Date();
    const appointmentDateTime = new Date(`${token.date}T${token.appointment_time}`);
    const startWindow = new Date(appointmentDateTime.getTime() - 20 * 60 * 1000); // 20 minutes before
    const endWindow = new Date(appointmentDateTime.getTime() + 15 * 60 * 1000); // 15 minutes after

    const isWithinWindow = now >= startWindow && now <= endWindow;
    setCanConfirm(isWithinWindow);

    if (!isWithinWindow) {
      const startTime = startWindow.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const endTime = endWindow.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setError(`Confirmation available between ${startTime} and ${endTime}`);
    } else {
      setError('');
    }
  };

  const getCurrentLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by this browser'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => {
          reject(new Error('Unable to get your location. Please enable location services.'));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      );
    });
  };

  const handleConfirmArrival = async () => {
    if (!canConfirm) {
      setError('Confirmation not available at this time');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Get GPS location
      const location = await getCurrentLocation();
      setLocation(location);

      // Call API to confirm arrival with GPS verification
      const response = await fetch('/api/tokens/confirm_arrival/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          latitude: location.latitude,
          longitude: location.longitude
        })
      });

      const data = await response.json();

      if (response.ok) {
        onConfirm(data);
      } else {
        setError(data.error || 'Failed to confirm arrival');
      }
    } catch (err) {
      setError(err.message || 'Failed to confirm arrival');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <div>No appointment found</div>;
  }

  return (
    <div className="arrival-confirmation">
      <h3>Confirm Your Arrival</h3>
      
      <div className="appointment-info">
        <p><strong>Doctor:</strong> {token.doctor?.name}</p>
        <p><strong>Date:</strong> {token.date}</p>
        <p><strong>Time:</strong> {token.appointment_time}</p>
        <p><strong>Status:</strong> {token.status}</p>
      </div>

      {error && (
        <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>
          {error}
        </div>
      )}

      {token.status === 'waiting' && (
        <div>
          <p>
            <strong>Important:</strong> You can only confirm your arrival between 20 minutes before 
            and 15 minutes after your appointment time. GPS verification is required.
          </p>
          
          <button
            onClick={handleConfirmArrival}
            disabled={!canConfirm || loading}
            style={{
              backgroundColor: canConfirm ? '#4CAF50' : '#cccccc',
              color: 'white',
              padding: '10px 20px',
              border: 'none',
              borderRadius: '5px',
              cursor: canConfirm ? 'pointer' : 'not-allowed',
              fontSize: '16px'
            }}
          >
            {loading ? 'Confirming...' : 'Confirm Arrival'}
          </button>
          
          {!canConfirm && (
            <p style={{ color: '#666', fontSize: '14px', marginTop: '10px' }}>
              Confirmation will be available 20 minutes before your appointment time.
            </p>
          )}
        </div>
      )}

      {token.status === 'confirmed' && (
        <div style={{ color: 'green' }}>
          <p><strong>✓ Arrival Confirmed!</strong></p>
          {token.arrival_confirmed_at && (
            <p>Confirmed at: {new Date(token.arrival_confirmed_at).toLocaleString()}</p>
          )}
        </div>
      )}

      {location && (
        <div style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
          Location verified: {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
        </div>
      )}
    </div>
  );
};

export default ArrivalConfirmation;