import React, { useState } from 'react';
import config from '../utils/config'; 

function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    console.log("Backend URL:", config.backendUrl); // Debug the backend URL

    try {
      const response = await fetch(`${config.backendUrl}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message);
      } else {
        setMessage(data.message || 'Signup failed');
      }
    } catch (error) {
      setMessage('An error occurred');
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Trading Metaverse à la 16th century</h1>
      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={styles.input}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
        />
        <button type="submit" style={styles.button}>Sign Up</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    backgroundColor: '#f0f0f0',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '20px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  input: {
    margin: '10px 0',
    padding: '10px',
    fontSize: '1rem',
    width: '200px',
  },
  button: {
    padding: '10px 20px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
};

export default Signup;
