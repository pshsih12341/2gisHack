import React, {useEffect, useState} from 'react';
import {load} from '@2gis/mapgl';
import {Directions} from '@2gis/mapgl-directions';
import {useGeolocation} from '../../../Shared/hooks/useGeolocation';
import GeolocationPrompt from '../../../components/GeolocationPrompt';
import markerIcon from '../../../Shared/imgs/mark.png';
import {useRoute} from '../../../Shared/RouteContext';
import {useStore} from '../../../App/store';
import {ROUTING_API_KEY} from '../../../Api/config';
import axios from 'axios';

const MapWrapper = React.memo(
  () => {
    return <div id='map-container' style={{width: '100%', height: '100%'}}></div>;
  },
  () => true
);

const Map = () => {
  const [mapInstance, setMapInstance] = useState(null);
  const [markerInstance, setMarkerInstance] = useState(null);
  const [isMapLoading, setIsMapLoading] = useState(true);
  const [mapError, setMapError] = useState(null);
  const [showGeolocationPrompt, setShowGeolocationPrompt] = useState(false);
  const [hasRequestedLocation, setHasRequestedLocation] = useState(false);
  const [directionsInstance, setDirectionsInstance] = useState(null);

  const {location, error: geoError, isLoading: isGeoLoading, getCurrentPosition} = useGeolocation();
  const {updateRouteData} = useRoute();
  const {geolocationPermission, setGeolocationPermission, responsePoints, firstRoutePoint} = useStore();

  useEffect(() => {
    // Показываем промпт только если разрешение еще не запрашивалось
    if (geolocationPermission === null && !hasRequestedLocation && !isGeoLoading && !location && !geoError) {
      setShowGeolocationPrompt(true);
    }
  }, [geolocationPermission, hasRequestedLocation, isGeoLoading, location, geoError]);

  useEffect(() => {
    if (location && mapInstance && markerInstance) {
      mapInstance.setCenter([location.longitude, location.latitude]);
      mapInstance.setZoom(15);
      markerInstance.setCoordinates([location.longitude, location.latitude]);
    }
  }, [location, mapInstance, markerInstance]);

  // Функция для построения маршрута по точкам из Zustand store
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
  // Функция для построения маршрута по клику
  const buildRouteOnClick = async (map, clickCoordinates) => {
    try {
      if (directionsInstance) {
        directionsInstance.clear();
      }

      const directions = new Directions(map, {
        directionsApiKey: ROUTING_API_KEY,
      });
      setDirectionsInstance(directions);

      let startPoint;
      console.log('buildRouteOnClick - location:', location);
      console.log('buildRouteOnClick - markerInstance:', markerInstance);

      if (location && location.longitude && location.latitude) {
        startPoint = [location.longitude, location.latitude];
        console.log('Using geolocation:', startPoint);
      } else if (markerInstance) {
        // Получаем координаты маркера как fallback
        const markerCoords = markerInstance.getCoordinates();
        if (markerCoords && markerCoords.length >= 2) {
          startPoint = [markerCoords[0], markerCoords[1]];
          console.log('Using marker coordinates:', startPoint);
        } else {
          startPoint = [37.61556, 55.75222];
          console.log('Marker coords invalid, using default:', startPoint);
        }
      } else {
        startPoint = [37.61556, 55.75222];
        console.log('No location or marker, using default coordinates:', startPoint);
      }

      // Конечная точка - место клика
      const endPoint = [clickCoordinates[0], clickCoordinates[1]];

      console.log('Building route from:', startPoint, 'to:', endPoint);

      const response = await axios.post(`https://2gis.misisxmisis.ru/api/map/route/safely`, {
        points: [
          {
            lon: `${startPoint[0]}`,
            lat: `${startPoint[1]}`,
            type: 'stop',
          },
          {
            lon: `${endPoint[0]}`,
            lat: `${endPoint[1]}`,
            type: 'stop',
          },
        ],
      });

      console.log('API Response:', response.data.query);

      const points = response.data.query.points.map((point) => [
        parseFloat(point.lon), // [longitude, latitude] - формат для Directions API
        parseFloat(point.lat),
      ]);

      // Строим пешеходный маршрут
      directions
        .pedestrianRoute({
          points: points,
        })
        .catch((error) => {
          console.error('Error building route:', error);
        });
    } catch (error) {
      console.error('Error building route on click:', error);
    }
  };

  // Инициализация карты - запускается только один раз при монтировании
  useEffect(() => {
    let map;
    setIsMapLoading(true);
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
          key: 'dcf704a4-be05-4c21-be87-e7f292ee00f1',
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
        // Добавляем обработчик кликов на карту
        map.on('click', (event) => {
          const coordinates = [event.lngLat[0], event.lngLat[1]];

          // Добавляем временный маркер в месте клика
          const clickMarker = new mapglAPI.Marker(map, {
            coordinates: coordinates,
            icon: markerIcon,
            size: [24, 24],
            anchor: [12, 24],
          });
          clickMarker.show();

          buildRouteOnClick(map, coordinates);
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
      if (map) {
        map.destroy();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAllowGeolocation = () => {
    setShowGeolocationPrompt(false);
    setHasRequestedLocation(true);
    setGeolocationPermission('granted');
    getCurrentPosition();

    updateRouteData({
      stages: [],
      totalTime: 0,
      totalDistance: 0,
      message: 'Геолокация разрешена! Теперь вы можете строить маршруты.',
    });
  };

  const handleDenyGeolocation = () => {
    setShowGeolocationPrompt(false);
    setHasRequestedLocation(true);
    setGeolocationPermission('denied');
    // Открываем попап после запрета геолокации
    updateRouteData({
      stages: [],
      totalTime: 0,
      totalDistance: 0,
      message: 'Геолокация запрещена. Некоторые функции могут быть недоступны.',
    });
  };

  return (
    <div className='w-full h-full space-y-4'>
      {/* Промпт геолокации */}
      {showGeolocationPrompt && (
        <GeolocationPrompt onAllow={handleAllowGeolocation} onDeny={handleDenyGeolocation} isLoading={isGeoLoading} />
      )}

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
