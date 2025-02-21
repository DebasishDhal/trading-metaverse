import React, { useState, useEffect } from "react";
import config from "../utils/config";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import outpostMarkers from "../utils/outpostMarkers";
import { Link } from "react-router-dom";

const redIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function Introduction() {
  const createCustomIcon = (spawnPoint) => {
    return new L.Icon({
      iconUrl: outpostMarkers[spawnPoint.name],
      iconSize: [50, 50],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16],
      shadowUrl:
        "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
      shadowSize: [41, 41],
      shadowAnchor: [12, 41],
    });
  };

  const [spawnPoints, setSpawnPoints] = useState([]);
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchSpawnPoints = async () => {
      try {
        const response = await fetch(
          `${config.backendUrl}/outposts/fetch_spawn_points`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        const data = await response.json();

        if (response.ok) {
          setSpawnPoints(data);
        } else {
          setMessage(data.message || "Failed to fetch spawn points");
        }
      } catch (error) {
        setMessage("An error occurred while fetching spawn points");
      }
    };

    const fetchRouteCoordinates = async () => {
      try {
        const response = await fetch(
          `${config.backendUrl}/outposts/route_coordinates`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        const data = await response.json();

        if (response.ok) {
          setRouteCoordinates(data);
        } else {
          setMessage("Failed to fetch route coordinates");
        }
      } catch (error) {
        setMessage("An error occurred while fetching route coordinates");
      }
    };

    fetchSpawnPoints();
    fetchRouteCoordinates();
  }, []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Welcome to the Trading Outpost Game</h1>
        <div style={styles.authButtons}>
          <Link to="/signup" style={styles.authButton}>
            Signup
          </Link>
          <Link to="/login" style={styles.authButton}>
            Login
          </Link>
        </div>
      </header>

      <p style={styles.description}>
        Embark on an adventure in a dynamic trading world where outposts hold
        unique advantages. Choose wisely, as your starting point affects your
        journey in commerce, reputation, and resources.
      </p>

      {message && <p style={styles.message}>{message}</p>}

      <MapContainer center={[40, 70]} zoom={3} style={styles.map}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {spawnPoints.map((spawnPoint) => (
          <Marker
            key={spawnPoint.id}
            position={[spawnPoint.latitude, spawnPoint.longitude]}
            icon={createCustomIcon(spawnPoint)}
          >
            <Popup>
              <strong>{spawnPoint.name}</strong>
              <br />
              Description: {spawnPoint.description}
              <br />
              Culture: {spawnPoint.culture}
              <br />
              Gold Bonus: {spawnPoint.gold_bonus}
              <br />
              Reputation Bonus: {spawnPoint.reputation_bonus}
              <br />
              Languages Spoken: {spawnPoint.language.join(", ")}
              <br />
              Population: {spawnPoint.population.toLocaleString()}
            </Popup>
          </Marker>
        ))}

        {routeCoordinates.map((route, index) => (
          <Polyline key={index} positions={route.route} color="red" />
        ))}
      </MapContainer>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "flex-start",
    minHeight: "100vh",
    backgroundColor: "#2c3e50",
    color: "white",
    padding: "20px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    width: "100%",
    maxWidth: "1200px",
    padding: "10px 20px",
  },
  title: {
    fontSize: "2rem",
    fontWeight: "bold",
  },
  authButtons: {
    display: "flex",
    gap: "10px",
  },
  authButton: {
    textDecoration: "none",
    color: "white",
    backgroundColor: "#3498db",
    padding: "2px 5px",  // Keep a small padding
    borderRadius: "5px",
    fontWeight: "bold",
    fontSize: "1.1rem",  // Reduce font size
    lineHeight: "1",
    height: "20px",  // Explicit height
    display: "flex",
    alignItems: "center",  // Ensure text is centered
    justifyContent: "center",
    margin: "0"
  },
  description: {
    textAlign: "center",
    fontSize: "1.2rem",
    maxWidth: "800px",
    marginBottom: "20px",
  },
  message: {
    fontSize: "1rem",
    color: "gold",
    marginBottom: "10px",
  },
  map: {
    height: "500px",
    width: "100%",
    maxWidth: "1200px",
    borderRadius: "10px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.3)",
  },
};

export default Introduction;
