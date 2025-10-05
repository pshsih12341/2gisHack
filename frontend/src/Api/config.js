import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000';

// 2GIS API ключи
export const MAPGL_API_KEY = ''; // Замените на ваш ключ
export const ROUTING_API_KEY = ''; // Замените на ваш ключ

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use((response) => {
  return response;
});
