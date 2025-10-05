import { http } from './http';

export const wheelchairService = {
  // Отправка маршрута для инвалидных колясок
  getWheelchairRoute: async (points) => {
    try {
      const response = await http.post('/api/map/route/wheelchair', {
        points: points
      });
      return response;
    } catch (error) {
      console.error('Ошибка при получении маршрута для инвалидных колясок:', error);
      throw error;
    }
  }
};
