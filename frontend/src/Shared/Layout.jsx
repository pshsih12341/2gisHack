import React from 'react';
import {Outlet} from 'react-router-dom';

const Layout = () => {
  return (
    <div className='h-screen flex flex-col'>
      <main className='flex-1 overflow-hidden'>
        <Outlet />
      </main>

      <nav className='bg-white border-t safe-area-bottom' role='navigation' aria-label='Основная навигация'>
        <div className='flex'>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-600 hover:text-blue-600 focus-visible'>
            <span className='text-2xl mb-1' aria-hidden='true'>
              🗺️
            </span>
            <span className='text-xs font-medium'>Карта</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-600 hover:text-blue-600 focus-visible'>
            <span className='text-2xl mb-1' aria-hidden='true'>
              💬
            </span>
            <span className='text-xs font-medium'>Чат</span>
          </button>
          <button className='flex-1 flex flex-col items-center py-3 px-2 text-gray-600 hover:text-blue-600 focus-visible'>
            <span className='text-2xl mb-1' aria-hidden='true'>
              👤
            </span>
            <span className='text-xs font-medium'>Профиль</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default Layout;
