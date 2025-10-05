import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000';

// 2GIS API ключи
export const MAPGL_API_KEY = 'dcae5afc-c412-4a64-a4a0-53e033d88bc6'; // Замените на ваш ключ
export const ROUTING_API_KEY = 'dcae5afc-c412-4a64-a4a0-53e033d88bc6'; // Замените на ваш ключ

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
