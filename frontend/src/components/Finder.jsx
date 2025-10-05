import React, {useState, useEffect, useRef} from 'react';
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
import {geocodingService} from '../Api/geocodingService';
import {useDebounce} from '../Shared/hooks/useDebounce';

const Finder = ({onAddressSelect}) => {
  const [fromValue, setFromValue] = useState('');
  const [toValue, setToValue] = useState('');
  const [selectedTransport, setSelectedTransport] = useState('car');

  // Состояние для поиска адресов
  const [fromSuggestions, setFromSuggestions] = useState([]);
  const [toSuggestions, setToSuggestions] = useState([]);
  const [showFromSuggestions, setShowFromSuggestions] = useState(false);
  const [showToSuggestions, setShowToSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  // Refs для управления фокусом
  const fromInputRef = useRef(null);
  const toInputRef = useRef(null);
  const fromSuggestionsRef = useRef(null);
  const toSuggestionsRef = useRef(null);

  // Debounced значения для поиска
  const debouncedFromValue = useDebounce(fromValue, 300);
  const debouncedToValue = useDebounce(toValue, 300);

  // Функция поиска адресов
  const searchAddresses = async (query, setSuggestions) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await geocodingService.searchAddresses(query);
      setSuggestions(results);
    } catch (error) {
      console.error('Error searching addresses:', error);
      setSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Обработчики выбора адреса
  const handleFromAddressSelect = (address) => {
    setFromValue(address.full_name || address.address_name);
    setShowFromSuggestions(false);
    if (onAddressSelect) {
      onAddressSelect('from', address);
    }
  };

  const handleToAddressSelect = (address) => {
    setToValue(address.full_name || address.address_name);
    setShowToSuggestions(false);
    if (onAddressSelect) {
      onAddressSelect('to', address);
    }
  };

  // Эффекты для поиска при изменении debounced значений
  useEffect(() => {
    if (debouncedFromValue) {
      searchAddresses(debouncedFromValue, setFromSuggestions);
    } else {
      setFromSuggestions([]);
    }
  }, [debouncedFromValue]);

  useEffect(() => {
    if (debouncedToValue) {
      searchAddresses(debouncedToValue, setToSuggestions);
    } else {
      setToSuggestions([]);
    }
  }, [debouncedToValue]);

  // Обработчики клика вне области для закрытия выпадающих списков
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        fromSuggestionsRef.current &&
        !fromSuggestionsRef.current.contains(event.target) &&
        fromInputRef.current &&
        !fromInputRef.current.contains(event.target)
      ) {
        setShowFromSuggestions(false);
      }
      if (
        toSuggestionsRef.current &&
        !toSuggestionsRef.current.contains(event.target) &&
        toInputRef.current &&
        !toInputRef.current.contains(event.target)
      ) {
        setShowToSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
          <div className='relative'>
            <div className='flex items-center space-x-3 bg-[#2F2F2F] h-[40px] rounded-lg p-3'>
              <img src={greenCircle} alt='' className='w-3 h-3' />
              <input
                ref={fromInputRef}
                type='text'
                placeholder='Откуда поедем?'
                value={fromValue}
                onChange={(e) => {
                  setFromValue(e.target.value);
                  setShowFromSuggestions(true);
                }}
                onFocus={() => setShowFromSuggestions(true)}
                className='flex-1 bg-transparent text-white placeholder-gray-400 outline-none'
              />
              {isSearching && fromValue && (
                <div className='w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin' />
              )}
              <img src={equalIcon} alt='' className='w-4 h-4' />
            </div>

            {/* Выпадающий список для "Откуда" */}
            {showFromSuggestions && fromSuggestions.length > 0 && (
              <div
                ref={fromSuggestionsRef}
                className='absolute top-full left-0 right-0 mt-1 bg-[#2F2F2F] rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto'
              >
                {fromSuggestions.map((address, index) => (
                  <div
                    key={index}
                    onClick={() => handleFromAddressSelect(address)}
                    className='p-3 hover:bg-[#404040] cursor-pointer border-b border-gray-600 last:border-b-0'
                  >
                    <div className='text-white text-sm font-medium'>{address.full_name || address.address_name}</div>
                    {address.address_name && address.address_name !== address.full_name && (
                      <div className='text-gray-400 text-xs mt-1'>{address.address_name}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className='relative'>
            <div className='flex items-center space-x-3 bg-[#2F2F2F] h-[40px] rounded-lg p-3'>
              <img src={blueCircle} alt='' className='w-3 h-3' />
              <input
                ref={toInputRef}
                type='text'
                placeholder='Куда поедем?'
                value={toValue}
                onChange={(e) => {
                  setToValue(e.target.value);
                  setShowToSuggestions(true);
                }}
                onFocus={() => setShowToSuggestions(true)}
                className='flex-1 bg-transparent text-white placeholder-gray-400 outline-none'
              />
              {isSearching && toValue && (
                <div className='w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin' />
              )}
              <img src={equalIcon} alt='' className='w-4 h-4' />
            </div>

            {/* Выпадающий список для "Куда" */}
            {showToSuggestions && toSuggestions.length > 0 && (
              <div
                ref={toSuggestionsRef}
                className='absolute top-full left-0 right-0 mt-1 bg-[#2F2F2F] rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto'
              >
                {toSuggestions.map((address, index) => (
                  <div
                    key={index}
                    onClick={() => handleToAddressSelect(address)}
                    className='p-3 hover:bg-[#404040] cursor-pointer border-b border-gray-600 last:border-b-0'
                  >
                    <div className='text-white text-sm font-medium'>{address.full_name || address.address_name}</div>
                    {address.address_name && address.address_name !== address.full_name && (
                      <div className='text-gray-400 text-xs mt-1'>{address.address_name}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
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
