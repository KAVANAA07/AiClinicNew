import React, { useState } from 'react';

const ReceptionistConfirmation = ({ token, onConfirm, onError }) => {
  const [loading, setLoading] = useState(false);

  const handleReceptionistConfirm = async () => {
    setLoading(true);

    try {
      const response = await fetch(`/api/tokens/${token.id}/confirm_arrival/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('token')}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        onConfirm(data);
      } else {
        onError(data.error || 'Failed to confirm arrival');
      }
    } catch (err) {
      onError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (token.status !== 'waiting') {
    return null;
  }

  return (
    <div className="receptionist-confirmation">
      <button
        onClick={handleReceptionistConfirm}
        disabled={loading}
        style={{
          backgroundColor: '#2196F3',
          color: 'white',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '14px'
        }}
      >
        {loading ? 'Confirming...' : 'Confirm Arrival'}
      </button>
    </div>
  );
};

export default ReceptionistConfirmation;