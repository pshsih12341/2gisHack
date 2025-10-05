import axios from 'axios';

export const API_BASE_URL = 'https://2gis.misisxmisis.ru';

// 2GIS API ключи
export const MAPGL_API_KEY = '7889d023-2357-402b-a407-b16c3b316fd5'; // Замените на ваш ключ
export const ROUTING_API_KEY = '7889d023-2357-402b-a407-b16c3b316fd5'; // Замените на ваш ключ

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
