import React, { useState } from 'react';
import './LoginPage.css'; 

function LoginPage({ apiClient, onLoginSuccess, onSwitchToRegister, onBackToHome }) {
    const [activeTab, setActiveTab] = useState('patient'); // 'patient' or 'staff'
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');

        // 
        // THIS IS THE CORRECTED SECTION
        // 
        // We use the full absolute URL of your Django server
        // and the correct paths from your api/urls.py file.
        // 
      const loginUrl = activeTab === 'patient' 
            ? '/login/' 
            : '/login/staff/';
        
        try {
            const response = await apiClient.post(loginUrl, { username, password });
            onLoginSuccess(response.data);
        } catch (err) {
            // Check for a specific 404 error first
            if (err.response && err.response.status === 404) {
                setError("Error: API endpoint not found. Check the URL.");
            } else {
                const errorMessage = activeTab === 'patient' 
                    ? 'Invalid patient credentials.' 
                    : 'Invalid staff credentials.';
                setError(err.response?.data?.error || errorMessage);
            }
        }
    };

    return (
        <div className="login-container">
            <button onClick={onBackToHome} className="back-button">← Back to Home</button>
            <div className="login-card">
                <div className="login-tabs">
                    <button 
                        className={`tab ${activeTab === 'patient' ? 'active' : ''}`}
                        onClick={() => setActiveTab('patient')}
                    >
                        Patient Login
                    </button>
                    <button 
                        className={`tab ${activeTab === 'staff' ? 'active' : ''}`}
                        onClick={() => setActiveTab('staff')}
                    >
                        Staff Login
                    </button>
                </div>

                <h1 className="login-title">{activeTab === 'patient' ? 'Patient Portal' : 'Staff & Doctor Portal'}</h1>
                
                <form onSubmit={handleLogin}>
                    <div className="input-group">
                        <label>Username</label>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
                    </div>
                    <div className="input-group">
                        <label>Password</label>
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </div>
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit" className="primary-button">Login</button>
                </form>

                {activeTab === 'patient' && (
                    <p className="switch-form-text">
                        New patient? <span onClick={onSwitchToRegister} className="switch-form-link">Register here</span>
                    </p>
                )}
            </div>
        </div>
    );
}

export default LoginPage;