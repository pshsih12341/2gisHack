import React, {useRef, useState, useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import axios from 'axios';
import {useStore} from '../../App/store';

// Компонент для форматированного отображения сообщений
const FormattedMessage = ({text, onNavigateToRoute}) => {
  const formatText = (text) => {
    return text.split('\n').map((line, index) => {
      // Обработка заголовков с эмодзи
      if (line.includes('✅') && line.includes('Многоэтапный маршрут')) {
        return (
          <div key={index} className='text-green-400 font-semibold text-base mb-2'>
            {line}
          </div>
        );
      }

      // Обработка этапов маршрута
      if (line.includes('🔄') && line.includes('Этап')) {
        return (
          <div key={index} className='text-blue-300 font-medium text-sm mb-1 ml-2'>
            {line}
          </div>
        );
      }

      // Обработка подэтапов с отступами
      if (line.includes('🚗') || line.includes('🚶') || line.includes('🚌')) {
        return (
          <div key={index} className='text-gray-300 text-xs mb-1 ml-6'>
            {line}
          </div>
        );
      }

      // Обработка пустых строк
      if (line.trim() === '') {
        return <div key={index} className='h-2'></div>;
      }

      // Обычный текст
      return (
        <div key={index} className='text-gray-200 text-sm mb-1'>
          {line}
        </div>
      );
    });
  };

  return (
    <div className='space-y-1'>
      {formatText(text)}
      <div className='mt-3 pt-2 border-t border-gray-600'>
        <button
          onClick={onNavigateToRoute}
          className='w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2'
        >
          <span>🗺️</span>
          Перейти к маршруту
        </button>
      </div>
    </div>
  );
};

const ChatPage = () => {
  const navigate = useNavigate();
  const {setResponsePoints, setFirstRoutePoint, chatMessages, addChatMessage, clearChatMessages} = useStore();
  const points = useRef(null);
  const [newMessage, setNewMessage] = useState('');

  const handleBackClick = () => {
    navigate('/');
  };

  const handleNavigateToRoute = () => {
    navigate('/');
  };

  // Инициализация сообщений из store при загрузке
  useEffect(() => {
    if (chatMessages.length === 0) {
      // Добавляем приветственное сообщение, если чат пустой
      const welcomeMessage = {
        id: 1,
        text: 'Привет! Я ваш помощник по навигации. Чем могу помочь?',
        isBot: true,
        timestamp: new Date().toLocaleTimeString(),
      };
      addChatMessage(welcomeMessage);
    }
  }, [chatMessages.length, addChatMessage]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
      const userMessage = {
        id: Date.now(),
        text: newMessage,
        isBot: false,
        timestamp: new Date().toLocaleTimeString(),
      };

      addChatMessage(userMessage);
      const userQuery = newMessage;
      setNewMessage('');

      // Показываем индикатор загрузки
      const loadingMessage = {
        id: Date.now() + 1,
        text: 'Помощник печатает...',
        isBot: true,
        timestamp: new Date().toLocaleTimeString(),
        isLoading: true,
      };
      addChatMessage(loadingMessage);

      try {
        // Отправляем запрос к API
        const response = await axios.post('https://2gis.misisxmisis.ru/api/map/plan-route', {
          query: userQuery,
          region: 'moscow',
        });

        console.log('API Response:', response.data);

        // Удаляем сообщение загрузки
        const updatedMessages = chatMessages.filter((msg) => !msg.isLoading);
        // Очищаем store и добавляем сообщения без loading
        clearChatMessages();
        updatedMessages.forEach((msg) => addChatMessage(msg));

        // Сохраняем точки в Zustand store
        if (response.data.points) {
          setResponsePoints(response.data.points);
          // Сохраняем первую точку для центрирования карты
          if (response.data.points.length > 0) {
            setFirstRoutePoint(response.data.points[0]);
            console.log('First route point saved to store:', response.data.points[0]);
          }
          console.log('Points saved to Zustand store:', response.data.points);
        }

        // Добавляем ответ от API
        const botMessage = {
          id: Date.now() + 2,
          text: response.data.text || response.data.message || 'Получил ваш запрос! Обрабатываю маршрут...',
          isBot: true,
          timestamp: new Date().toLocaleTimeString(),
          isFormatted: true, // Флаг для форматированного отображения
        };
        addChatMessage(botMessage);
        points.current = response.data.points;
      } catch (error) {
        console.error('Error sending message to API:', error);

        // Удаляем сообщение загрузки
        const updatedMessages = chatMessages.filter((msg) => !msg.isLoading);
        clearChatMessages();
        updatedMessages.forEach((msg) => addChatMessage(msg));

        // Добавляем сообщение об ошибке
        const errorMessage = {
          id: Date.now() + 2,
          text: 'Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.',
          isBot: true,
          timestamp: new Date().toLocaleTimeString(),
        };
        addChatMessage(errorMessage);
      }
    }
  };

  return (
    <div className='w-full h-full bg-[#222222] text-white flex flex-col'>
      {/* Header */}
      <div className='bg-[#2F2F2F] p-4 border-b border-gray-700 flex items-center gap-4'>
        <button
          onClick={handleBackClick}
          className='w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500 transition-colors'
        >
          <span className='text-white text-sm font-medium'>←</span>
        </button>
        <div>
          <h1 className='text-lg font-semibold'>Чат с помощником</h1>
          <p className='text-sm text-gray-400'>Онлайн</p>
        </div>
      </div>

      {/* Messages */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {chatMessages.map((message) => (
          <div key={message.id} className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}>
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.isBot ? 'bg-[#2F2F2F] text-white' : 'bg-blue-600 text-white'
              } ${message.isLoading ? 'opacity-70' : ''}`}
            >
              {message.isFormatted ? (
                <FormattedMessage text={message.text} onNavigateToRoute={handleNavigateToRoute} />
              ) : (
                <p className='text-sm'>{message.text}</p>
              )}
              {message.isLoading && (
                <div className='flex space-x-1 mt-2'>
                  <div className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'></div>
                  <div
                    className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
                    style={{animationDelay: '0.1s'}}
                  ></div>
                  <div
                    className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
                    style={{animationDelay: '0.2s'}}
                  ></div>
                </div>
              )}
              <p className='text-xs opacity-70 mt-1'>{message.timestamp}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className='bg-[#2F2F2F] p-4 border-t border-gray-700'>
        <form onSubmit={handleSendMessage} className='flex gap-2'>
          <input
            type='text'
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder='Введите сообщение...'
            className='flex-1 bg-[#404040] text-white placeholder-gray-400 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500'
          />
          <button
            type='submit'
            className='bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors'
          >
            Отправить
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPage;
