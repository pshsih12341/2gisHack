import {useState, useEffect} from 'react';

/**
 * Хук для получения геолокации пользователя
 * @param {Object} options - опции для getCurrentPosition
 * @returns {Object} - состояние геолокации
 */
export const useGeolocation = (options = {}) => {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 300000, // 5 минут
    ...options
  };

  const getCurrentPosition = () => {
    if (!navigator.geolocation) {
      setError('Геолокация не поддерживается вашим браузером');
      return;
    }

    setIsLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const {latitude, longitude} = position.coords;
        setLocation({
          latitude,
          longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        });
        setIsLoading(false);
      },
      (error) => {
        let errorMessage = 'Не удалось получить геолокацию';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Доступ к геолокации запрещен пользователем';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Информация о местоположении недоступна';
            break;
          case error.TIMEOUT:
            errorMessage = 'Время ожидания геолокации истекло';
            break;
          default:
            errorMessage = `Неизвестная ошибка: ${error.message}`;
            break;
        }
        
        setError(errorMessage);
        setIsLoading(false);
        console.error('Ошибка геолокации:', error);
      },
      defaultOptions
    );
  };

  const watchPosition = () => {
    if (!navigator.geolocation) {
      setError('Геолокация не поддерживается вашим браузером');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const {latitude, longitude} = position.coords;
        setLocation({
          latitude,
          longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        });
        setIsLoading(false);
      },
      (error) => {
        let errorMessage = 'Не удалось получить геолокацию';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Доступ к геолокации запрещен пользователем';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Информация о местоположении недоступна';
            break;
          case error.TIMEOUT:
            errorMessage = 'Время ожидания геолокации истекло';
            break;
          default:
            errorMessage = `Неизвестная ошибка: ${error.message}`;
            break;
        }
        
        setError(errorMessage);
        setIsLoading(false);
        console.error('Ошибка геолокации:', error);
      },
      defaultOptions
    );

    return watchId;
  };

  const clearWatch = (watchId) => {
    if (watchId && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId);
    }
  };

  useEffect(() => {
    // Автоматически запрашиваем геолокацию при монтировании
    getCurrentPosition();
  }, []);

  return {
    location,
    error,
    isLoading,
    getCurrentPosition,
    watchPosition,
    clearWatch
  };
};
