import { http } from './http';

export const greenService = {
  // Отправка зеленого маршрута
  getGreenRoute: async (points) => {
    try {
      const response = await http.post('/api/map/route/green', {
        points: points
      });
      return response;
    } catch (error) {
      console.error('Ошибка при получении зеленого маршрута:', error);
      throw error;
    }
  }
};
