import React, {useEffect, useState, useCallback, useRef, useContext} from 'react';
import {load} from '@2gis/mapgl';
import {Directions} from '@2gis/mapgl-directions';
import {useGeolocation} from '../../../Shared/hooks/useGeolocation';
import GeolocationPrompt from '../../../components/GeolocationPrompt';
import markerIcon from '../../../Shared/imgs/mark.png';
import {useStore} from '../../../App/store';
import {ROUTING_API_KEY} from '../../../Api/config';
import startIcon from '../../../Shared/imgs/startIcon.png';
import endIcon from '../../../Shared/imgs/finishIcon.png';
import {MapContext} from '../../../Shared/MapContenxProvider';

const MapWrapper = React.memo(
  () => {
    return <div id='map-container' style={{width: '100%', height: '100%'}}></div>;
  },
  () => true
);

const Map = () => {
  const [mapInstance, setMapInstance] = useContext(MapContext);
  const [markerInstance, setMarkerInstance] = useState(null);
  const [firstPointMarker] = useState(null);
  const [isMapLoading, setIsMapLoading] = useState(true);
  const counter = useRef(0);
  const [mapError, setMapError] = useState(null);
  const [directionsInstance, setDirectionsInstance] = useState(null);
  const {location} = useGeolocation();
  const {responsePoints, firstRoutePoint, setFirstPoint, secondPoint, setSecondPoint} = useStore();

  useEffect(() => {
    if (location && mapInstance && markerInstance) {
      mapInstance.setCenter([location.longitude, location.latitude]);
      mapInstance.setZoom(15);
      markerInstance.setCoordinates([location.longitude, location.latitude]);
    }
  }, [location, mapInstance, markerInstance]);

  const buildRouteFromStore = async (map, points) => {
    try {
      if (directionsInstance) {
        directionsInstance.clear();
      }

      const directions = new Directions(map, {
        directionsApiKey: ROUTING_API_KEY,
      });
      setDirectionsInstance(directions);

      console.log('Building route from Zustand store points:', points);
      const directionsPoints = points.map((point) => [parseFloat(point.longitude), parseFloat(point.latitude)]);

      console.log('Directions API points:', directionsPoints);

      directions.pedestrianRoute({
        points: directionsPoints,
      });
    } catch (error) {
      console.error('Error building route from Zustand store:', error);
    }
  };

  // Функция для обработки клика на карте
  const handleMapClick = useCallback(
    async (event, map, mapglAPI) => {
      if (!map) return;

      const coordinates = [event.lngLat[0], event.lngLat[1]];
      const pointData = {
        lon: coordinates[0],
        lat: coordinates[1],
        full_name: `Точка ${coordinates[0].toFixed(6)}, ${coordinates[1].toFixed(6)}`,
        address_name: `Точка ${coordinates[0].toFixed(6)}, ${coordinates[1].toFixed(6)}`,
      };
      if (counter.current === 1) {
        setSecondPoint(pointData);
        const marker = new mapglAPI.Marker(map, {
          coordinates: coordinates,
          icon: endIcon,
          size: [32, 32],
          anchor: [16, 32],
        });
        marker.show();
      } else {
        setFirstPoint(pointData);
        counter.current = 1;
        const marker = new mapglAPI.Marker(map, {
          coordinates: coordinates,
          icon: startIcon,
          size: [32, 32],
          anchor: [16, 32],
        });
        marker.show();
      }
    },
    [secondPoint, setFirstPoint, setSecondPoint]
  );

  // Инициализация карты - запускается только один раз при монтировании
  useEffect(() => {
    let map;

    setMapError(null);

    const initMap = async () => {
      try {
        const mapglAPI = await load();
        const center = firstRoutePoint
          ? [firstRoutePoint.longitude, firstRoutePoint.latitude]
          : location
            ? [location.longitude, location.latitude]
            : [37.61556, 55.75222];

        map = new mapglAPI.Map('map-container', {
          center,
          zoom: location ? 15 : 10,
          key: '7889d023-2357-402b-a407-b16c3b316fd5',
        });
        setMapInstance(map);
        setIsMapLoading(false);
        const marker = new mapglAPI.Marker(map, {
          coordinates: location ? [location.longitude, location.latitude] : [37.61556, 55.75222],
          icon: markerIcon,
          size: [32, 32],
          anchor: [16, 32],
        });

        marker.show();
        setMarkerInstance(marker);
        if (responsePoints) {
          buildRouteFromStore(map, responsePoints);
        }

        map.on('click', (ev) => {
          handleMapClick(ev, map, mapglAPI);
        });
      } catch (error) {
        setMapError(error.message);
        setIsMapLoading(false);
      }
    };

    initMap();

    return () => {
      if (markerInstance) {
        markerInstance.destroy();
      }
      if (firstPointMarker) {
        firstPointMarker.destroy();
      }
      if (map) {
        map.off('click', handleMapClick);
        map.destroy();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className='w-full h-full space-y-4'>
      {/* Карта */}
      <div className='w-full h-full border border-gray-300 rounded-lg overflow-hidden relative'>
        {isMapLoading && (
          <div className='absolute inset-0 flex items-center justify-center bg-gray-100'>
            <span className='text-gray-600'>Загрузка карты...</span>
          </div>
        )}
        {mapError && (
          <div className='absolute inset-0 flex items-center justify-center bg-red-100'>
            <span className='text-red-600'>Ошибка карты: {mapError}</span>
          </div>
        )}
        <MapWrapper />
      </div>
    </div>
  );
};

export default Map;
