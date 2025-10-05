import React from 'react';
import {Outlet} from 'react-router-dom';
import BottomDrawer from '../components/BottomDrawer';
import {useRoute} from './RouteContext';
import Finder from '../components/Finder';

const Layout = () => {
  const {routeData, isDrawerOpen, toggleDrawer} = useRoute();

  return (
    <div className='h-screen flex flex-col relative'>
      <main className='flex-1 overflow-hidden'>
        <Outlet />
      </main>

      {/* Выдвижной попап */}
      <BottomDrawer
        isOpen={isDrawerOpen}
        onToggle={toggleDrawer}
        title={routeData ? 'Детали маршрута' : 'Построение маршрута'}
      >
        <Finder />
      </BottomDrawer>
    </div>
  );
};

export default Layout;
