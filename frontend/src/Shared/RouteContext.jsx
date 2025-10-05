import React, {createContext, useContext, useState} from 'react';

const RouteContext = createContext();

export const useRoute = () => {
  const context = useContext(RouteContext);
  if (!context) {
    throw new Error('useRoute must be used within a RouteProvider');
  }
  return context;
};

export const RouteProvider = ({children}) => {
  const [routeData, setRouteData] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const updateRouteData = (data) => {
    setRouteData(data);
    if (data) {
      setIsDrawerOpen(true);
    }
  };

  const toggleDrawer = (open) => {
    setIsDrawerOpen(open);
  };

  const clearRoute = () => {
    setRouteData(null);
    setIsDrawerOpen(false);
  };

  const value = {
    routeData,
    isDrawerOpen,
    updateRouteData,
    toggleDrawer,
    clearRoute,
  };

  return <RouteContext.Provider value={value}>{children}</RouteContext.Provider>;
};
