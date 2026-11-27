
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});
export const getNearbyStores = (latitude, longitude, radius = 10) =>
  api.get("/stores/nearby", {
    params: {
      latitude,
      longitude,
      radius_km: radius,
    },
  });

export const getProducts = () => api.get("/products/");
export const getInventory = () => api.get("/inventory/");
export const getBatches = () => api.get("/batches/");
export const getStores = () => api.get("/stores/");

export const createProduct = (data) => api.post("/products/", data);
export const createBatch = (data) => api.post("/batches/", data);
export const createStore = (data) => api.post("/stores/", data);

export default api;

export const registerStore = (storeData) =>
  api.post("/stores/register", storeData);

