import React, { useState, useEffect } from 'react';
import config from '../utils/config';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import outpostMarkers from '../utils/outpostMarkers';

function LandingPage() {
  const createCustomIcon = (spawnPoint) => {
    return new L.Icon({
      iconUrl: outpostMarkers[spawnPoint.name],
      iconSize: [50, 50],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16],
      shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
      shadowSize: [41, 41],
      shadowAnchor: [12, 41],
    })
  }
  const [spawnPoints, setSpawnPoints] = useState([]);
  const [selectedSpawnPoint, setSelectedSpawnPoint] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchSpawnPoints = async () => {
      try {
        const response = await fetch(`${config.backendUrl}/outposts/fetch_spawn_points`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        const data = await response.json();

        console.log('Fetched Spawn Points:', data);

        if (response.ok) {
          setSpawnPoints(data);
        } else {
          setMessage(data.message || 'Failed to fetch spawn points');
        }
      } catch (error) {
        console.error('Error fetching spawn points:', error);
        setMessage('An error occurred while fetching spawn points');
      }
    };

    fetchSpawnPoints();
  }, []);

  const handleSpawnPointSelection = (spawnPoint) => {
    setSelectedSpawnPoint(spawnPoint);
    setMessage(`You have selected: ${spawnPoint.name}`);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Choose Your Spawn Point</h1>
      {message && <p style={styles.message}>{message}</p>}
      <MapContainer center={[40, 70]} zoom={3} style={{ height: '500px', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {spawnPoints.map((spawnPoint) => (
          <Marker key={spawnPoint.id} position={[spawnPoint.latitude, spawnPoint.longitude]} icon={createCustomIcon(spawnPoint)}>
            <Popup>
              <strong>{spawnPoint.name}</strong><br />
              Description: {spawnPoint.description}<br />
              Culture: {spawnPoint.culture}<br />
              Gold Bonus: {spawnPoint.gold_bonus}<br />
              Reputation Bonus: {spawnPoint.reputation_bonus}<br />
              Languages Spoken: {spawnPoint.language.join(', ')}<br />
              Population: {spawnPoint.population.toLocaleString()}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      <div style={styles.listContainer}>
        <ul style={styles.list}>
          {spawnPoints.map((spawnPoint) => (
            <li key={spawnPoint.id} style={styles.listItem}>
              <button onClick={() => handleSpawnPointSelection(spawnPoint)} style={styles.button}>
                <strong>{spawnPoint.name}</strong>
              </button>
              <div style={styles.details}>
                <p><strong>Description:</strong> {spawnPoint.description}</p>
                <p><strong>Culture:</strong> {spawnPoint.culture}</p>
                <p><strong style={{ color: 'gold' }}>Gold Bonus:</strong> {spawnPoint.gold_bonus}</p>
                <p><strong style={{color: 'green'}}>Reputation Bonus:</strong> {spawnPoint.reputation_bonus}</p>
                <p><strong>Culture:</strong> {spawnPoint.culture}</p>
                <p><strong>Languages Spoken:</strong> {spawnPoint.language.join(', ')}</p>
                <p><strong>Population:</strong> {spawnPoint.population.toLocaleString()}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-start',
    minHeight: '100vh',
    backgroundColor: '#f0f0f0',
    padding: '20px',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '20px',
  },
  message: {
    fontSize: '1rem',
    color: 'green',
    marginBottom: '10px',
  },
  listContainer: {
    width: '50%',
    maxHeight: '60vh',
    overflowY: 'auto',
    borderRadius: '8px',
    padding: '10px',
    backgroundColor: '#fff',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  list: {
    listStyleType: 'none',
    padding: 0,
    margin: 0,
  },
  listItem: {
    marginBottom: '15px',
    padding: '10px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  button: {
    width: '100%',
    padding: '10px',
    fontSize: '1.2rem',
    fontWeight: 'bold',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    marginBottom: '5px',
  },
  details: {
    fontSize: '0.9rem',
    color: '#555',
  },
};

export default LandingPage;
