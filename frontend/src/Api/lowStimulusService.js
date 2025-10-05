import { http } from './http';

export const lowStimulusService = {
  // Отправка маршрута для низкой стимуляции
  getLowStimulusRoute: async (points) => {
    try {
      const response = await http.post('/api/map/route/low_stimulus', {
        points: points
      });
      return response;
    } catch (error) {
      console.error('Ошибка при получении маршрута для низкой стимуляции:', error);
      throw error;
    }
  }
};
