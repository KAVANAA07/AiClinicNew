import React, { useState, useEffect } from 'react';

const ScheduleManagement = ({ apiClient, onBack }) => {
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [saving, setSaving] = useState({});

    const fetchSchedules = async () => {
        try {
            setLoading(true);
            setError('');
            console.log('Fetching schedules...');
            const response = await apiClient.get('/schedules/');
            console.log('Schedules response:', response.data);
            setSchedules(response.data);
        } catch (err) {
            const errorMsg = err.response?.data?.error || 'Failed to load doctor schedules.';
            setError(errorMsg);
            console.error('Schedule fetch error:', err.response || err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSchedules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const updateSchedule = async (doctorId, scheduleData) => {
        try {
            setSaving(prev => ({ ...prev, [doctorId]: true }));
            setError('');
            
            const response = await apiClient.patch(`/schedules/${doctorId}/`, scheduleData);
            
            // Update local state
            setSchedules(prev => prev.map(schedule => 
                schedule.doctor === doctorId ? response.data : schedule
            ));
            
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to update schedule.');
            console.error('Schedule update error:', err);
        } finally {
            setSaving(prev => ({ ...prev, [doctorId]: false }));
        }
    };

    const handleScheduleChange = (doctorId, field, value) => {
        setSchedules(prev => prev.map(schedule => 
            schedule.doctor === doctorId 
                ? { ...schedule, [field]: value }
                : schedule
        ));
    };

    const formatTime = (timeStr) => {
        if (!timeStr) return '';
        // Handle both HH:MM and HH:MM:SS formats
        if (timeStr.length > 5) {
            return timeStr.substring(0, 5); // HH:MM format
        }
        return timeStr;
    };

    const calculateTotalSlots = (startTime, endTime, duration) => {
        if (!startTime || !endTime || !duration) return 0;
        
        const start = new Date(`2000-01-01T${startTime}`);
        const end = new Date(`2000-01-01T${endTime}`);
        const diffMinutes = (end - start) / (1000 * 60);
        
        return Math.floor(diffMinutes / duration);
    };

    if (loading) {
        return (
            <div className="dashboard-container">
                <header className="dashboard-header">
                    <h1>Schedule Management</h1>
                    <button onClick={onBack} className="logout-button">Back to Dashboard</button>
                </header>
                <div className="loading-screen">Loading schedules...</div>
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Doctor Schedule Management</h1>
                <button onClick={onBack} className="logout-button">Back to Dashboard</button>
            </header>

            {error && <div className="error-banner">{error}</div>}

            <div className="dashboard-content">
                <div className="card">
                    <h2>Configure Doctor Working Hours & Slots</h2>
                    <p className="schedule-info">
                        Set daily working hours, slot duration, and maximum slots for each doctor. 
                        Changes will apply to future appointments.
                    </p>

                    <div className="schedule-grid">
                        {schedules.map(schedule => {
                            const totalSlots = calculateTotalSlots(
                                schedule.start_time, 
                                schedule.end_time, 
                                schedule.slot_duration_minutes
                            );
                            const effectiveSlots = schedule.max_slots_per_day || totalSlots;

                            return (
                                <div key={schedule.doctor} className="schedule-card">
                                    <div className="schedule-header">
                                        <h3>Dr. {schedule.doctor_name}</h3>
                                        <div className="schedule-status">
                                            <label className="toggle-switch">
                                                <input
                                                    type="checkbox"
                                                    checked={schedule.is_active}
                                                    onChange={(e) => {
                                                        handleScheduleChange(schedule.doctor, 'is_active', e.target.checked);
                                                        updateSchedule(schedule.doctor, { is_active: e.target.checked });
                                                    }}
                                                />
                                                <span className="toggle-slider"></span>
                                            </label>
                                            <span>{schedule.is_active ? 'Active' : 'Inactive'}</span>
                                        </div>
                                    </div>

                                    <div className="schedule-form">
                                        <div className="form-row">
                                            <div className="input-group">
                                                <label>Start Time</label>
                                                <input
                                                    type="time"
                                                    value={formatTime(schedule.start_time)}
                                                    onChange={(e) => handleScheduleChange(schedule.doctor, 'start_time', e.target.value)}
                                                    disabled={saving[schedule.doctor]}
                                                />
                                            </div>
                                            <div className="input-group">
                                                <label>End Time</label>
                                                <input
                                                    type="time"
                                                    value={formatTime(schedule.end_time)}
                                                    onChange={(e) => handleScheduleChange(schedule.doctor, 'end_time', e.target.value)}
                                                    disabled={saving[schedule.doctor]}
                                                />
                                            </div>
                                        </div>

                                        <div className="form-row">
                                            <div className="input-group">
                                                <label>Slot Duration (minutes)</label>
                                                <select
                                                    value={schedule.slot_duration_minutes}
                                                    onChange={(e) => handleScheduleChange(schedule.doctor, 'slot_duration_minutes', parseInt(e.target.value))}
                                                    disabled={saving[schedule.doctor]}
                                                >
                                                    <option value={10}>10 minutes</option>
                                                    <option value={15}>15 minutes</option>
                                                    <option value={20}>20 minutes</option>
                                                    <option value={30}>30 minutes</option>
                                                    <option value={45}>45 minutes</option>
                                                    <option value={60}>60 minutes</option>
                                                </select>
                                            </div>
                                            <div className="input-group">
                                                <label>Max Slots per Day (optional)</label>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    max="100"
                                                    placeholder={`Default: ${totalSlots}`}
                                                    value={schedule.max_slots_per_day || ''}
                                                    onChange={(e) => handleScheduleChange(schedule.doctor, 'max_slots_per_day', e.target.value ? parseInt(e.target.value) : null)}
                                                    disabled={saving[schedule.doctor]}
                                                />
                                            </div>
                                        </div>

                                        <div className="schedule-summary">
                                            <div className="summary-item">
                                                <strong>Available Slots:</strong> {effectiveSlots}
                                            </div>
                                            <div className="summary-item">
                                                <strong>Working Hours:</strong> {formatTime(schedule.start_time)} - {formatTime(schedule.end_time)}
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => updateSchedule(schedule.doctor, {
                                                start_time: schedule.start_time,
                                                end_time: schedule.end_time,
                                                slot_duration_minutes: schedule.slot_duration_minutes,
                                                max_slots_per_day: schedule.max_slots_per_day,
                                                is_active: schedule.is_active
                                            })}
                                            className="primary-button"
                                            disabled={saving[schedule.doctor]}
                                        >
                                            {saving[schedule.doctor] ? 'Saving...' : 'Save Schedule'}
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ScheduleManagement;