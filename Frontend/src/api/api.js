import axios from "axios";

// Core configuration for the API
export const API_BASE_URL = "http://localhost:8000/api";
export const API_BASE = "http://localhost:8000/api"; // For backward compatibility with some components

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
