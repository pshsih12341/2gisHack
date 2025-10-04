import React from 'react';
import {Button} from './ui/button';

const GeolocationPrompt = ({onAllow, onDeny, isLoading}) => {
  return (
    <div
      className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'
      role='dialog'
      aria-labelledby='geolocation-title'
      aria-describedby='geolocation-description'
      aria-modal='true'
    >
      <div className='bg-white rounded-lg p-6 max-w-sm w-full mobile-container'>
        <div className='text-center space-y-4'>
          <div className='w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center'>
            <span className='text-2xl' aria-hidden='true'>
              📍
            </span>
          </div>

          <div>
            <h3 id='geolocation-title' className='mobile-subtitle text-gray-900 mb-2'>
              Разрешить геолокацию
            </h3>
            <p id='geolocation-description' className='mobile-text text-gray-600'>
              Приложение запрашивает доступ к вашему местоположению для отображения карты и предоставления
              персонализированных услуг.
            </p>
          </div>

          <div className='space-y-3'>
            <Button
              onClick={onAllow}
              disabled={isLoading}
              className='mobile-button w-full'
              aria-describedby='allow-description'
            >
              {isLoading ? 'Загрузка...' : 'Разрешить'}
            </Button>
            <p id='allow-description' className='sr-only'>
              Нажмите для разрешения доступа к геолокации
            </p>

            <Button
              onClick={onDeny}
              variant='outline'
              disabled={isLoading}
              className='mobile-button w-full'
              aria-describedby='deny-description'
            >
              Отказаться
            </Button>
            <p id='deny-description' className='sr-only'>
              Нажмите для отказа от доступа к геолокации
            </p>
          </div>

          <div className='text-xs text-gray-500'>Вы можете изменить это разрешение в настройках браузера</div>
        </div>
      </div>
    </div>
  );
};

export default GeolocationPrompt;
