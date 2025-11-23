import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LiveWaitTimesDashboard = () => {
  const [liveData, setLiveData] = useState([]);
  const [doctorsStatus, setDoctorsStatus] = useState([]);
  const [clinicOverview, setClinicOverview] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedDoctor, setSelectedDoctor] = useState('all');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [selectedDoctor]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/api/live-dashboard-overview/');
      if (response.data.success) {
        const { dashboard } = response.data;
        setClinicOverview(dashboard.clinic_overview);
        setDoctorsStatus(dashboard.doctors_status);
        setLiveData(dashboard.live_wait_times);
        setLastUpdated(new Date(dashboard.last_updated));
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTokenStatus = async (tokenId, newStatus) => {
    try {
      const response = await axios.post(`/api/update-token-status/${tokenId}/`, {
        status: newStatus
      });
      
      if (response.data.success) {
        // Refresh data after status update
        fetchDashboardData();
      }
    } catch (error) {
      console.error('Error updating token status:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getWaitTimeColor = (minutes) => {
    if (minutes <= 10) return 'text-green-600';
    if (minutes <= 30) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredData = selectedDoctor === 'all' 
    ? liveData 
    : liveData.filter(item => item.doctor_name === selectedDoctor);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Live Wait Times Dashboard</h1>
        <p className="text-gray-600">
          Real-time predictions for pre-booked appointments using ML + current flow analysis
        </p>
        {lastUpdated && (
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Clinic Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
          <h3 className="text-sm font-medium text-gray-500">Total Appointments</h3>
          <p className="text-2xl font-bold text-gray-900">{clinicOverview.total_appointments_today}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
          <h3 className="text-sm font-medium text-gray-500">Completed</h3>
          <p className="text-2xl font-bold text-gray-900">{clinicOverview.completed_today}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
          <h3 className="text-sm font-medium text-gray-500">In Progress</h3>
          <p className="text-2xl font-bold text-gray-900">{clinicOverview.in_progress}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
          <h3 className="text-sm font-medium text-gray-500">Pending</h3>
          <p className="text-2xl font-bold text-gray-900">{clinicOverview.pending}</p>
        </div>
      </div>

      {/* Doctor Status Cards */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Doctor Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {doctorsStatus.map(doctor => (
            <div key={doctor.doctor_id} className="bg-white p-4 rounded-lg shadow">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900">{doctor.doctor_name}</h3>
                {doctor.running_late && (
                  <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                    Running Late
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-3">{doctor.specialization}</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Total:</span> {doctor.total_appointments}
                </div>
                <div>
                  <span className="text-gray-500">Completed:</span> {doctor.completed}
                </div>
                <div>
                  <span className="text-gray-500">In Progress:</span> {doctor.in_progress}
                </div>
                <div>
                  <span className="text-gray-500">Avg Delay:</span> {doctor.average_delay_minutes}m
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <select
          value={selectedDoctor}
          onChange={(e) => setSelectedDoctor(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2"
        >
          <option value="all">All Doctors</option>
          {doctorsStatus.map(doctor => (
            <option key={doctor.doctor_id} value={doctor.doctor_name}>
              {doctor.doctor_name}
            </option>
          ))}
        </select>
      </div>

      {/* Live Wait Times Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Live Wait Time Predictions</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Token
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Patient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Doctor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Scheduled Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Predicted Wait
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expected Start
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredData.map((item) => (
                <tr key={item.token_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{item.token_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.patient_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.doctor_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.appointment_time}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`font-semibold ${getWaitTimeColor(item.predicted_wait_minutes)}`}>
                      {item.predicted_wait_minutes} min
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {item.predicted_start_time}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      item.is_prebooked ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {item.is_prebooked ? 'Pre-booked' : 'Same-day'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {item.status === 'confirmed' && (
                      <button
                        onClick={() => updateTokenStatus(item.token_id, 'in_progress')}
                        className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 mr-2"
                      >
                        Start
                      </button>
                    )}
                    {item.status === 'in_progress' && (
                      <button
                        onClick={() => updateTokenStatus(item.token_id, 'completed')}
                        className="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600"
                      >
                        Complete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredData.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No appointments found for the selected criteria.
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveWaitTimesDashboard;