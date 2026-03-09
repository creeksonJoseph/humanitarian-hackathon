import axios from "axios";

// Core configuration for the API
export const API_BASE_URL = "https://humanitarian-hackathon.onrender.com/api";
export const API_BASE = "https://humanitarian-hackathon.onrender.com/api"; // For backward compatibility with some components

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
