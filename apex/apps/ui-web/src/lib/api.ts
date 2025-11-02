import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use((response) => {
  const { result, confidence } = response.data;
  if (result === undefined || confidence === undefined) {
    console.error('Invalid envelope:', response.data);
  }
  return response;
});

export default api;

