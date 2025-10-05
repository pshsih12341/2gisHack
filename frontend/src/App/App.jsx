import React from 'react';
import {createRoot} from 'react-dom/client';
import Routing from './Routing';
import PWAUpdatePrompt from '../components/PWAUpdatePrompt';
import PWAInstallPrompt from '../components/PWAInstallPrompt';
import './index.css';
import MapProvider from '../Shared/MapContenxProvider';
import {RouteProvider} from '../Shared/RouteContext';

const App = () => {
  return (
    <MapProvider>
      <RouteProvider>
        <Routing />
      </RouteProvider>
    </MapProvider>
  );
};

createRoot(document.getElementById('root')).render(<App />);
