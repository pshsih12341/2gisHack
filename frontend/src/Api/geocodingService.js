import axios from 'axios';

const GEOCODING_API_KEY = '7889d023-2357-402b-a407-b16c3b316fd5';
const GEOCODING_BASE_URL = 'https://catalog.api.2gis.com/3.0';

export const geocodingService = {
  // Поиск адресов по запросу
  async searchAddresses(query, limit = 10) {
    try {
      const response = await axios.get(`${GEOCODING_BASE_URL}/items/geocode`, {
        params: {
          q: query,
          key: GEOCODING_API_KEY,
          type: 'building,street,adm_div.city,adm_div.settlement',
          fields: 'items.point,items.geometry,items.address_name,items.full_name',
          limit: limit,
        },
      });

      return response.data.result?.items || [];
    } catch (error) {
      console.error('Error searching addresses:', error);
      return [];
    }
  },

  // Обратное геокодирование (координаты -> адрес)
  async reverseGeocode(lon, lat) {
    try {
      const response = await axios.get(`${GEOCODING_BASE_URL}/items/geocode`, {
        params: {
          point: `${lon},${lat}`,
          key: GEOCODING_API_KEY,
          type: 'building,street,adm_div.city,adm_div.settlement',
          fields: 'items.point,items.geometry,items.address_name,items.full_name',
          limit: 1,
        },
      });

      return response.data.result?.items?.[0] || null;
    } catch (error) {
      console.error('Error reverse geocoding:', error);
      return null;
    }
  },
};
