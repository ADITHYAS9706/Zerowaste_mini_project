import { useState } from "react";
import { MapPin, Navigation, Store, Phone, LocateFixed } from "lucide-react";
import { getNearbyStores } from "../services/api";

export default function NearbyStores() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const findNearbyStores = () => {
    setError("");
    setLoading(true);
    setSearched(false);

    if (!navigator.geolocation) {
      setError("This browser does not support location access.");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const response = await getNearbyStores(coords.latitude, coords.longitude, 10);
          const rows = response?.data?.stores;
          setStores(Array.isArray(rows) ? rows : []);
          setSearched(true);
        } catch (err) {
          setError(err?.response?.data?.detail || "Unable to retrieve nearby stores. Check the backend connection.");
        } finally {
          setLoading(false);
        }
      },
      (locationError) => {
        if (locationError.code === 1) setError("Location permission was denied. Allow location access to search nearby stores.");
        else if (locationError.code === 2) setError("Your current location is unavailable.");
        else setError("The location request timed out. Please try again.");
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  };

  return (
    <div className="nearby-stores-card">
      <div className="nearby-stores-heading">
        <div className="nearby-stores-icon"><MapPin size={19} /></div>
        <div>
          <h3>Nearby store suggestions</h3>
          <p>Find registered grocery stores within 10 km of your location.</p>
        </div>
        <button type="button" className="nearby-find-button" onClick={findNearbyStores} disabled={loading}>
          {loading ? <span className="button-spinner" /> : <Navigation size={16} />}
          {loading ? "Searching..." : "Find stores"}
        </button>
      </div>

      {error && <div className="nearby-error" role="alert">{error}</div>}
      {searched && stores.length === 0 && <div className="nearby-empty">No registered stores were found within 10 km.</div>}

      {stores.length > 0 && (
        <div className="nearby-store-grid">
          {stores.map((store) => (
            <article className="nearby-store-item" key={store.store_id}>
              <div className="nearby-store-name"><Store size={16} /><strong>{store.store_name || "Grocery store"}</strong></div>
              <p><MapPin size={14} />{store.address || "Address not provided"}</p>
              <div className="nearby-store-meta">
                <span><LocateFixed size={13} /> {store.distance_km ?? "—"} km away</span>
                {store.phone && <a href={`tel:${store.phone}`}><Phone size={13} /> {store.phone}</a>}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
