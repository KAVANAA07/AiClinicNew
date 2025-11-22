import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import './App.css';
import PublicHomePage from './PublicHomePage';
import LoginPage from './LoginPage';
import './LoginPage.css';
// --- LOGO IMPORT ---
import PatientAISummary from './components/PatientAISummary';
import ScheduleManagement from './components/ScheduleManagement';

import medqLogo from './logo.jpg'; // Assuming logo.png is in the src folder

// --- API Configuration ---
const apiClient = axios.create({
    // *** FIX APPLIED HERE: Using the live Render backend URL ***
    baseURL: 'http://localhost:8000/api/',
});

apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('authToken');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'Auth:', !!token);
    return config;
}, error => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
});

apiClient.interceptors.response.use(
    response => {
        console.log('API Response:', response.config.method?.toUpperCase(), response.config.url, 'Status:', response.status);
        return response;
    },
    error => {
        console.error('API Error:', error.config?.method?.toUpperCase(), error.config?.url, 'Status:', error.response?.status, 'Data:', error.response?.data);
        if (error.response?.status === 401) {
            console.warn('Unauthorized request - token may be invalid');
            // Optionally clear invalid token
            // localStorage.removeItem('authToken');
            // localStorage.removeItem('loggedInUser');
        }
        return Promise.reject(error);
    }
);


// ====================================================================
// PUBLIC & AUTH COMPONENTS
// ====================================================================

const PublicHeader = ({ onLoginClick, onRegisterClick }) => (
    <header className="public-header">
        <a href="/" className="logo">
             <img src={medqLogo} alt="MedQ Logo" className="logo-img" /> {/* Use imported logo */}
            <div className="logo-text">
                <p className="app-name">MedQ</p>
                <p className="app-tagline">Better Flow for Kinder Care</p>
            </div>
        </a>
        <div className="header-actions">
            <button onClick={onLoginClick} className="header-button-secondary">Login</button>
            <button onClick={onRegisterClick} className="header-button-primary">Register</button>
        </div>
    </header>
);

const PublicFooter = ({ onStaffLoginClick }) => (
    <footer className="public-footer">
        <p>&copy; {new Date().getFullYear()} AI-Powered Clinic Systems. All rights reserved.</p>
        <p className="staff-login-link-container">
            Are you a doctor or staff? <span onClick={onStaffLoginClick} className="staff-login-link">Login here</span>
        </p>
    </footer>
);

// --- REVERTED: PatientRegisterComponent (Simple, No OTP) ---
const PatientRegisterComponent = ({ onRegisterSuccess, onSwitchToLogin, showSuccessMessage }) => {
    // --- State for details form ---
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [password2, setPassword2] = useState('');
    const [name, setName] = useState('');
    const [age, setAge] = useState('');
    const [phoneNumber, setPhoneNumber] = useState(''); // E.g., +919876543210
    
    // --- State for messages & loading ---
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false); // Keep loading state

    // --- REVERTED: Handle Registration Details Submission ---
    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        if (password !== password2) { 
            setError("Passwords do not match."); 
            setIsLoading(false);
            return; 
        }
        
        if (password.length < 8) {
            setError("Password must be at least 8 characters long.");
            setIsLoading(false);
            return;
        }
        
        // Enhanced phone validation
        const phoneRegex = /^\+[1-9]\d{1,14}$/;
        if (!phoneRegex.test(phoneNumber)) {
             setError("Please enter a valid phone number with country code (e.g., +919876543210).");
             setIsLoading(false);
             return;
        }

        try {
            // Call backend to create ACTIVE user and log in
            const response = await apiClient.post('/register/patient/', { 
                username, password, password2, name, age, phone_number: phoneNumber 
            });

            // Show success message from App.js
            showSuccessMessage("Registration Successful!");

            // Call onRegisterSuccess after a short delay to show message
            setTimeout(() => {
                 onRegisterSuccess(response.data);
            }, 1500); // 1.5 second delay

        } catch (err) {
            console.error("Registration error:", err);
            let detailedError = 'Registration failed.';
             if (err.response?.data) { // Backend validation error
                 detailedError = Object.values(err.response.data).flat().join(' ');
             }
             setError(detailedError);
             setIsLoading(false); // Stop loading on error
        }
    };

    // --- Render Logic (Single Step) ---
    return ( 
        <div className="login-container">
            {/* No reCAPTCHA container needed */}
            <div className="login-card">
                <h1 className="login-title">Patient Registration</h1>
                <form onSubmit={handleRegister}>
                    <div className="input-group"><label>Full Name</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} required disabled={isLoading} /></div>
                    <div className="input-group"><label>Age</label><input type="number" value={age} onChange={(e) => setAge(e.target.value)} required disabled={isLoading} /></div>
                    <div className="input-group"><label>Phone Number (e.g., +919876543210)</label><input type="tel" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="+919876543210" required disabled={isLoading} /></div>
                    <div className="input-group"><label>Username</label><input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required disabled={isLoading} /></div>
                    <div className="input-group"><label>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required disabled={isLoading} /></div>
                    <div className="input-group"><label>Confirm Password</label><input type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} required disabled={isLoading} /></div>
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit" className="primary-button" disabled={isLoading}>
                        {isLoading ? 'Registering...' : 'Register & Login'}
                    </button>
                </form>
                <p className="switch-form-text">Already have an account? <span onClick={() => !isLoading && onSwitchToLogin()} className={`switch-form-link ${isLoading ? 'disabled-link' : ''}`}>Login here</span></p>
            </div>
        </div> 
    );
};


// ====================================================================
// PRIVATE DASHBOARD COMPONENTS (FULL CODE RESTORED)
// ====================================================================

const ReceptionistDashboardComponent = ({ loggedInUser, onLogout, onSelectPatient, onViewHistory, onViewAnalytics, onManageSchedules }) => {
    const [patientName, setPatientName] = useState('');
    const [patientAge, setPatientAge] = useState('');
    const [patientPhone, setPatientPhone] = useState('');
    const [assignedDoctor, setAssignedDoctor] = useState('');
    const [doctors, setDoctors] = useState([]);
    const [queue, setQueue] = useState([]);
    const [error, setError] = useState('');
    const [availableSlots, setAvailableSlots] = useState([]);
    const [selectedSlot, setSelectedSlot] = useState('');
    const today = new Date().toISOString().split('T')[0];

    const formatTime = (timeStr) => {
        if (!timeStr) return '';
        const parts = timeStr.split(':');
        if (parts.length < 2) return 'Invalid time';
        const [hour, minute] = parts;
        const h = parseInt(hour, 10);
        const m = parseInt(minute, 10);
        if (isNaN(h) || isNaN(m)) return 'Invalid time';
        const ampm = h >= 12 ? 'PM' : 'AM';
        const formattedHour = h % 12 === 0 ? 12 : h % 12;
        const formattedMinute = String(m).padStart(2, '0'); 
        return `${formattedHour}:${formattedMinute} ${ampm}`;
    };

    const fetchQueue = useCallback(async () => {
        try { const response = await apiClient.get('/tokens/'); setQueue(response.data); } catch (err) { setError('Could not fetch queue.'); }
    }, []);

    const fetchDoctors = useCallback(async () => {
        try {
            const response = await apiClient.get('/doctors/');
            setDoctors(response.data);
            if (response.data.length > 0 && !assignedDoctor) {
                setAssignedDoctor(response.data[0].id);
            }
        } catch (err) { setError('Could not fetch doctors.'); }
    }, [assignedDoctor]);

    useEffect(() => {
        fetchDoctors();
        fetchQueue();
        const interval = setInterval(fetchQueue, 5000); 
        return () => clearInterval(interval);
    }, [fetchDoctors, fetchQueue]);

    useEffect(() => {
        const fetchSlots = async () => {
            if (assignedDoctor) {
                try {
                    // Fetch slots for today's date
                    const response = await apiClient.get(`/doctors/${assignedDoctor}/available-slots/${today}/`);
                    setAvailableSlots(response.data);
                } catch (err) {
                    console.error("Failed to fetch slots for receptionist view:", err);
                    setAvailableSlots([]);
                }
            } else {
                setAvailableSlots([]);
            }
        };
        fetchSlots();
        const intervalId = setInterval(fetchSlots, 20000); 
        return () => clearInterval(intervalId);
    }, [assignedDoctor, today]); // Re-fetch slots if doctor or date changes

    const handleGenerateToken = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await apiClient.post('/tokens/', { 
                patient_name: patientName, 
                patient_age: patientAge, 
                phone_number: patientPhone, 
                assigned_doctor: assignedDoctor,
                appointment_time: selectedSlot // This will be an empty string "" for walk-ins
            });
            setPatientName(''); 
            setPatientAge(''); 
            setPatientPhone('');
            setSelectedSlot(''); 
            fetchQueue(); // Refresh queue immediately
            
            // --- NEW: Refresh available slots after booking ---
            if (assignedDoctor) {
                try {
                    const response = await apiClient.get(`/doctors/${assignedDoctor}/available-slots/${today}/`);
                    setAvailableSlots(response.data);
                } catch (err) {
                    console.error("Failed to re-fetch slots:", err);
                }
            }
            // --- End New ---

        } catch (err) { 
             setError(err.response?.data?.error || 'Failed to create token.'); 
             console.error("Token creation error:", err.response || err);
        }
    };

    const handleStaffUpdateStatus = async (tokenId, newStatus) => {
        setError(''); 
        try { 
            await apiClient.patch(`/tokens/${tokenId}/update_status/`, { status: newStatus }); 
            fetchQueue(); 
        } 
        catch (err) { 
             setError(err.response?.data?.error || `Failed to update status to ${newStatus}.`); 
             console.error("Status update error:", err.response || err);
        }
    };

    const getWelcomeMessage = () => {
        const userName = loggedInUser?.user?.name || loggedInUser?.user?.username || 'Staff Member';
        let welcomeText = `Welcome, ${userName}`;
        if (loggedInUser?.user?.clinic?.name) { 
            welcomeText += ` | ${loggedInUser.user.clinic.name}`; 
        }
        return welcomeText;
    };
    
    const LocationIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" /></svg>);

    const safeQueue = Array.isArray(queue) ? queue : []; 
    const sortedQueue = [...safeQueue]; // The backend now handles sorting

    const currentTimeForFilter = new Date();
    const futureSlots = availableSlots.filter(slot => {
        if (today === new Date().toISOString().split('T')[0]) {
            const parts = slot.split(':');
            if (parts.length < 2) return false;
            const [hour, minute] = parts;
            const h = parseInt(hour, 10);
            const m = parseInt(minute, 10);
            if (isNaN(h) || isNaN(m)) return false;
            const slotTime = new Date();
            slotTime.setHours(h, m, 0, 0);
            return slotTime >= currentTimeForFilter; 
        }
        return true; 
    });

    return ( 
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Receptionist Dashboard</h1>
                <div className="user-info">
                    <span>{getWelcomeMessage()}</span>
                    <button onClick={onManageSchedules} className="secondary-button">Manage Schedules</button>
                    <button onClick={onViewAnalytics} className="secondary-button">View Analytics</button>
                    <button onClick={onLogout} className="logout-button">Logout</button>
                </div>
            </header>
            {error && <div className="error-banner">{error}</div>}
            <div className="dashboard-content staff-dashboard-layout">
                <div className="form-card card"> 
                    <h2>Add Patient / Book Slot</h2>
                    <form onSubmit={handleGenerateToken}>
                        <div className="input-group"><label>Patient Name</label><input type="text" value={patientName} onChange={(e) => setPatientName(e.target.value)} required /></div>
                        <div className="input-group"><label>Patient Age</label><input type="number" value={patientAge} onChange={(e) => setPatientAge(e.target.value)} required /></div>
                        <div className="input-group"><label>Patient Phone (+CountryCode)</label><input type="tel" value={patientPhone} onChange={(e) => setPatientPhone(e.target.value)} placeholder="+919876543210" required /></div>
                        <div className="input-group"><label>Assign to Doctor</label><select value={assignedDoctor} onChange={(e) => { setAssignedDoctor(e.target.value); setSelectedSlot(''); }} required>{doctors.map((doc) => (<option key={doc.id} value={doc.id}>{doc.name} - {doc.specialization}</option>))}</select></div>
                        
                        {assignedDoctor && (
                            <div className="input-group">
                                <label>Select Available Time (Optional - leave blank for walk-in)</label>
                                <div className="time-slots-container">
                                    {futureSlots.length > 0 ? (
                                        futureSlots.map(slot => (
                                            <button 
                                                type="button" 
                                                key={slot} 
                                                className={`time-slot-btn ${selectedSlot === slot ? 'selected' : ''}`}
                                                onClick={() => setSelectedSlot(prev => prev === slot ? '' : slot)} 
                                            >
                                                {formatTime(slot)}
                                            </button>
                                        ))
                                    ) : <p>No slots available for this doctor today.</p>}
                                </div>
                            </div>
                        )}
                        
                        <button type="submit" className="primary-button">
                            {selectedSlot ? 'Book Appointment Slot' : 'Add Walk-in Patient'}
                         </button>
                    </form>
                </div>
                <div className="queue-card card"> 
                    <h2>Live Patient Queue</h2>
                    <div className="table-container">
                        {sortedQueue.length > 0 ? ( 
                            <table className="patient-table">
                                <thead>
                                    <tr>
                                        <th>Token</th>
                                        <th>Patient</th>
                                        <th>Age</th>
                                        <th>Doctor</th>
                                        <th>Time</th>
                                        <th>Status</th>
                                        <th>Distance</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortedQueue.map((token) => ( 
                                        <tr key={token.id} className={`status-${token.status}`}>
                                            <td className="token-cell">#{token.token_number || (token.appointment_time ? 'Scheduled' : 'Walk-in')}</td>
                                            <td className="patient-cell">{token.patient.name}</td>
                                            <td>{token.patient.age}</td>
                                            <td>{token.doctor.name}</td>
                                            <td>{token.appointment_time ? formatTime(token.appointment_time) : 'Walk-in'}</td>
                                            <td><span className={`status-badge status-${token.status}`}>{token.status.replace(/_/g, ' ')}</span></td>
                                            <td>
                                                {token.distance_km != null && ['waiting', 'confirmed'].includes(token.status) ? (
                                                    <span className="distance-info">
                                                        <LocationIcon />
                                                        {token.distance_km <= 0.1 ? 'At Clinic' : `${token.distance_km.toFixed(1)} km`}
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td>
                                                <div className="action-buttons">
                                                    {token.status === 'waiting' && (
                                                        <button onClick={() => handleStaffUpdateStatus(token.id, 'confirmed')} className="table-btn confirm-btn">Confirm</button>
                                                    )}
                                                    {['waiting', 'confirmed', 'in_consultancy'].includes(token.status) && (
                                                        <>
                                                            <button onClick={() => handleStaffUpdateStatus(token.id, 'cancelled')} className="table-btn cancel-btn">Cancel</button>
                                                            <button onClick={() => handleStaffUpdateStatus(token.id, 'skipped')} className="table-btn skip-btn">Skip</button>
                                                        </>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p>The queue is currently empty.</p>
                        )}
                    </div>
                </div>
            </div>
        </div> 
    );
};
const DoctorDashboardComponent = ({ loggedInUser, onLogout, onSelectPatient, onViewHistory, onViewAnalytics }) => {
    const [queue, setQueue] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    // --- NEW: Emergency History Search State ---
    const [searchPhone, setSearchPhone] = useState('');
    const [searchHistory, setSearchHistory] = useState(null);
    const [searchError, setSearchError] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [aiSummary, setAiSummary] = useState('');
    const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
    // --- END NEW STATE ---

    const fetchQueue = useCallback(async () => {
        setError(''); 
        setLoading(true);
        try { 
            console.log('Fetching doctor queue...');
            const response = await apiClient.get('/tokens/'); 
            console.log('Doctor queue response:', response.data);
            console.log('Response type:', typeof response.data, 'Is array:', Array.isArray(response.data));
            setQueue(Array.isArray(response.data) ? response.data : []); 
        } catch (err) { 
            setError('Could not fetch your patient queue.'); 
            console.error("Fetch queue error:", err);
            console.error("Error response:", err.response);
            console.error("Error status:", err.response?.status);
            console.error("Error data:", err.response?.data);
            setQueue([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchQueue();
        const interval = setInterval(fetchQueue, 5000); 
        return () => clearInterval(interval);
    }, [fetchQueue]);

    // Debug logging
    useEffect(() => {
        console.log('Doctor dashboard queue state:', queue);
        console.log('Queue length:', queue.length);
        console.log('Loading state:', loading);
        console.log('User info:', loggedInUser);
        console.log('User role:', loggedInUser?.user?.role);
    }, [queue, loading, loggedInUser]);

    // --- NEW: Emergency Search Handler ---
    const handleEmergencySearch = async (e) => {
        e.preventDefault();
        if (!searchPhone.trim()) return;
        
        setIsSearching(true);
        setSearchError('');
        setSearchHistory(null);

        try {
            const response = await apiClient.get(`/history-search/?phone=${encodeURIComponent(searchPhone.trim())}`);
            setSearchHistory(response.data); // Expecting a list of consultation records
        } catch (err) {
            console.error("Search error:", err);
            setSearchError(err.response?.data?.error || 'Patient not found or error occurred.');
            setSearchHistory([]); 
        } finally {
            setIsSearching(false);
        }
    };
    // --- END NEW HANDLER ---

    const handleStaffUpdateStatus = async (tokenId, newStatus) => {
         setError('');
        try { 
            await apiClient.patch(`/tokens/${tokenId}/update_status/`, { status: newStatus }); 
            fetchQueue(); 
        } 
        catch (err) { 
             setError(err.response?.data?.error || `Failed to update status to ${newStatus}.`); 
             console.error("Status update error:", err.response || err);
        }
    };
    
    const handleStartConsultation = (token) => {
         handleStaffUpdateStatus(token.id, 'in_consultancy'); 
         onSelectPatient(token.patient); 
    };

    const getWelcomeMessage = () => {
        const userName = loggedInUser?.user?.name || loggedInUser?.user?.username || 'Doctor';
        let welcomeText = `Welcome, Dr. ${userName}`;
        if (loggedInUser?.user?.clinic?.name) {
            welcomeText += ` | ${loggedInUser.user.clinic.name}`;
        }
        return welcomeText;
    };
    
    const safeQueue = Array.isArray(queue) ? queue : [];
    const sortedQueue = [...safeQueue]; 

    const confirmedPatients = sortedQueue.filter(t => t && t.status === 'confirmed');
    const waitingPatients = sortedQueue.filter(t => t && t.status === 'waiting');
    const inConsultancy = sortedQueue.find(t => t && t.status === 'in_consultancy'); 

    const nextPatientTokenId = confirmedPatients.length > 0 ? confirmedPatients[0]?.id : null;

    const formatTime = (timeStr) => { 
         if (!timeStr) return '';
         const parts = timeStr.split(':');
         if (parts.length < 2) return 'Invalid time';
         const [hour, minute] = parts;
         const h = parseInt(hour, 10);
         const m = parseInt(minute, 10);
         if (isNaN(h) || isNaN(m)) return 'Invalid time';
         const ampm = h >= 12 ? 'PM' : 'AM';
         const formattedHour = h % 12 === 0 ? 12 : h % 12;
         const formattedMinute = String(m).padStart(2, '0');
         return `${formattedHour}:${formattedMinute} ${ampm}`;
    };

    return ( 
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Doctor Dashboard</h1>
                <div className="user-info">
                    <span>{getWelcomeMessage()}</span>
                    <button onClick={onViewAnalytics} className="secondary-button">View Analytics</button>
                    <button onClick={onLogout} className="logout-button">Logout</button>
                </div>
            </header>
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-message">Loading patient queue...</div>}
            <div className="dashboard-content doctor-dashboard-layout"> 
                
                {/* --- Enhanced Emergency Search Section --- */}
                <div className="card emergency-search-card" style={{border: '2px solid var(--primary-color)', marginBottom: '20px', background: 'linear-gradient(135deg, #f8f9fa, #e9ecef)'}}>
                    <h2 style={{color: 'var(--primary-color)', marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px'}}>
                        🔍 Patient History Search
                        <span style={{fontSize: '0.7em', background: 'var(--highlight-color)', color: 'white', padding: '2px 8px', borderRadius: '12px'}}>ENHANCED</span>
                    </h2>
                    <form onSubmit={handleEmergencySearch} style={{display: 'flex', gap: '10px', marginBottom: '15px', padding: '15px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)'}}>
                        <div className="input-group" style={{flex: 1, margin: 0}}>
                            <input 
                                type="tel" 
                                placeholder="Enter Patient Phone (+91...)" 
                                value={searchPhone}
                                onChange={(e) => setSearchPhone(e.target.value)}
                                required
                            />
                        </div>
                        <button type="submit" className="primary-button" disabled={isSearching} style={{padding: '12px 24px', minWidth: '140px'}}>
                            {isSearching ? '🔄 Searching...' : '🔍 Search History'}
                        </button>
                    </form>

                    {searchError && <p className="error-message">{searchError}</p>}

                    {searchHistory && (
                        <div className="search-results" style={{background: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
                            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px'}}>
                                <h3 style={{margin: 0, color: 'var(--primary-color)'}}>📋 History Results for {searchPhone}</h3>
                                <span style={{background: 'var(--success-color)', color: 'white', padding: '4px 12px', borderRadius: '20px', fontSize: '0.8em'}}>
                                    {searchHistory.length} Records Found
                                </span>
                            </div>
                            {searchHistory.length > 0 ? (
                                <div style={{maxHeight: '400px', overflowY: 'auto', border: '1px solid var(--medium-gray)', borderRadius: '6px'}}>
                                    {searchHistory.map((record, index) => (
                                        <div key={record.id} style={{padding: '15px', borderBottom: index < searchHistory.length - 1 ? '1px solid var(--light-gray)' : 'none', background: index % 2 === 0 ? '#fafafa' : 'white'}}>
                                            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px'}}>
                                                <span style={{fontWeight: 'bold', color: 'var(--primary-color)'}}>
                                                    📅 {new Date(record.date).toLocaleDateString()}
                                                </span>
                                                <span style={{background: 'var(--info-color)', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8em'}}>
                                                    👨‍⚕️ {record.doctor ? record.doctor.name : 'Unknown'}
                                                </span>
                                            </div>
                                            <p style={{margin: '8px 0', color: 'var(--text-color)'}}><strong>Notes:</strong> {record.notes || 'No notes'}</p>
                                            
                                            {record.prescription_items && record.prescription_items.length > 0 && (
                                                <div style={{marginTop: '12px', backgroundColor: '#e8f5e8', padding: '10px', borderRadius: '6px', border: '1px solid #c3e6c3'}}>
                                                    <strong style={{color: 'var(--success-color)', display: 'flex', alignItems: 'center', gap: '5px'}}>
                                                        💊 Prescription ({record.prescription_items.length} items):
                                                    </strong>
                                                    <div style={{marginTop: '8px'}}>
                                                        {record.prescription_items.map((item, idx) => (
                                                            <div key={idx} style={{padding: '6px 0', borderBottom: idx < record.prescription_items.length - 1 ? '1px solid #d4edda' : 'none'}}>
                                                                <span style={{fontWeight: '600'}}>{item.medicine_name}</span> - {item.dosage} ({item.duration_days} days)
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div style={{textAlign: 'center', padding: '40px', color: 'var(--dark-gray)'}}>
                                    <div style={{fontSize: '3em', marginBottom: '10px'}}>📭</div>
                                    <p>No consultation history found for this patient.</p>
                                </div>
                            )}
                            <div style={{display: 'flex', gap: '12px', marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '6px'}}>
                                <button 
                                    onClick={() => {setSearchHistory(null); setSearchPhone('');}} 
                                    className="secondary-button" 
                                    style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'}}
                                >
                                    🗑️ Clear Results
                                </button>
                                <button 
                                    onClick={async () => {
                                        if (!searchHistory || searchHistory.length === 0) return;
                                        
                                        setIsGeneratingSummary(true);
                                        try {
                                            const historyText = searchHistory.map(record => 
                                                `Date: ${new Date(record.date).toLocaleDateString()}\n` +
                                                `Doctor: ${record.doctor?.name || 'Unknown'}\n` +
                                                `Notes: ${record.notes || 'No notes'}\n` +
                                                `Prescriptions: ${record.prescription_items?.map(item => 
                                                    `${item.medicine_name} - ${item.dosage} (${item.duration_days} days)`
                                                ).join(', ') || 'None'}\n\n`
                                            ).join('');
                                            
                                            const response = await apiClient.post('/ai-summary/', {
                                                patient_history: historyText,
                                                phone: searchPhone
                                            });
                                            
                                            setAiSummary(response.data.summary);
                                        } catch (err) {
                                            console.error('AI Summary error:', err);
                                            setAiSummary('Error generating AI summary. Please try again.');
                                        } finally {
                                            setIsGeneratingSummary(false);
                                        }
                                    }}
                                    className="primary-button"
                                    disabled={!searchHistory || searchHistory.length === 0 || isGeneratingSummary}
                                    style={{flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: 'linear-gradient(135deg, var(--highlight-color), #ff6b35)'}}
                                >
                                    {isGeneratingSummary ? '🔄 Generating...' : '🤖 AI Summary'}
                                </button>
                            </div>
                            
                            {aiSummary && (
                                <div style={{marginTop: '20px', padding: '20px', background: 'linear-gradient(135deg, #e3f2fd, #f3e5f5)', borderRadius: '8px', border: '2px solid var(--info-color)'}}>
                                    <h4 style={{margin: '0 0 15px 0', color: 'var(--primary-color)', display: 'flex', alignItems: 'center', gap: '8px'}}>
                                        🤖 AI Medical Summary
                                    </h4>
                                    <div style={{background: 'white', padding: '15px', borderRadius: '6px', border: '1px solid #e0e0e0', whiteSpace: 'pre-wrap', lineHeight: '1.6'}}>
                                        {aiSummary}
                                    </div>
                                    <button 
                                        onClick={() => setAiSummary('')} 
                                        style={{marginTop: '10px', padding: '8px 16px', background: 'var(--medium-gray)', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                                    >
                                        ✖ Close Summary
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
                {/* --- END NEW SECTION --- */}

                 {inConsultancy && (
                      <div className="card">
                           <h2 className="queue-section-title" style={{color: 'var(--primary-color)'}}>Currently with Patient</h2>
                            <div className="queue-grid">
                                <div key={inConsultancy.id} className={`queue-item-card status-in_consultancy`}>
                                     <div className="queue-card-header">
                                         <div className="token-number">#{inConsultancy.token_number || (inConsultancy.appointment_time ? 'Scheduled' : 'Walk-in')}</div>
                                         <span className={`status-badge status-in_consultancy`}>In Consultancy</span>
                                     </div>
                                     <div className="queue-card-body">
                                         <p className="patient-name">{inConsultancy.patient?.name || 'Unknown Patient'}</p>
                                         <p><strong>Age:</strong> {inConsultancy.patient?.age || 'N/A'}</p>
                                          {inConsultancy.appointment_time && (
                                            <p className="appointment-time-display">
                                                <strong>Original Slot:</strong> {formatTime(inConsultancy.appointment_time)}
                                            </p>
                                          )}
                                     </div>
                                     <div className="queue-card-footer">
                                        <button onClick={() => onSelectPatient(inConsultancy.patient)} className="primary-button">Open Consultation Notes</button>
                                        <button onClick={() => handleStaffUpdateStatus(inConsultancy.id, 'skipped')} className="secondary-button" style={{backgroundColor: 'var(--status-skipped)', marginTop:'0.5rem'}}>Mark as Skipped</button>
                                         <button onClick={() => handleStaffUpdateStatus(inConsultancy.id, 'cancelled')} className="cancel-button" style={{marginTop:'0.5rem'}}>Cancel Token</button>
                                     </div>
                                </div> 
                           </div>
                           <hr className="queue-divider" />
                      </div>
                 )}

                <div className="card">
                    <h2 className="queue-section-title">Ready for Consultation ({confirmedPatients.length})</h2>
                    {!loading && (
                        <div className="table-container">
                            {confirmedPatients.length > 0 ? (
                                <table className="patient-table">
                                    <thead>
                                        <tr>
                                            <th>Token</th>
                                            <th>Patient</th>
                                            <th>Age</th>
                                            <th>Time</th>
                                            <th>Status</th>
                                            <th>Start</th>
                                            <th>History</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {confirmedPatients.map((token) => (
                                            <tr key={token.id} className={`${token.id === nextPatientTokenId && !inConsultancy ? 'next-patient-row' : ''}`}>
                                                <td className="token-cell">#{token.token_number || (token.appointment_time ? 'Scheduled' : 'Walk-in')}</td>
                                                <td className="patient-cell">{token.patient?.name || 'Unknown'}</td>
                                                <td>{token.patient?.age || 'N/A'}</td>
                                                <td>{token.appointment_time ? formatTime(token.appointment_time) : 'Walk-in'}</td>
                                                <td><span className="status-badge status-confirmed">Confirmed</span></td>
                                                <td>
                                                    {!inConsultancy ? (
                                                        <button onClick={() => handleStartConsultation(token)} className="table-btn start-btn">Start</button>
                                                    ) : (
                                                        <span className="disabled-text">Wait</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <button onClick={() => onViewHistory(token.patient)} className="table-btn history-btn">History</button>
                                                </td>
                                                <td>
                                                    <button onClick={() => handleStaffUpdateStatus(token.id, 'skipped')} className="table-btn skip-btn">Skip</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p>No patients are currently confirmed and waiting.</p>
                            )}
                        </div>
                    )}
                    
                    <hr className="queue-divider" />
                    <h2 className="queue-section-title">Waiting for Arrival ({waitingPatients.length})</h2>
                    {!loading && (
                        <div className="table-container">
                            {waitingPatients.length > 0 ? (
                                <table className="patient-table">
                                    <thead>
                                        <tr>
                                            <th>Token</th>
                                            <th>Patient</th>
                                            <th>Age</th>
                                            <th>Time</th>
                                            <th>Status</th>
                                            <th>Start</th>
                                            <th>History</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {waitingPatients.map((token) => (
                                            <tr key={token.id}>
                                                <td className="token-cell">#{token.token_number || (token.appointment_time ? 'Scheduled' : 'Walk-in')}</td>
                                                <td className="patient-cell">{token.patient?.name || 'Unknown'}</td>
                                                <td>{token.patient?.age || 'N/A'}</td>
                                                <td>{token.appointment_time ? formatTime(token.appointment_time) : 'Walk-in'}</td>
                                                <td><span className="status-badge status-waiting">Waiting</span></td>
                                                <td><span className="disabled-text">Not Arrived</span></td>
                                                <td>
                                                    <button onClick={() => onViewHistory(token.patient)} className="table-btn history-btn">History</button>
                                                </td>
                                                <td>
                                                    <button onClick={() => handleStaffUpdateStatus(token.id, 'cancelled')} className="table-btn cancel-btn">Cancel</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p>No patients are currently waiting for arrival confirmation.</p>
                            )}
                        </div>
                    )}
                    
                    {/* Debug info for development */}
                    <div style={{marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0', fontSize: '12px'}}>
                        <strong>Debug Info:</strong><br/>
                        Total queue items: {safeQueue.length}<br/>
                        Confirmed: {confirmedPatients.length}<br/>
                        Waiting: {waitingPatients.length}<br/>
                        In consultancy: {inConsultancy ? 1 : 0}<br/>
                        Loading: {loading ? 'Yes' : 'No'}<br/>
                        Error: {error || 'None'}<br/>
                        Auth token: {localStorage.getItem('authToken') ? 'Present' : 'Missing'}<br/>
                        User role: {loggedInUser?.user?.role || 'Unknown'}<br/>
                        User name: {loggedInUser?.user?.name || 'Unknown'}
                        <br/><button onClick={fetchQueue} style={{marginTop: '10px', padding: '5px 10px'}}>Refresh Queue</button>
                    </div>
                </div>
            </div>
        </div> 
    );
};

const ConsultationComponent = ({ patient, doctor, onBack }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [notes, setNotes] = useState('');
    const [saveError, setSaveError] = useState(''); 
    const [isSaving, setIsSaving] = useState(false); 
    
    const [prescriptionItems, setPrescriptionItems] = useState([
        { medicine_name: '', dosage: '', duration_days: '', timing_morning: false, timing_afternoon: false, timing_evening: false }
    ]);

    const fetchHistory = useCallback(async () => {
        if (!patient) return;
        setLoading(true); setError('');
        try {
            const response = await apiClient.get(`/history/${patient.id}/`);
            setHistory(response.data);
        } catch (err) {
            setError('Could not fetch patient history.');
            console.error("Fetch history error:", err.response || err);
        } finally { setLoading(false); }
    }, [patient]);

    useEffect(() => { fetchHistory(); }, [fetchHistory]);

    const handlePrescriptionChange = (index, event) => {
        const values = [...prescriptionItems];
        const { name, value, type, checked } = event.target;
        values[index][name] = type === 'checkbox' ? checked : value;
        setPrescriptionItems(values);
    };

    const handleAddPrescriptionRow = () => {
        setPrescriptionItems([...prescriptionItems, { medicine_name: '', dosage: '', duration_days: '', timing_morning: false, timing_afternoon: false, timing_evening: false }]);
    };
    
    const handleRemovePrescriptionRow = (index) => {
        if (prescriptionItems.length > 1) { 
            const values = [...prescriptionItems];
            values.splice(index, 1);
            setPrescriptionItems(values);
        }
    };

    const handleSaveConsultation = async (e) => {
        e.preventDefault();
        setSaveError(''); 
        setIsSaving(true); 

        const validPrescriptionItems = prescriptionItems.filter(item => 
             item.medicine_name.trim() || item.dosage.trim() || item.duration_days.trim()
        );

        let prescriptionIsValid = true;
        validPrescriptionItems.forEach(item => {
             if (!item.medicine_name.trim() || !item.dosage.trim() || !item.duration_days.trim()) {
                 prescriptionIsValid = false;
             }
             if (isNaN(parseInt(item.duration_days)) || parseInt(item.duration_days) <= 0) {
                  prescriptionIsValid = false;
             }
        });

        if (!notes.trim()) {
             setSaveError('Consultation notes cannot be empty.');
             setIsSaving(false);
             return;
        }

        if (!prescriptionIsValid && validPrescriptionItems.length > 0) {
            setSaveError('Please fill in Medicine Name, Dosage, and a valid number of Days for all added prescription items.');
            setIsSaving(false);
            return;
        }

        const payload = {
            patient: patient.id,
            notes: notes.trim(),
            prescription_items: validPrescriptionItems.map(item => ({
                 ...item,
                 duration_days: parseInt(item.duration_days) 
            })) 
        };

        try {
            await apiClient.post('/consultations/create/', payload);
            onBack(); 
        } catch (err) {
            setSaveError(err.response?.data?.error || 'Failed to save consultation.');
            console.error("Save consultation error:", err.response || err);
            setIsSaving(false); 
        }
    };

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                 <h1>Consultation: {patient?.name || 'Loading...'} (Age: {patient?.age || 'N/A'})</h1>
                 <button onClick={onBack} className="logout-button" disabled={isSaving}>Back to Dashboard</button>
            </header>
            <div className="consultation-content">
                <div className="card history-card">
                    <h2>Patient History</h2>
                    {/* <-- ADDED: AI Summary component so doctor can summarize a patient's history */}
                    {patient && (
                        <PatientAISummary patientId={patient.id} token={localStorage.getItem('authToken')} />)}

                    {loading && <p>Loading history...</p>}
                    {error && <p className="error-message">{error}</p>}
                    {!loading && !error && (history.length > 0 ? (
                        <ul className="history-list">{history.map(c => (
                            <li key={c.id} className="history-item">
                                <p><strong>Date:</strong> {new Date(c.date).toLocaleDateString()}</p>
                                <p><strong>Doctor:</strong> {c.doctor.name}</p>
                                <p><strong>Notes:</strong> {c.notes}</p>
                                {c.prescription_items && c.prescription_items.length > 0 && (
                                    <>
                                        <p><strong>Prescription:</strong></p>
                                        <ul className="prescription-detail-list">
                                            {c.prescription_items.map(item => (
                                                <li key={item.id}>
                                                     {item.medicine_name} - {item.dosage} ({item.duration_days} days)
                                                     <small style={{marginLeft: '10px', color: 'var(--dark-gray)'}}>
                                                          ({item.timing_morning ? 'M' : ''}{item.timing_afternoon ? 'A' : ''}{item.timing_evening ? 'E' : ''})
                                                     </small>
                                                </li>
                                            ))}
                                        </ul>
                                    </>
                                )}
                            </li>
                        ))}</ul>
                    ) : (<p>No past consultations found for this patient.</p>))}
                </div>
                <div className="card form-card">
                    <h2>Add New Consultation</h2>
                    <form onSubmit={handleSaveConsultation}>
                        <div className="input-group">
                            <label>Consultation Notes</label>
                            <textarea rows="5" value={notes} onChange={(e) => setNotes(e.target.value)} required disabled={isSaving}></textarea>
                        </div>
                        
                        <h3>Prescription</h3>
                        {prescriptionItems.map((item, index) => (
                            <div className="prescription-row" key={index}>
                                <input type="text" name="medicine_name" placeholder="Medicine Name" value={item.medicine_name} onChange={e => handlePrescriptionChange(index, e)} className="presc-input-med" disabled={isSaving} />
                                <input type="text" name="dosage" placeholder="Dosage (e.g., 1 tablet)" value={item.dosage} onChange={e => handlePrescriptionChange(index, e)} className="presc-input-short" disabled={isSaving} />
                                <input type="number" name="duration_days" placeholder="Days" value={item.duration_days} onChange={e => handlePrescriptionChange(index, e)} className="presc-input-short" min="1" disabled={isSaving}/> {/* Added min="1" */}
                                <div className="timing-checkboxes">
                                    <label title="Morning"><input type="checkbox" name="timing_morning" checked={item.timing_morning} onChange={e => handlePrescriptionChange(index, e)} disabled={isSaving} /> M</label>
                                    <label title="Afternoon"><input type="checkbox" name="timing_afternoon" checked={item.timing_afternoon} onChange={e => handlePrescriptionChange(index, e)} disabled={isSaving} /> A</label>
                                    <label title="Evening"><input type="checkbox" name="timing_evening" checked={item.timing_evening} onChange={e => handlePrescriptionChange(index, e)} disabled={isSaving} /> E</label>
                                </div>
                                {prescriptionItems.length > 1 && 
                                    <button 
                                            type="button" 
                                            onClick={() => handleRemovePrescriptionRow(index)} 
                                            className="remove-button"
                                            title="Remove this item"
                                            disabled={isSaving}>×</button>
                                }
                                {prescriptionItems.length <= 1 && <div style={{width: '30px'}}></div>} 
                            </div>
                        ))}
                        <button type="button" onClick={handleAddPrescriptionRow} className="secondary-button add-med-button" disabled={isSaving}>Add Another Medicine</button>
                        
                        {saveError && <p className="error-message">{saveError}</p>}
                        
                        <button type="submit" className="primary-button save-consult-button" disabled={isSaving}>
                             {isSaving ? 'Saving...' : 'Save & Complete Appointment'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

const PatientHistoryComponent = ({ patient, onBack }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchHistory = useCallback(async () => {
        if (!patient) return;
        setLoading(true); setError('');
        try {
            const response = await apiClient.get(`/history/${patient.id}/`);
            setHistory(response.data);
        } catch (err) {
            setError('Could not fetch patient history.');
            console.error("Fetch history error:", err.response || err);
        } finally { setLoading(false); }
    }, [patient]);

    useEffect(() => { fetchHistory(); }, [fetchHistory]);

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Patient History: {patient?.name || 'Loading...'} (Age: {patient?.age || 'N/A'})</h1>
                <button onClick={onBack} className="logout-button">Back to Dashboard</button>
            </header>
            <div className="dashboard-content">
                <div className="card">
                    <h2>Consultation History</h2>
                    {loading && <p>Loading history...</p>}
                    {error && <p className="error-message">{error}</p>}
                    {!loading && !error && (history.length > 0 ? (
                        <ul className="history-list">{history.map(c => (
                            <li key={c.id} className="history-item">
                                <p><strong>Date:</strong> {new Date(c.date).toLocaleDateString()}</p>
                                <p><strong>Doctor:</strong> {c.doctor.name}</p>
                                <p><strong>Notes:</strong> {c.notes}</p>
                                {c.prescription_items && c.prescription_items.length > 0 && (
                                    <>
                                        <p><strong>Prescription:</strong></p>
                                        <ul className="prescription-detail-list">
                                            {c.prescription_items.map(item => (
                                                <li key={item.id}>
                                                     {item.medicine_name} - {item.dosage} ({item.duration_days} days)
                                                     <small style={{marginLeft: '10px', color: 'var(--dark-gray)'}}>
                                                          ({item.timing_morning ? 'M' : ''}{item.timing_afternoon ? 'A' : ''}{item.timing_evening ? 'E' : ''})
                                                     </small>
                                                </li>
                                            ))}
                                        </ul>
                                    </>
                                )}
                            </li>
                        ))}</ul>
                    ) : (<p>No past consultations found for this patient.</p>))}
                </div>
            </div>
        </div>
    );
};

const PatientDashboardComponent = ({ loggedInUser, onLogout }) => {
    const [currentToken, setCurrentToken] = useState(null);
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(true);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [clinics, setClinics] = useState([]);
    const [selectedClinicId, setSelectedClinicId] = useState('');
    const [selectedDoctorId, setSelectedDoctorId] = useState('');
    const [liveQueue, setLiveQueue] = useState([]);
    const [availableSlots, setAvailableSlots] = useState([]);
    const [selectedSlot, setSelectedSlot] = useState('');
    const today = new Date().toISOString().split('T')[0];
    const [bookingDate, setBookingDate] = useState(today);
    const [isVerifying, setIsVerifying] = useState(false);
    const [isHistoryVisible, setIsHistoryVisible] = useState(false);
    const [confirmationWindowMessage, setConfirmationWindowMessage] = useState('');
    const [isWithinConfirmationWindow, setIsWithinConfirmationWindow] = useState(false);

    const InfoItem = ({ icon, label, value }) => ( <div className="info-item"><div className="info-icon">{icon}</div><div className="info-text"><strong>{value}</strong><span>{label}</span></div></div> );
    const ClockIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 6v6l4 2"/><circle cx="12" cy="12" r="10"/></svg>;
    const TicketIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5-2.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 010 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 010-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375z" /></svg>;
    const DoctorIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>;
    const ClinicIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m0 0v12m0-12L3 15" /></svg>;
    const StatusIcon = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    
    const fetchTodaysToken = useCallback(async () => { try { const response = await apiClient.get('/tokens/get_my_token/'); setCurrentToken(response.data); } catch (err) { setCurrentToken(null); } }, []);
    const fetchAllData = useCallback(async () => { try { const [tokenRes, clinicsRes, historyRes] = await Promise.all([ apiClient.get('/tokens/get_my_token/').catch(() => ({ data: null })), apiClient.get('/clinics_with_doctors/'), apiClient.get('/history/my_history/') ]); setCurrentToken(tokenRes.data); setClinics(clinicsRes.data); setHistory(historyRes.data); } catch (err) { setError('Could not load your dashboard data.'); } finally { setLoadingHistory(false); } }, []);
    
    useEffect(() => { 
        fetchAllData(); 
        const interval = setInterval(fetchTodaysToken, 10000); 
        return () => clearInterval(interval); 
    }, [fetchAllData, fetchTodaysToken]);
    
    useEffect(() => {
        const fetchSlots = async () => {
            if (selectedDoctorId && bookingDate) {
                try {
                    setError('');
                    const response = await apiClient.get(`/doctors/${selectedDoctorId}/available-slots/${bookingDate}/`);
                    setAvailableSlots(response.data);
                } catch (err) {
                    setError('Could not fetch available slots for the selected date.');
                    setAvailableSlots([]);
                }
            } else {
                setAvailableSlots([]);
            }
        };
        fetchSlots();
    }, [selectedDoctorId, bookingDate]);
    
    useEffect(() => {
        const fetchLiveQueue = async () => {
            let doctorId = null;
            let queueDate = today;
            
            if (currentToken && currentToken.doctor_id && currentToken.status !== 'completed' && currentToken.status !== 'cancelled') {
                doctorId = currentToken.doctor_id;
                queueDate = currentToken.date;
            } else if (selectedDoctorId) {
                doctorId = selectedDoctorId;
                queueDate = bookingDate;
            }
            
            if (doctorId) {
                try {
                    const response = await apiClient.get(`/patient/queue/${doctorId}/${queueDate}`); 
                    setLiveQueue(response.data);
                } catch (err) {
                    console.error("Could not fetch live queue.");
                    setLiveQueue([]); 
                }
            } else {
                setLiveQueue([]); 
            }
        };
        fetchLiveQueue(); 
        const queueInterval = setInterval(fetchLiveQueue, 7000); 
        return () => clearInterval(queueInterval);
    }, [currentToken, selectedDoctorId, bookingDate, today]); 

    // --- MODIFIED: Wrapped formatTime in useCallback ---
    const formatTime = useCallback((timeStr) => {
        if (!timeStr) return '';
        const [hour, minute] = timeStr.split(':');
        if (isNaN(hour) || isNaN(minute)) return 'Invalid';
        const h = parseInt(hour, 10);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const formattedHour = h % 12 === 0 ? 12 : h % 12;
        const formattedMinute = String(minute).padStart(2, '0');
        return `${formattedHour}:${formattedMinute} ${ampm}`;
    }, []); 

    // --- NEW: Helper function to get today's date string ---
    const getTodayDateString = () => {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    useEffect(() => {
        const checkConfirmationWindow = () => {
            // Only check if the token date is today
            if (currentToken && currentToken.appointment_time && currentToken.status === 'waiting' && currentToken.date === getTodayDateString()) {
                const now = new Date();
                const parts = currentToken.appointment_time.split(':');
                if (parts.length < 2) return;
                const [hour, minute] = parts;
                const h = parseInt(hour, 10);
                const m = parseInt(minute, 10);
                if (isNaN(h) || isNaN(m)) return;
                const appointmentTime = new Date(); 
                appointmentTime.setHours(h, m, 0, 0); 

                const startWindow = new Date(appointmentTime.getTime() - 20 * 60000); // 20 mins before
                const endWindow = new Date(appointmentTime.getTime() + 15 * 60000);   // 15 mins after

                if (now >= startWindow && now <= endWindow) {
                    setIsWithinConfirmationWindow(true);
                    setConfirmationWindowMessage('');
                } else if (now < startWindow) {
                    setIsWithinConfirmationWindow(false);
                    setConfirmationWindowMessage(`You can confirm arrival starting from ${formatTime(startWindow.toTimeString().substring(0,5))}`); 
                } else { // now > endWindow
                    setIsWithinConfirmationWindow(false);
                    setConfirmationWindowMessage('Your confirmation window has passed.');
                }
            } else {
                setIsWithinConfirmationWindow(false);
                setConfirmationWindowMessage('');
            }
        };

        checkConfirmationWindow(); 
        const windowInterval = setInterval(checkConfirmationWindow, 30000); 
        return () => clearInterval(windowInterval);
    }, [currentToken, formatTime]); 
    
    const handleConfirmArrival = async () => {
        setMessage('');
        setError('');
        setIsVerifying(true);
        if (!navigator.geolocation) {
            setError("Geolocation is not supported by your browser.");
            setIsVerifying(false);
            return;
        }
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                try {
                    const response = await apiClient.post('/tokens/confirm_arrival/', { latitude, longitude });
                    if (response.data && response.data.token) {
                        setCurrentToken(response.data.token); 
                        setMessage(response.data.message || 'Arrival confirmed successfully!');
                    } else {
                        throw new Error("Invalid response structure from server.");
                    }
                } catch (err) {
                    setError(err.response?.data?.error || 'Could not confirm arrival. Please ensure you are within 1km of the clinic.');
                    console.error("Confirm arrival error:", err.response || err);
                } finally {
                    setIsVerifying(false);
                }
            },
            (geoError) => {
                let geoErrorMessage = "Could not get your location.";
                if (geoError.code === 1) { 
                    geoErrorMessage = "Location permission denied. Please enable location services in your browser/phone settings.";
                } else if (geoError.code === 2) {
                     geoErrorMessage = "Location information is unavailable. Please check your network or GPS.";
                } else if (geoError.code === 3) {
                     geoErrorMessage = "Location request timed out.";
                }
                setError(geoErrorMessage);
                setIsVerifying(false);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 } 
        );
    };

    const handlePatientCancelToken = async () => { 
        setMessage(''); 
        setError(''); 
        try { 
             const response = await apiClient.post('/tokens/patient_cancel/'); 
            setMessage(response.data.message); 
            setCurrentToken(null); 
        } catch (err) { 
            setError(err.response?.data?.error || 'Could not cancel token.'); 
            console.error("Cancel token error:", err.response || err);
        } 
    };

    const handleBookAppointment = async (e) => { 
        e.preventDefault(); 
        setMessage(''); 
        setError(''); 
        if (!selectedDoctorId || !selectedSlot || !bookingDate) { 
            setError('Please select a clinic, doctor, date, and time slot.'); 
            return; 
        } 
        try { 
            const response = await apiClient.post('/tokens/patient_create/', { 
                doctor_id: selectedDoctorId,
                date: bookingDate,
                time: selectedSlot
            }); 

            // --- START OF FIX ---
            const newPartialToken = response.data; 

            const currentClinic = clinics.find(c => String(c.id) === String(selectedClinicId));
            const currentDoctor = currentClinic?.doctors.find(d => String(d.id) === String(selectedDoctorId));

            const fullToken = {
                ...newPartialToken, 
                date: bookingDate,  
                
                // Add the full objects for display
                doctor: currentDoctor ? { name: currentDoctor.name } : { name: "Unknown" },
                clinic: currentClinic ? { name: currentClinic.name } : { name: "Unknown" },

                // Add the missing IDs for the live queue to work
                doctor_id: selectedDoctorId,
                clinic_id: selectedClinicId
            };

            setCurrentToken(fullToken);
            // --- END OF FIX ---

            setMessage('Appointment booked successfully!'); 
            setSelectedClinicId('');
            setSelectedDoctorId('');
            setSelectedSlot('');
            setBookingDate(today); 
            setAvailableSlots([]); 
        } catch (err) { 
            setError(err.response?.data?.error || 'Could not book appointment. Slot might be taken or you may already have an appointment.'); 
            console.error("Booking error:", err.response || err);
            if (selectedDoctorId && bookingDate) {
                try {
                    const slotResponse = await apiClient.get(`/doctors/${selectedDoctorId}/available-slots/${bookingDate}/`);
                    setAvailableSlots(slotResponse.data);
                } catch (slotErr) { /* Ignore slot fetch error here */ }
            }
        } 
    };
    const handleClinicChange = (clinicId) => { 
        setSelectedClinicId(clinicId); 
        setSelectedDoctorId(''); 
        setSelectedSlot(''); 
        setAvailableSlots([]); 
    };
    const handleDoctorChange = (doctorId) => {
         setSelectedDoctorId(doctorId);
         setSelectedSlot(''); 
         setAvailableSlots([]); 
    };
     const handleDateChange = (date) => {
         setBookingDate(date);
         setSelectedSlot(''); 
         setAvailableSlots([]); 
    };
    
    const doctorsOfSelectedClinic = clinics.find(c => String(c.id) === String(selectedClinicId))?.doctors || [];

    const toggleHistoryView = () => {
        setIsHistoryVisible(prevState => !prevState);
    };
    
    const currentTimeForFilter = new Date();
    const futureSlots = availableSlots.filter(slot => {
        if (bookingDate === new Date().toISOString().split('T')[0]) { 
            const parts = slot.split(':');
            if (parts.length < 2) return false;
            const [hour, minute] = parts;
            const h = parseInt(hour, 10);
            const m = parseInt(minute, 10);
            if (isNaN(h) || isNaN(m)) return false;
            const slotTime = new Date();
            slotTime.setHours(h, m, 0, 0);
            return slotTime >= currentTimeForFilter; 
        }
        return true; 
    });

    return ( 
        <div className="dashboard-container patient-dashboard">
            <header className="dashboard-header">
                <h1>Patient Portal</h1>
                <div className="user-info">
                    <span>Welcome, {loggedInUser.user.name}</span>
                    <button onClick={onLogout} className="logout-button">Logout</button>
                </div>
            </header>
            <div className={`patient-dashboard-layout ${isHistoryVisible ? 'history-visible' : ''}`}>
                <div className="patient-main-content">
                    <div className="card">
                        {/* --- MODIFIED: Show "Today's Status" or "Upcoming Appointment" --- */}
                        <h2>{currentToken?.date === getTodayDateString() ? "Your Status Today" : (currentToken ? "Your Upcoming Appointment" : "Book an Appointment")}</h2>
                        
                        {message && <p className="success-message" style={{display:'block'}}>{message}</p>} 
                        {error && <p className="error-message">{error}</p>}
                        
                        <button onClick={toggleHistoryView} className="secondary-button view-history-button">
                            {isHistoryVisible ? 'Hide History' : 'View Consultation History'}
                        </button>

                        {currentToken ? ( 
                            <div className="info-card">
                                {/* --- NEW: Show Date --- */}
                                <InfoItem icon={<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>} 
                                    label="Appointment Date" 
                                    value={new Date(currentToken.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} />

                                {currentToken.appointment_time && <InfoItem icon={<ClockIcon />} label="Appointment Time" value={formatTime(currentToken.appointment_time)} />}
                                {currentToken.token_number && <InfoItem icon={<TicketIcon />} label="Token #" value={`${currentToken.token_number}`} />}
                                {currentToken.doctor && <InfoItem icon={<DoctorIcon />} label="Doctor" value={currentToken.doctor.name} />}
                                {currentToken.clinic && <InfoItem icon={<ClinicIcon />} label="Clinic" value={currentToken.clinic.name} />}
                                <InfoItem icon={<StatusIcon />} label="Status" value={<span className={`status-badge status-${currentToken.status}`}>{currentToken.status.replace(/_/g, ' ')}</span>} />
                                
                                {/* --- MODIFIED: Only show "Confirm Arrival" if token is for TODAY --- */}
                                {currentToken.status === 'waiting' && currentToken.date === getTodayDateString() && (
                                    <div style={{gridColumn: '1 / -1'}}> 
                                        <button 
                                            onClick={handleConfirmArrival} 
                                            className="primary-button confirm-button"
                                            disabled={isVerifying || !isWithinConfirmationWindow}
                                        >
                                            {isVerifying ? 'Verifying Location...' : 'Confirm My Arrival (GPS)'}
                                        </button>
                                        {confirmationWindowMessage && <p className="confirmation-window-message">{confirmationWindowMessage}</p>}
                                    </div>
                                )}
                                {['waiting', 'confirmed'].includes(currentToken.status) && (
                                     <div style={{gridColumn: '1 / -1'}}>
                                         <button onClick={handlePatientCancelToken} className="cancel-button">Cancel My Token</button>
                                     </div>
                                )}
                            </div> 
                        ) : ( 
                            <div className="form-card no-border">
                                <h2>Book a New Appointment</h2>
                                <form onSubmit={handleBookAppointment}>
                                    <div className="input-group">
                                        <label>Select Clinic</label>
                                        <select value={selectedClinicId} onChange={(e) => handleClinicChange(e.target.value)} required>
                                            <option value="">-- Choose a clinic --</option>
                                            {clinics.map(clinic => (<option key={clinic.id} value={clinic.id}>{clinic.name} - {clinic.city}</option>))}
                                        </select>
                                    </div>
 
                                    {selectedClinicId && (
                                        <div className="input-group">
                                            <label>Select Doctor</label>
                                            <select value={selectedDoctorId} onChange={(e) => handleDoctorChange(e.target.value)} required>
                                                <option value="">-- Choose a doctor --</option>
                                                {doctorsOfSelectedClinic.map(doctor => (<option key={doctor.id} value={doctor.id}>{doctor.name} - {doctor.specialization}</option>))}
                                            </select>
                                        </div>
                                    )}
                                    {selectedDoctorId && (
                                        <>
                                            <div className="input-group">
                                                <label>Select Date</label>
                                                <input
                                                    type="date"
                                                    value={bookingDate}
                                                    min={today} 
                                                    onChange={(e) => handleDateChange(e.target.value)}
                                                    required
                                                />
                                            </div>
                                            <div className="input-group">
                                                <label>Select an Available Time</label>
                                                <div className="time-slots-container">
                                                    {futureSlots.length > 0 ? (
                                                        futureSlots.map(slot => (
                                                            <button 
                                                                type="button" 
                                                                key={slot} 
                                                                className={`time-slot-btn ${selectedSlot === slot ? 'selected' : ''}`}
                                                                onClick={() => setSelectedSlot(slot)} 
                                                            >
                                                                {formatTime(slot)}
                                                            </button>
                                                        ))
                                                    ) : <p>No available slots found for this doctor on {bookingDate}.</p>}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                    <button type="submit" className="primary-button" disabled={!selectedSlot || !selectedDoctorId || !bookingDate}>Book Appointment</button>
                                </form>
                            </div> 
                        )}
                    </div>

                    {/* Show Live Queue for current appointment or when booking */}
                    {((currentToken && currentToken.status !== 'completed' && currentToken.status !== 'cancelled' && currentToken.date === getTodayDateString()) || selectedDoctorId) && (
                        <div className="card">
                            <h2>Live Queue for Dr. {currentToken?.doctor?.name || (selectedDoctorId && doctorsOfSelectedClinic.find(d => String(d.id) === String(selectedDoctorId))?.name) || '...'}</h2>
                            <div className="table-container">
                                {liveQueue.length > 0 ? (
                                    <table className="patient-table">
                                        <thead>
                                            <tr>
                                                <th>Position</th>
                                                <th>Token</th>
                                                <th>Patient</th>
                                                <th>Time</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {liveQueue.map((token, index) => (
                                                <tr key={token.id} className={`${currentToken && String(token.id) === String(currentToken.id) ? 'my-token-row' : ''}`}>
                                                    <td>{index + 1}</td>
                                                    <td className="token-cell">#{token.token_number || (token.appointment_time ? 'Scheduled' : 'Walk-in')}</td>
                                                    <td className="patient-cell">{token.patient?.name || 'Patient'}</td>
                                                    <td>{token.appointment_time ? formatTime(token.appointment_time) : 'Walk-in'}</td>
                                                    <td><span className={`status-badge status-${token.status}`}>{token.status.replace(/_/g, ' ')}</span></td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : <p>The queue is currently empty or loading...</p>}
                            </div>
                        </div>
                    )}
                </div>

                {isHistoryVisible && (
                    <div className="patient-sidebar">
                        <div className="card">
                            <h2>Consultation History</h2>
                            {loadingHistory ? <p>Loading history...</p> : ( 
                                history.length > 0 ? ( 
                                    <ul className="history-list">{history.map(c => ( 
                                        <li key={c.id} className="history-item">
                                            <p><strong>Date:</strong> {new Date(c.date).toLocaleDateString()}</p>
                                            <p><strong>Doctor:</strong> {c.doctor.name}</p>
                                            <p><strong>Notes:</strong> {c.notes}</p>
                                            {c.prescription_items && c.prescription_items.length > 0 && (
                                                <>
                                                    <p><strong>Prescription:</strong></p>
                                                    <ul className="prescription-detail-list">
                                                        {c.prescription_items.map(item => (
                                                             <li key={item.id}>
                                                                  {item.medicine_name} - {item.dosage} ({item.duration_days} days)
                                                                  <small style={{marginLeft: '10px', color: 'var(--dark-gray)'}}>
                                                                       ({item.timing_morning ? 'M' : ''}{item.timing_afternoon ? 'A' : ''}{item.timing_evening ? 'E' : ''})
                                                                  </small>
                                                             </li>
                                                        ))}
                                                    </ul>
                                                </>
                                            )}
                                        </li> 
                                    ))}</ul> 
                                ) : (<p>No past consultations found.</p>)
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div> 
    );
};


const AnalyticsDashboardComponent = ({ onBack }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    useEffect(() => { const fetchAnalytics = async () => { try { const response = await apiClient.get('/analytics/'); setStats(response.data); } catch (err) { setError('Could not load analytics data.'); } finally { setLoading(false); } }; fetchAnalytics(); }, []);
    if (loading) return <div className="loading-screen">Loading Analytics...</div>;
    if (error) return <div className="error-banner">{error}</div>;
    if (!stats) return <div className="loading-screen">No analytics data available.</div>; 
    
    const breakdown = stats.patient_status_breakdown || {};
    const waiting = breakdown.waiting || 0;
    const confirmed = breakdown.confirmed || 0;
    const completed = breakdown.completed || 0;
    
    const totalForPie = waiting + confirmed + completed;
    const completedPercent = totalForPie > 0 ? (completed / totalForPie) * 100 : 0;
    const confirmedPercent = totalForPie > 0 ? (confirmed / totalForPie) * 100 : 0;
    const confirmedEndPercent = Math.min(100, completedPercent + confirmedPercent);
    const waitingEndPercent = 100; 

    const pieGradient = { background: `conic-gradient(var(--status-completed) 0% ${completedPercent}%, var(--status-confirmed) ${completedPercent}% ${confirmedEndPercent}%, var(--status-waiting) ${confirmedEndPercent}% ${waitingEndPercent}%)` };
    
    const workload = stats.doctor_workload || [];
    const maxWorkload = Math.max(...workload.map(d => d.count), 0);
    
    return ( 
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Clinic Analytics for {stats.clinic_name || 'Your Clinic'}</h1>
                <div className="user-info">
                    <span>{stats.date || new Date().toLocaleDateString()}</span>
                    <button onClick={onBack} className="logout-button">Back to Dashboard</button>
                </div>
            </header>
            <div className="analytics-content">
                <div className="stats-grid">
                    <div className="stat-card"><h3>Total Patients Today</h3><p>{stats.total_patients || 0}</p></div>
                    <div className="stat-card"><h3>Avg. Wait Time</h3><p>{stats.average_wait_time_minutes != null ? `${stats.average_wait_time_minutes} min` : 'N/A'}</p></div>
                </div>
                <div className="charts-container">
                    <div className="card">
                        <h2>Doctor Workload Today</h2>
                        <div className="workload-chart">
                            {workload.length > 0 ? workload.map(doc => ( 
                                <div key={doc.doctor__name || `doc-${Math.random()}`} className="workload-bar-item"> 
                                    <div className="bar-label">{doc.doctor__name || 'Unknown Doctor'} ({doc.count || 0})</div>
                                    <div className="bar-container">
                                        <div className="bar" style={{ width: `${maxWorkload > 0 ? (doc.count / maxWorkload) * 100 : 0}%` }}></div>
                                    </div>
                                </div> 
                            )) : <p>No doctor activity recorded today.</p>}
                        </div>
                    </div>
                    <div className="card">
                        <h2>Patient Status Breakdown</h2>
                        <div className="pie-chart-container">
                            <div className="pie-chart" style={pieGradient}>
                                <strong>{totalForPie}</strong><span>Total</span>
                            </div>
                            <ul className="pie-legend">
                                <li className="legend-item"><span className="legend-color" style={{backgroundColor: 'var(--status-completed)'}}></span>Completed ({completed})</li>
                                <li className="legend-item"><span className="legend-color" style={{backgroundColor: 'var(--status-confirmed)'}}></span>Confirmed ({confirmed})</li>
                                <li className="legend-item"><span className="legend-color" style={{backgroundColor: 'var(--status-waiting)'}}></span>Waiting ({waiting})</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div> 
    );
};


// ====================================================================
// 5. MAIN APP CONTROLLER
// ====================================================================

const useInactivityTimer = (logoutCallback, timeout = 15 * 60 * 1000) => {
    const timerRef = useRef();
    const resetTimer = useCallback(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(logoutCallback, timeout);
    }, [logoutCallback, timeout]);
    useEffect(() => {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        const resetActivity = () => resetTimer();
        events.forEach(event => window.addEventListener(event, resetActivity));
        resetTimer();
        return () => {
            events.forEach(event => window.removeEventListener(event, resetActivity));
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [resetTimer]);
};

function App() {
    const [loggedInUser, setLoggedInUser] = useState(null);
    const [selectedPatient, setSelectedPatient] = useState(null);
    const [viewingHistory, setViewingHistory] = useState(null);
    const [view, setView] = useState('home');
    const [successMessage, setSuccessMessage] = useState(''); // State for success message

    // Function to show the success message
    const showSuccessMessage = (message) => {
        setSuccessMessage(message);
        setTimeout(() => {
            setSuccessMessage('');
        }, 3000); 
    };

    const handleLogout = useCallback(() => {
        localStorage.clear();
        setLoggedInUser(null);
        setSelectedPatient(null);
        setView('home');
    }, []);

    useInactivityTimer(handleLogout);

    useEffect(() => {
        const savedUser = localStorage.getItem('loggedInUser');
        const token = localStorage.getItem('authToken');
        if (savedUser && token) {
             try { 
                 const parsed = JSON.parse(savedUser);
                 // Defensive: ensure we have expected shape and valid role
                 const validRoles = ['patient', 'doctor', 'receptionist'];
                 if (!parsed || !parsed.user || !parsed.user.role || !validRoles.includes(parsed.user.role)) {
                     console.warn('Saved user is missing role or malformed, clearing localStorage.', parsed);
                     localStorage.removeItem('authToken');
                     localStorage.removeItem('loggedInUser');
                     return;
                 }
                 setLoggedInUser(parsed);
                 setView('dashboard');
             } catch (e) {
                  console.error("Error parsing saved user data:", e);
                  localStorage.clear(); 
             }
        }
    }, []);

    const handleLoginSuccess = (data) => {
        try {
            console.log('handleLoginSuccess received:', data);
            if (!data || !data.token || !data.user || !data.user.role) {
                console.error('Invalid login data received:', data);
                showSuccessMessage('Login failed: invalid response from server. Please try again.');
                return;
            }
            
            // Validate role
            const validRoles = ['patient', 'doctor', 'receptionist'];
            if (!validRoles.includes(data.user.role)) {
                console.error('Invalid user role received:', data.user.role);
                showSuccessMessage('Login failed: invalid user role. Please contact support.');
                return;
            }
            
            // Defensive: ensure token is a string
            const token = typeof data.token === 'string' ? data.token : String(data.token);
            localStorage.setItem('authToken', token);
            localStorage.setItem('loggedInUser', JSON.stringify(data));
            setLoggedInUser(data);
            setView('dashboard');
        } catch (e) {
            console.error('Error handling login success:', e, data);
            showSuccessMessage('Login failed: unexpected error occurred.');
        }
    };
    
    const handleSelectPatient = (patient) => setSelectedPatient(patient);
    const handleViewHistory = (patient) => setViewingHistory(patient);
    const handleBackToDashboard = () => {
        setSelectedPatient(null);
        setViewingHistory(null);
    };

    const renderContent = () => {
        if (loggedInUser && loggedInUser.user && view === 'dashboard') {
            if (selectedPatient) {
                return <ConsultationComponent patient={selectedPatient} doctor={loggedInUser.user} onBack={handleBackToDashboard} />;
            }
            if (viewingHistory) {
                return <PatientHistoryComponent patient={viewingHistory} onBack={handleBackToDashboard} />;
            }
            const userRole = loggedInUser.user?.role; 
            switch (userRole) {
                case 'doctor':
                    return <DoctorDashboardComponent loggedInUser={loggedInUser} onLogout={handleLogout} onSelectPatient={handleSelectPatient} onViewHistory={handleViewHistory} onViewAnalytics={() => setView('analytics')} />;
                case 'receptionist':
                    return <ReceptionistDashboardComponent loggedInUser={loggedInUser} onLogout={handleLogout} onSelectPatient={handleSelectPatient} onViewHistory={handleViewHistory} onViewAnalytics={() => setView('analytics')} onManageSchedules={() => setView('schedules')} />;
                case 'patient':
                    return <PatientDashboardComponent loggedInUser={loggedInUser} onLogout={handleLogout} />;
                default:
                    // Defensive fallback: if role missing or unknown, clear localStorage and show login
                    console.warn("Unknown or missing user role:", userRole);
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('loggedInUser');
                    setLoggedInUser(null);
                    setView('login');
                    return <LoginPage apiClient={apiClient} onLoginSuccess={handleLoginSuccess} onSwitchToRegister={() => setView('register')} onBackToHome={() => setView('home')} showSuccessMessage={showSuccessMessage} />;
            }
        }
        
        if(view === 'analytics' && loggedInUser){
            return <AnalyticsDashboardComponent onBack={() => setView('dashboard')} />;
        }
        
        if(view === 'schedules' && loggedInUser){
            return <ScheduleManagement apiClient={apiClient} onBack={() => setView('dashboard')} />;
        }

        switch (view) {
            case 'login':
                return <LoginPage 
                          apiClient={apiClient}
                          onLoginSuccess={handleLoginSuccess} 
                          onSwitchToRegister={() => setView('register')} 
                          onBackToHome={() => setView('home')}
                          showSuccessMessage={showSuccessMessage} 
                       />;
            case 'register':
                return <PatientRegisterComponent 
                          onRegisterSuccess={handleLoginSuccess} 
                          onSwitchToLogin={() => setView('login')}
                          showSuccessMessage={showSuccessMessage} 
                       />;
            case 'home':
            default:
                return (
                    <div className="public-layout">
                        <PublicHeader onLoginClick={()=>setView('login')} onRegisterClick={()=>setView('register')} />
                        <PublicHomePage />
                        <PublicFooter onStaffLoginClick={() => setView('login')} />
                    </div>
                );
        }
    };

    return (
        <div className="App">
            {successMessage && <div className="success-overlay">{successMessage}</div>}
            {renderContent()}
        </div>
    );
}

export default App;