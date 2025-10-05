import React from 'react';

const RouteDetails = ({routeData, isVisible}) => {
  if (!isVisible || !routeData) {
    return (
      <div className='text-center py-8 text-gray-500'>
        <div className='text-4xl mb-2'>🗺️</div>
        <p>Кликните на карту для построения маршрута</p>
      </div>
    );
  }

  const {stages = [], totalTime = 0, totalDistance = 0} = routeData;

  const formatTime = (minutes) => {
    if (minutes < 60) {
      return `${minutes} мин`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}ч ${mins}мин` : `${hours}ч`;
  };

  const formatDistance = (meters) => {
    if (meters < 1000) {
      return `${meters} м`;
    }
    return `${(meters / 1000).toFixed(1)} км`;
  };

  const getTransportIcon = (transportType) => {
    const icons = {
      bus: '🚌',
      tram: '🚋',
      metro: '🚇',
      pedestrian: '🚶',
      car: '🚗',
      taxi: '🚕',
    };
    return icons[transportType] || '🚌';
  };

  const getTransportName = (transportType) => {
    const names = {
      bus: 'Автобус',
      tram: 'Трамвай',
      metro: 'Метро',
      pedestrian: 'Пешком',
      car: 'На машине',
      taxi: 'Такси',
    };
    return names[transportType] || 'Транспорт';
  };

  return (
    <div className='space-y-4'>
      {/* Общая информация о маршруте */}
      <div className='bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200'>
        <h4 className='font-semibold text-blue-900 mb-3 flex items-center'>
          <span className='text-xl mr-2'>📍</span>
          Информация о маршруте
        </h4>
        <div className='grid grid-cols-2 gap-4 text-sm'>
          <div className='flex items-center space-x-2'>
            <span className='text-blue-600'>⏱️</span>
            <span className='text-blue-800 font-medium'>{formatTime(totalTime)}</span>
          </div>
          <div className='flex items-center space-x-2'>
            <span className='text-blue-600'>📏</span>
            <span className='text-blue-800 font-medium'>{formatDistance(totalDistance)}</span>
          </div>
        </div>
      </div>

      {/* Детали по этапам */}
      <div className='space-y-3'>
        <h4 className='font-semibold text-gray-800 flex items-center'>
          <span className='text-lg mr-2'>🛤️</span>
          Этапы маршрута
        </h4>

        {stages.map((stage, index) => (
          <div key={index} className='bg-white border border-gray-200 rounded-lg p-3'>
            <div className='flex items-center justify-between mb-2'>
              <div className='flex items-center space-x-2'>
                <span className='text-lg'>{getTransportIcon(stage.transportType)}</span>
                <span className='font-medium text-gray-800'>{getTransportName(stage.transportType)}</span>
              </div>
              <div className='text-sm text-gray-600'>{formatTime(stage.duration || 0)}</div>
            </div>

            {stage.routes && stage.routes.length > 0 && (
              <div className='space-y-1'>
                {stage.routes.map((route, routeIndex) => (
                  <div key={routeIndex} className='text-sm text-gray-600'>
                    <div className='flex items-center space-x-2'>
                      <div className='w-2 h-2 bg-blue-500 rounded-full'></div>
                      <span>{route.name || `Маршрут ${routeIndex + 1}`}</span>
                    </div>
                    {route.description && <div className='ml-4 text-xs text-gray-500 mt-1'>{route.description}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Действия */}
      <div className='pt-4 border-t border-gray-200 space-y-2'>
        <button className='w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2'>
          <span>🚀</span>
          <span>Начать навигацию</span>
        </button>
        <button className='w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2'>
          <span>📋</span>
          <span>Поделиться маршрутом</span>
        </button>
      </div>
    </div>
  );
};

export default RouteDetails;
