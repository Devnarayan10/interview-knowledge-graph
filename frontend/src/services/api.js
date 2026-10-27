/**
 * Centralized API client for backend communication.
 * Full endpoints will be added in Phase 9.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed';
    return Promise.reject(new Error(message));
  },
);

export const healthCheck = () => axios.get(`${API_BASE_URL.replace('/api', '')}/health`);

export default api;
