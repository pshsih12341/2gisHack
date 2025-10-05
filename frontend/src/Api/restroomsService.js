import { http } from './http';

export const restroomsService = {
  // Отправка маршрута для туалетов
  getRestroomsRoute: async (points) => {
    try {
      const response = await http.post('/api/map/route/restrooms?max_vias=8&hotspot_radius_m=200', {
        points: points
      });
      return response;
    } catch (error) {
      console.error('Ошибка при получении маршрута для туалетов:', error);
      throw error;
    }
  }
};
