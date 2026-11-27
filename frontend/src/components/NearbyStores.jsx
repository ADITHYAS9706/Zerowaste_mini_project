
import { useState } from "react";
import { MapPin, Navigation, Store } from "lucide-react";
import { getNearbyStores } from "../services/api";

function NearbyStores() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const findNearbyStores = () => {
    setError("");
    setLoading(true);
    setSearched(false);

    if (!navigator.geolocation) {
      setError("Your browser does not support location access.");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const latitude = position.coords.latitude;
          const longitude = position.coords.longitude;

          const response = await getNearbyStores(
            latitude,
            longitude,
            10
          );

          setStores(response.data.stores);
          setSearched(true);
        } catch (err) {
          setError(
            err.response?.data?.detail ||
            "Unable to retrieve nearby stores."
          );
        } finally {
          setLoading(false);
        }
      },
      (locationError) => {
        if (locationError.code === 1) {
          setError("Location permission was denied. Please allow location access.");
        } else if (locationError.code === 2) {
          setError("Your current location is unavailable.");
        } else {
          setError("Location request timed out. Please try again.");
        }

        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 60000,
      }
    );
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>
        <MapPin size={22} style={{ verticalAlign: "middle" }} />
        {" "}Nearby Grocery Stores
      </h2>

      <p>
        Find grocery stores near your current location.
      </p>

      <button
        onClick={findNearbyStores}
        disabled={loading}
        style={{
          padding: "12px 20px",
          background: "#15803d",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: loading ? "not-allowed" : "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <Navigation size={18} />
        {loading ? "Finding stores..." : "Find Nearby Stores"}
      </button>

      {error && (
        <p style={{ color: "red", marginTop: "15px" }}>
          {error}
        </p>
      )}

      {searched && stores.length === 0 && (
        <p style={{ marginTop: "20px" }}>
          No grocery stores found within 10 km.
        </p>
      )}

      <div style={{ marginTop: "20px" }}>
        {stores.map((store) => (
          <div
            key={store.store_id}
            style={{
              border: "1px solid #ddd",
              borderRadius: "10px",
              padding: "16px",
              marginBottom: "12px",
              maxWidth: "450px",
            }}
          >
            <h3>
              <Store
                size={18}
                style={{ verticalAlign: "middle" }}
              />
              {" "}{store.store_name}
            </h3>

            <p>
              <MapPin size={15} style={{ verticalAlign: "middle" }} />
              {" "}{store.address}
            </p>

            <p>
              Distance: <strong>{store.distance_km} km</strong>
            </p>

            <p>
              Store ID: {store.store_id}
            </p>

            {store.phone && (
              <p>Phone: {store.phone}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default NearbyStores;
