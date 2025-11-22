import React, { useState } from 'react';
import axios from 'axios';

const PatientAISummary = ({ patientId, token }) => {
    const [summary, setSummary] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleGetSummary = async () => {
        setLoading(true);
        setError("");
        setSummary("");
        
        try {
            // ✅ FIX: This URL matches exactly what is in api/urls.py
            // It calls: http://localhost:8000/api/patient-summary/17/
            const response = await axios.get(
                `http://localhost:8000/api/patient-summary/${patientId}/`,
                { headers: { Authorization: `Token ${token}` } }
            );
            
            if (response.data.error) {
                setError(response.data.error);
            } else {
                // Handle different response formats from the API
                const summaryText = response.data.summary_text || 
                                  response.data.summary || 
                                  JSON.stringify(response.data, null, 2);
                setSummary(summaryText);
            }
        } catch (err) {
            console.error("Summary Error:", err);
            setError("Failed to generate summary. Server might be busy loading the AI.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ai-summary-section" style={{ marginBottom: '20px' }}>
            {/* Button to trigger AI */}
            {!summary && !loading && (
                <button 
                    onClick={handleGetSummary} 
                    className="summary-btn"
                    style={{ 
                        backgroundColor: '#6200ea', 
                        color: 'white', 
                        padding: '10px 15px', 
                        borderRadius: '5px', 
                        border: 'none', 
                        cursor: 'pointer',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        width: '100%',
                        justifyContent: 'center'
                    }}
                >
                    <span>🧠</span> Generate AI Medical Summary
                </button>
            )}

            {/* Loading State */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '10px', color: '#6200ea' }}>
                    <p style={{ fontWeight: 'bold', animation: 'pulse 1s infinite' }}>
                        ✨ AI is reading patient history...
                    </p>
                    <small>(First run takes ~20s to load the brain)</small>
                </div>
            )}
            
            {/* Error State */}
            {error && (
                <div style={{ backgroundColor: '#ffebee', color: '#c62828', padding: '10px', borderRadius: '5px', marginTop: '10px' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Summary Display Card */}
            {summary && (
                <div className="ai-summary-card" style={{ 
                    background: 'linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)', 
                    padding: '20px', 
                    borderRadius: '8px', 
                    borderLeft: '5px solid #6200ea', 
                    marginTop: '15px',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.05)'
                }}>
                    <h4 style={{ marginTop: 0, color: '#6200ea', display: 'flex', alignItems: 'center' }}>
                        <span style={{ marginRight: '10px', fontSize: '1.5em' }}>🤖</span> 
                        AI Analysis
                    </h4>
                    <div style={{ 
                        backgroundColor: 'rgba(255,255,255,0.6)', 
                        padding: '15px', 
                        borderRadius: '6px', 
                        lineHeight: '1.6',
                        color: '#333',
                        fontSize: '0.95rem'
                    }}>
                        {summary}
                    </div>
                    <button 
                        onClick={() => setSummary("")} 
                        style={{ 
                            marginTop: '10px', 
                            fontSize: '0.8em', 
                            color: '#666', 
                            background: 'none', 
                            border: 'none', 
                            cursor: 'pointer', 
                            textDecoration: 'underline' 
                        }}
                    >
                        Close Summary
                    </button>
                </div>
            )}
        </div>
    );
};

export default PatientAISummary;