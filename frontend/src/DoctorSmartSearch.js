// FILE: src/DoctorSmartSearch.js
import React, { useState } from 'react';
import axios from 'axios';

const DoctorSmartSearch = ({ clinicId, onDoctorFound }) => {
    const [symptoms, setSymptoms] = useState('');
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState('');

    const handleSearch = async () => {
        if (!symptoms || !clinicId) return alert("Please select a clinic and describe symptoms.");
        setLoading(true);
        setMsg("");
        
        try {
            const res = await axios.post('http://localhost:8000/api/recommend-doctor/', {
                symptoms: symptoms,
                clinic_id: clinicId
            });
            
            if (res.data.found) {
                // This is the magic: It sends the doctor ID back to App.js
                onDoctorFound(res.data.id); 
                setMsg(`✅ Recommended: ${res.data.name} (${res.data.specialization})`);
            } else {
                setMsg("ℹ️ No specific match. Please select manually.");
            }
        } catch (err) {
            console.error(err);
            setMsg("❌ AI Service Unavailable");
        }
        setLoading(false);
    };

    if (!clinicId) return null; // Don't show if no clinic selected

    return (
        <div style={{ background: '#e3f2fd', padding: '15px', margin: '15px 0', borderRadius: '8px', border: '1px solid #90caf9' }}>
            <label style={{ fontWeight: 'bold', color: '#1565c0' }}>🤖 AI Assistant: Not sure who to see?</label>
            <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <input 
                    type="text" 
                    placeholder="e.g. severe migraine..." 
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
                />
                <button 
                    onClick={handleSearch} 
                    disabled={loading}
                    style={{ background: '#1976d2', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer' }}
                >
                    {loading ? 'Checking...' : 'Find Doctor'}
                </button>
            </div>
            {msg && <div style={{ marginTop: '8px', fontSize: '0.9em', color: '#333' }}>{msg}</div>}
        </div>
    );
};

export default DoctorSmartSearch;