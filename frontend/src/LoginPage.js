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

        if (!username.trim() || !password.trim()) {
            setError('Please enter both username and password.');
            return;
        }

        const loginUrl = activeTab === 'patient' ? '/login/' : '/login/staff/';
        
        try {
            const response = await apiClient.post(loginUrl, { username, password });
            console.log('Login response:', response?.data);
            
            // Validate response structure
            if (!response.data || !response.data.token || !response.data.user) {
                throw new Error('Invalid response structure from server');
            }
            
            // Validate role matches login type
            const userRole = response.data.user.role;
            if (activeTab === 'patient' && userRole !== 'patient') {
                setError('This account is not a patient account. Please use Staff Login.');
                return;
            }
            if (activeTab === 'staff' && userRole === 'patient') {
                setError('This account is not a staff account. Please use Patient Login.');
                return;
            }
            
            onLoginSuccess(response.data);
        } catch (err) {
            console.error('Login error:', err);
            if (err.response?.status === 404) {
                setError("Login service unavailable. Please try again later.");
            } else if (err.message === 'Invalid response structure from server') {
                setError("Server error. Please contact support.");
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