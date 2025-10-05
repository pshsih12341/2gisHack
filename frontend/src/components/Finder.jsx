import React, {useEffect, useState, useContext} from 'react';
import carIcon from '../Shared/imgs/Car Icon.svg';
import busIcon from '../Shared/imgs/bus.svg';
import walkingIcon from '../Shared/imgs/person-standing.svg';
import taxiIcon from '../Shared/imgs/Ticket Icon.svg';
import motorcycleIcon from '../Shared/imgs/bike.svg';
import deliveryIcon from '../Shared/imgs/package.svg';
import bicycleIcon from '../Shared/imgs/bikeWith.svg';
import bookmarkIcon from '../Shared/imgs/bookmark.svg';
import homeIcon from '../Shared/imgs/home.svg';
import briefcaseIcon from '../Shared/imgs/briefcase.svg';
import searchIcon from '../Shared/imgs/Search Icon.svg';
import routeIcon from '../Shared/imgs/Car Icon.svg';
import navigatorIcon from '../Shared/imgs/Navigator Icon.svg';
import friendsIcon from '../Shared/imgs/Friends Icon.svg';
import tipsIcon from '../Shared/imgs/Tips Icon.svg';
import greenCircle from '../Shared/imgs/greenCircle.svg';
import blueCircle from '../Shared/imgs/blueCircle.svg';
import equalIcon from '../Shared/imgs/equal.svg';
import {useStore} from '../App/store';
import {wheelchairService} from '../Api/wheelchairService';
import {Directions} from '@2gis/mapgl-directions';
import {ROUTING_API_KEY} from '../Api/config';
import {MapContext} from '../Shared/MapContenxProvider';

const Finder = () => {
  const [fromValue, setFromValue] = useState('');
  const [toValue, setToValue] = useState('');
  const [selectedTransport, setSelectedTransport] = useState('car');
  const [isLoading, setIsLoading] = useState(false);
  const {firstPoint, secondPoint} = useStore();
  const [mapInstance] = useContext(MapContext);

  useEffect(() => {
    if (firstPoint) {
      setFromValue(firstPoint?.full_name);
    }
    if (secondPoint) {
      setToValue(secondPoint?.full_name);
    }
  }, [firstPoint, secondPoint]);

  const handleWheelchairRoute = async () => {
    if (!firstPoint || !secondPoint) {
      alert('Пожалуйста, выберите начальную и конечную точки на карте');
      return;
    }

    setIsLoading(true);
    try {
      const points = [
        {lon: `${firstPoint.lon}`, lat: `${firstPoint.lat}`, type: 'stop'},
        {lon: `${secondPoint.lon}`, lat: `${secondPoint.lat}`, type: 'stop'},
      ];
      console.log('Points:', points);
      const response = await wheelchairService.getWheelchairRoute(points);
      console.log('Маршрут для инвалидных колясок:', response);

      const directions = new Directions(mapInstance, {
        directionsApiKey: ROUTING_API_KEY,
      });
      const directionsPoints = response.query.points.map((point) => [parseFloat(point.lon), parseFloat(point.lat)]);
      directions.pedestrianRoute({
        points: directionsPoints,
      });
    } catch (error) {
      console.error('Ошибка при получении маршрута:', error);
      alert('Ошибка при получении маршрута для инвалидных колясок');
    } finally {
      setIsLoading(false);
    }
  };

  const transportOptions = [
    {id: 'car', icon: carIcon, label: 'На машине'},
    {id: 'bus', icon: busIcon, label: 'Автобус'},
    {id: 'walking', icon: walkingIcon, label: 'Пешком'},
    {id: 'taxi', icon: taxiIcon, label: 'Такси'},
    {id: 'motorcycle', icon: motorcycleIcon, label: 'Мотоцикл'},
    {id: 'delivery', icon: deliveryIcon, label: 'Доставка'},
    {id: 'bicycle', icon: bicycleIcon, label: 'Велосипед'},
  ];

  const quickButtons = [
    {icon: bookmarkIcon, label: ''},
    {icon: homeIcon, label: 'Домой'},
    {icon: briefcaseIcon, label: 'На работу'},
  ];

  return (
    <div className='bg-[#222222] text-white h-full flex flex-col justify-between'>
      <div>
        <div className=''>
          <div className='flex items-center space-x-3 bg-[#2F2F2F] h-[40px] rounded-lg p-3 mb-3'>
            <img src={greenCircle} alt='' className='w-3 h-3' />
            <input
              type='text'
              placeholder='Откуда поедем?'
              value={fromValue}
              onChange={(e) => setFromValue(e.target.value)}
              className='flex-1 bg-transparent text-white placeholder-gray-400 outline-none'
            />
            <img src={equalIcon} alt='' className='w-4 h-4' />
          </div>

          <div className='flex items-center space-x-3 bg-[#2F2F2F] h-[40px] rounded-lg p-3'>
            <img src={blueCircle} alt='' className='w-3 h-3' />
            <input
              type='text'
              placeholder='Куда поедем?'
              value={toValue}
              onChange={(e) => setToValue(e.target.value)}
              className='flex-1 bg-transparent text-white placeholder-gray-400 outline-none'
            />
            <img src={equalIcon} alt='' className='w-4 h-4' />
          </div>
        </div>

        {/* Транспортные опции */}
        <div className='pt-[15px] mr-[-15px] '>
          <div className='flex space-x-2 overflow-x-auto'>
            {transportOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setSelectedTransport(option.id)}
                className={` flex flex-col items-center p-3 pt-1 pb-1 rounded-lg transition-colors ${
                  selectedTransport === option.id ? 'bg-[#666666] text-white' : ''
                }`}
              >
                <img src={option.icon} alt={option.label} className='w-6 h-6 mb-1' />
              </button>
            ))}
          </div>
        </div>

        {/* Быстрые кнопки */}
        <div className=' pb-4'>
          <div className='flex space-x-3'>
            {quickButtons.map((button, index) => (
              <button
                key={index}
                className='gap-[5px] flex mt-[15px] items-center p-3 pt-1 pb-1  hover:bg-gray-700 transition-colors'
              >
                <img src={button.icon} alt={button.label} className='' />
                <span className=' text-gray-300'>{button.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Кнопка маршрута для инвалидных колясок */}
        <div className='pb-4'>
          <button
            onClick={handleWheelchairRoute}
            disabled={isLoading || !firstPoint || !secondPoint}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              isLoading || !firstPoint || !secondPoint
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isLoading ? 'Загрузка...' : 'Маршрут для инвалидных колясок'}
          </button>
        </div>
      </div>

      {/* Нижняя навигация */}
      <div className='ml-[-15px] mr-[-15px] border-t border-gray-700'>
        <div className='flex'>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-400 hover:text-white transition-colors'>
            <img src={searchIcon} alt='Поиск' className='w-5 h-5 mb-1' />
            <span className='text-xs'>Поиск</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-400 hover:text-white transition-colors'>
            <img src={routeIcon} alt='Проезд' className='w-5 h-5 mb-1' />
            <span className='text-xs'>Проезд</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-400 hover:text-white transition-colors'>
            <img src={navigatorIcon} alt='Навигатор' className='w-5 h-5 mb-1' />
            <span className='text-xs'>Навигатор</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-400 hover:text-white transition-colors'>
            <img src={friendsIcon} alt='Друзья' className='w-5 h-5 mb-1' />
            <span className='text-xs'>Друзья</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-400 hover:text-white transition-colors'>
            <img src={tipsIcon} alt='Советы' className='w-5 h-5 mb-1' />
            <span className='text-xs'>Советы</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Finder;
