import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

export const getNearbyStores = (latitude, longitude, radius = 10) =>
  api.get("/stores/nearby", { params: { latitude, longitude, radius_km: radius } });

export const getProducts = () => api.get("/products/");
export const getInventory = () => api.get("/inventory/");
export const getBatches = () => api.get("/batches/");
export const getStores = () => api.get("/stores/");
export const getSales = (limit = 250) => api.get("/sales/", { params: { limit } });
export const getExpiry = () => api.get("/expiry/");
export const getForecast = (storeId) => api.get("/forecast/", { params: storeId ? { store_id: storeId } : {} });
export const getRedistributionRecommendations = () => api.get("/redistribution/recommendations");
export const getTransferRequests = () => api.get("/redistribution/transfers");
export const getCommunityOffers = () => api.get("/community/offers");
export const getCommunityRequests = () => api.get("/community/requests");
export const getStaff = () => api.get("/staff/");

export const createProduct = (data) => api.post("/products/", data);
export const updateProduct = (productId, data) => api.put(`/products/${encodeURIComponent(productId)}`, data);
export const deleteProduct = (productId) => api.delete(`/products/${encodeURIComponent(productId)}`);
export const createBatch = (data) => api.post("/batches/", data);
export const createStore = (data) => api.post("/stores/", data);
export const registerStore = (storeData) => api.post("/stores/register", storeData);
export const updateStore = (storeId, data) => api.put(`/stores/${encodeURIComponent(storeId)}`, data);
export const createSale = (data) => api.post("/sales/", data);
export const createTransferRequest = (data) => api.post("/redistribution/transfers", data);
export const publishCommunityOffer = (data) => api.post("/community/offers", data);
export const requestCommunityOffer = (offerId, data) => api.post(`/community/offers/${offerId}/requests`, data);
export const decideCommunityRequest = (requestId, status) => api.patch(`/community/requests/${requestId}`, { status });
export const createStaff = (data) => api.post("/staff/", data);
export const updateStaffStatus = (userId, isActive) => api.patch(`/staff/${encodeURIComponent(userId)}`, { is_active: isActive });

export default api;
