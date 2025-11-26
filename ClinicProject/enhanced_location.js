// Enhanced GPS Location Service for accurate coordinates

const getAccurateLocation = () => {
  return new Promise((resolve, reject) => {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }

    // Enhanced options for better accuracy
    const options = {
      enableHighAccuracy: true,    // Use GPS instead of network/wifi
      timeout: 30000,              // 30 seconds timeout
      maximumAge: 0                // Don't use cached location
    };

    // Try multiple times for better accuracy
    let attempts = 0;
    const maxAttempts = 3;
    let bestAccuracy = Infinity;
    let bestPosition = null;

    const tryGetLocation = () => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          attempts++;
          const accuracy = position.coords.accuracy;
          
          console.log(`GPS Attempt ${attempts}:`, {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: accuracy + 'm'
          });

          // Keep the most accurate reading
          if (accuracy < bestAccuracy) {
            bestAccuracy = accuracy;
            bestPosition = position;
          }

          // If we have good accuracy (< 50m) or max attempts reached
          if (accuracy < 50 || attempts >= maxAttempts) {
            resolve({
              latitude: bestPosition.coords.latitude,
              longitude: bestPosition.coords.longitude,
              accuracy: bestAccuracy
            });
          } else {
            // Try again for better accuracy
            setTimeout(tryGetLocation, 2000);
          }
        },
        (error) => {
          console.error('GPS Error:', error);
          
          switch(error.code) {
            case error.PERMISSION_DENIED:
              reject(new Error('Location access denied. Please enable location permissions.'));
              break;
            case error.POSITION_UNAVAILABLE:
              reject(new Error('Location information unavailable. Please check GPS settings.'));
              break;
            case error.TIMEOUT:
              reject(new Error('Location request timed out. Please try again.'));
              break;
            default:
              reject(new Error('Unknown location error occurred.'));
              break;
          }
        },
        options
      );
    };

    tryGetLocation();
  });
};

// Usage example for your React component:
const handleConfirmArrival = async () => {
  try {
    console.log('Getting accurate location...');
    const location = await getAccurateLocation();
    
    console.log('Final location:', location);
    
    // Make API call with accurate coordinates
    const response = await fetch('/api/patient/confirm-arrival/', {
      method: 'POST',
      headers: {
        'Authorization': `Token ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        latitude: location.latitude,
        longitude: location.longitude
      })
    });
    
    const result = await response.json();
    console.log('Confirmation result:', result);
    
  } catch (error) {
    console.error('Location error:', error.message);
    alert(`Location Error: ${error.message}`);
  }
};

// Alternative: Manual coordinate input for testing
const manualLocationInput = () => {
  const lat = prompt('Enter latitude (e.g., 12.900794):');
  const lng = prompt('Enter longitude (e.g., 74.98795):');
  
  if (lat && lng) {
    return {
      latitude: parseFloat(lat),
      longitude: parseFloat(lng),
      accuracy: 0
    };
  }
  return null;
};

export { getAccurateLocation, manualLocationInput };