import React, { useState, useEffect } from 'react';
import config from '../utils/config';

function LandingPage() {
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
                <p><strong>Gold Bonus:</strong> {spawnPoint.gold_bonus}</p>
                <p><strong>Reputation Bonus:</strong> {spawnPoint.reputation_bonus}</p>
                <p><strong>Culture:</strong> {spawnPoint.culture}</p>
                <p><strong>Languages Spoken:</strong> {spawnPoint.language.join(', ')}</p>
                <p><strong>Population:</strong> {spawnPoint.population}</p>
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
    justifyContent: 'flex-start', // Ensure content starts from the top
    minHeight: '100vh', // Allow page to expand
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
    maxHeight: '60vh', // Limit height and make scrollable
    overflowY: 'auto', // Enable scrolling if too many items
    borderRadius: '8px',
    padding: '10px',
    backgroundColor: '#fff',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  list: {
    listStyleType: 'none',
    padding: 0,
    margin: 0, // Ensure no extra spacing
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
