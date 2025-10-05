import React, {useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import Routing from './Routing';
import './index.css';
import MapProvider from '../Shared/MapContenxProvider';
import {RouteProvider} from '../Shared/RouteContext';

const App = () => {
  // Регистрация Service Worker
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }
  }, []);

  return (
    <MapProvider>
      <RouteProvider>
        <Routing />
      </RouteProvider>
    </MapProvider>
  );
};

export default App;

createRoot(document.getElementById('root')).render(<App />);
