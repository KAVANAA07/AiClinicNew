import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './PublicHomePage.css'; // Uses the enhanced CSS

// Re-use the apiClient from your App.js
const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/',
});

// --- Helper function to get today's date in YYYY-MM-DD format ---
const getTodayDateString = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

// --- SVG Icons ---
const ClockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
    </svg>
);
const TicketIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
         <path d="M3 10V4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6" />
         <path d="M3 14v6a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6" />
         <path d="M10 10h4" />
         <path d="M10 14h4" />
         <path d="M8 7v10" />
         <path d="M16 7v10" />
         <path d="M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
         <path d="M16 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
    </svg>
);
const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
);


// --- Child Component: Live Queue View (MODIFIED) ---
const LiveQueueView = ({ doctor, onBack }) => {
    const [queue, setQueue] = useState([]);
    const [error, setError] = useState('');
    // --- NEW: State for the selected date, default to today ---
    const [selectedDate, setSelectedDate] = useState(getTodayDateString());

    // --- MODIFIED: fetchQueue now depends on selectedDate ---
    const fetchQueue = useCallback(async () => {
        setError(''); 
        try {
            // Use the new URL format with the selected date
            const response = await apiClient.get(`/patient/queue/${doctor.id}/${selectedDate}/`);
            setQueue(response.data);
        } catch (err) {
            setError(`Could not fetch the queue for ${selectedDate}. Please try again later.`);
            console.error(err);
        }
    }, [doctor.id, selectedDate]); // --- MODIFIED: Add selectedDate as dependency ---

    // --- MODIFIED: useEffect now triggers when selectedDate changes ---
    useEffect(() => {
        fetchQueue(); // Fetch immediately on load/date change
        
        // Auto-refresh only if the selected date is today
        let queueInterval = null;
        if (selectedDate === getTodayDateString()) {
             queueInterval = setInterval(fetchQueue, 7000); // Refresh every 7 seconds
        }
        
        return () => {
            if (queueInterval) {
                clearInterval(queueInterval); // Cleanup on component unmount or date change
            }
        };
    }, [fetchQueue, selectedDate]); // --- MODIFIED: Add selectedDate as dependency ---

    const formatTime = (timeStr) => {
        if (!timeStr) return 'Walk-in';
        const [hour, minute] = timeStr.split(':');
        if (isNaN(hour) || isNaN(minute)) return 'Invalid Time';
        const h = parseInt(hour, 10);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const formattedHour = h % 12 === 0 ? 12 : h % 12;
        return `${formattedHour}:${String(minute).padStart(2, '0')} ${ampm}`;
    };

    return (
        <div className="public-view-container">
            <button onClick={onBack} className="back-button-public">← Back to Doctors</button>
            <div className="card public-card">
                
                {/* --- NEW: Queue Header with Date Picker --- */}
                <div className="queue-header">
                    <div className="queue-header-title">
                        <h2 className="public-card-header">Queue for Dr. {doctor.name}</h2>
                        <p className="public-card-subheader">{doctor.specialization}</p>
                    </div>
                    <div className="queue-header-controls">
                        <label htmlFor="queue-date">Select Date</label>
                        <input 
                            type="date"
                            id="queue-date"
                            className="queue-date-picker"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                    </div>
                </div>
                {/* --- End of New Header --- */}

                <div className="live-queue-list">
                    {error && <p className="error-message">{error}</p>}
                    {!error && queue.length > 0 ? (
                        queue.map((token, index) => (
                            <div key={token.id} className={`queue-token-public status-${token.status}`}>
                                <div className="token-position">{index + 1}</div>
                                <div className="token-details">
                                    <span className="token-number-public">Token #{token.token_number || (token.appointment_time ? 'Timed' : 'Walk-in')}</span>
                                    <span className="token-time-public">{formatTime(token.appointment_time)}</span>
                                </div>
                                <div className={`token-status-public status-${token.status}`}>{token.status.replace('_', ' ')}</div>
                            </div>
                        ))
                    ) : (
                        <p>The queue is empty for {selectedDate}.</p>
                    )}
                </div>
            </div>
        </div>
    );
};


// --- Main Component: Public Home Page (MODIFIED) ---
function PublicHomePage() {
    const [clinics, setClinics] = useState([]);
    const [selectedClinic, setSelectedClinic] = useState(null);
    const [selectedDoctor, setSelectedDoctor] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    // --- NEW: State for search bars ---
    const [clinicSearch, setClinicSearch] = useState('');
    const [doctorSearch, setDoctorSearch] = useState('');

    useEffect(() => {
        const fetchClinics = async () => {
            try {
                // Use public endpoint
                const response = await apiClient.get('/public/clinics/'); 
                setClinics(response.data);
            } catch (err) {
                setError('Could not load clinic information. Please refresh the page.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchClinics();
    }, []);

    // --- NEW: Filtered lists logic ---
    const filteredClinics = clinics.filter(clinic => 
        clinic.name.toLowerCase().includes(clinicSearch.toLowerCase()) ||
        clinic.city.toLowerCase().includes(clinicSearch.toLowerCase())
    );

    const filteredDoctors = (selectedClinic?.doctors || []).filter(doctor =>
        doctor.name.toLowerCase().includes(doctorSearch.toLowerCase()) ||
        doctor.specialization.toLowerCase().includes(doctorSearch.toLowerCase())
    );

    if (loading) return <div className="loading-screen">Loading Clinics...</div>;
    if (error) return <div className="error-banner">{error}</div>;

    // --- Conditional Rendering Logic ---

    if (selectedDoctor) {
        return <LiveQueueView doctor={selectedDoctor} onBack={() => setSelectedDoctor(null)} />;
    }

    if (selectedClinic) {
        return (
            <div className="public-view-container">
                <button onClick={() => setSelectedClinic(null)} className="back-button-public">← Back to Clinics</button>
                <div className="card public-card">
                    <h2 className="public-card-header">Select a Doctor at {selectedClinic.name}</h2>
                    
                    {/* --- NEW: Doctor Search Bar --- */}
                    <div className="search-bar-container">
                         <SearchIcon />
                         <input 
                            type="text"
                            className="search-bar"
                            placeholder="Search by doctor name or specialization..."
                            value={doctorSearch}
                            onChange={(e) => setDoctorSearch(e.target.value)}
                         />
                    </div>

                    <div className="selection-grid">
                        {filteredDoctors.length > 0 ? (
                            filteredDoctors.map(doctor => (
                                <div key={doctor.id} className="selection-card doctor-card" onClick={() => setSelectedDoctor(doctor)}>
                                    <h3>Dr. {doctor.name}</h3>
                                    <p>{doctor.specialization}</p>
                                </div>
                            ))
                        ) : (
                            <p>No doctors found matching "{doctorSearch}".</p>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="public-view-container">
             <div className="card public-card">
                <h2 className="public-card-header">Select a Clinic to View Live Queues</h2>
                
                 {/* --- NEW: Clinic Search Bar --- */}
                 <div className="search-bar-container">
                     <SearchIcon />
                     <input 
                        type="text"
                        className="search-bar"
                        placeholder="Search by clinic name or city..."
                        value={clinicSearch}
                        onChange={(e) => setClinicSearch(e.target.value)}
                     />
                 </div>

                <div className="selection-grid">
                    {filteredClinics.length > 0 ? (
                        filteredClinics.map(clinic => (
                            <div key={clinic.id} className="selection-card clinic-card" onClick={() => {
                                setSelectedClinic(clinic);
                                setDoctorSearch(''); // Reset doctor search on new clinic
                            }}>
                                <h3>{clinic.name}</h3>
                                <p>{clinic.city}</p>
                                
                                {/* --- ENHANCED: Display AI-predicted stats --- */}
                                <div className="clinic-stats">
                                    <div className="stat-item ai-prediction" title="AI-Predicted Average Wait Time">
                                        <ClockIcon />
                                        <span className="ai-time">{clinic.average_wait_time} min</span>
                                        <small className="ai-label">AI Predicted</small>
                                    </div>
                                    <div className="stat-item" title="Total Patients Today">
                                        <TicketIcon />
                                        <span>{clinic.total_tokens} patients</span>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>No clinics found matching "{clinicSearch}".</p>
                    )}
                </div>
            </div>
        </div>
    );
}

export default PublicHomePage;

