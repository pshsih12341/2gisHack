import React from 'react';
import {Button} from '../../components/ui/button';
import Map from './components/Map';
import {useNavigate, useOutletContext} from 'react-router-dom';

const HomePage = () => {
  const navigate = useNavigate();
  const {selectedFromPoint, selectedToPoint} = useOutletContext() || {};

  const handleProfileClick = () => {
    navigate('/profile');
  };

  const handleChatClick = () => {
    navigate('/chat');
  };

  return (
    <article className='w-full h-full'>
      <div className='absolute top-4 left-4 z-10 flex gap-2'>
        <button
          onClick={handleProfileClick}
          className='w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500 transition-colors'
        >
          <span className='text-white text-sm font-medium'>👤</span>
        </button>
        <button
          onClick={handleChatClick}
          className='w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500 transition-colors'
        >
          <span className='text-white text-sm font-medium'>💬</span>
        </button>
      </div>
      <Map selectedFromPoint={selectedFromPoint} selectedToPoint={selectedToPoint} />
    </article>
  );
};

export default HomePage;
