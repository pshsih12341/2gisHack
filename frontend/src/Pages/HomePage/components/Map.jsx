import React, {useEffect, useState} from 'react';
import {load} from '@2gis/mapgl';
import {useGeolocation} from '../../../Shared/hooks/useGeolocation';
import GeolocationPrompt from '../../../components/GeolocationPrompt';
import markerIcon from '../../../Shared/imgs/mark.png';
import RoutingService from '../../../Api/routingService';
import {ROUTING_API_KEY} from '../../../Api/config';
import axios from 'axios';
import {bigResponce, responce} from '../consts';
import wellknown from 'wellknown';
import {useRoute} from '../../../Shared/RouteContext';
import {useStore} from '../../../App/store';

const MapWrapper = React.memo(
  () => {
    return <div id='map-container' style={{width: '100%', height: '100%'}}></div>;
  },
  () => true
);

const Map = () => {
  const [mapInstance, setMapInstance] = useState(null);
  const [sourceInstance, setSourceInstance] = useState(null);
  const [markerInstance, setMarkerInstance] = useState(null);
  const [mapglAPIState, setMapglAPIState] = useState(null);
  const [isMapLoading, setIsMapLoading] = useState(true);
  const [mapError, setMapError] = useState(null);
  const [showGeolocationPrompt, setShowGeolocationPrompt] = useState(false);
  const [hasRequestedLocation, setHasRequestedLocation] = useState(false);

  const {location, error: geoError, isLoading: isGeoLoading, getCurrentPosition} = useGeolocation();
  const {updateRouteData} = useRoute();
  const {geolocationPermission, setGeolocationPermission} = useStore();

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
  function generateLayers(response, mapglAPI, map) {
    const colors = ['#0000ff', '#ff0000', '#00ff00', '#ffa500', '#800080'];
    const layers = [];
    response?.stages?.forEach((stage, index) => {
      const features = [];
      stage.routes?.forEach((route) => {
        route?.raw_data?.movements?.forEach((movement) => {
          movement?.alternatives?.forEach((alternative) => {
            alternative?.geometry?.forEach((geom) => {
              const geometry = wellknown.parse(geom.selection);
              if (geometry) {
                features.push({
                  type: 'Feature',
                  geometry: geometry,
                  properties: {
                    bar: index.toString(),
                  },
                });
              }
            });
          });
        });
      });

      const source = new mapglAPI.GeoJsonSource(map, {
        data: {
          type: 'FeatureCollection',
          features: features,
        },
        attributes: {
          bar: index.toString(),
        },
      });
      const color = colors[index];
      const layer = {
        id: `my-polygons-layer-${index}`,

        filter: ['match', ['sourceAttr', 'bar'], [index.toString()], true, false],
        type: 'line',
        style: {
          color: color,
          width: 2,
        },
      };
      layers.push(layer);
    });
    console.log(layers);
    return layers;
  }

  useEffect(() => {
    let map;
    setIsMapLoading(true);
    setMapError(null);

    const initMap = async () => {
      try {
        const mapglAPI = await load();
        setMapglAPIState(mapglAPI);
        const center = location ? [location.longitude, location.latitude] : [37.61556, 55.75222];

        map = new mapglAPI.Map('map-container', {
          center,
          zoom: location ? 15 : 10,
          key: 'dcae5afc-casdasd',
        });

        setMapInstance(map);
        setIsMapLoading(false);
        const marker = new mapglAPI.Marker(map, {
          coordinates: center,
          icon: markerIcon,
          size: [32, 32],
          anchor: [16, 32],
        });

        marker.show();
        setMarkerInstance(marker);

        map.on('styleload', () => {
          const layers = generateLayers(bigResponce, mapglAPI, map);
          layers.forEach((layer) => {
            console.log(layer);
            map.addLayer(layer);
          });
        });

        map.on('click', handleMapClick);
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
        map.off('click', handleMapClick);
        map.destroy();
      }
    };
  }, [location]);

  const handleAllowGeolocation = () => {
    setShowGeolocationPrompt(false);
    setHasRequestedLocation(true);
    setGeolocationPermission('granted');
    getCurrentPosition();
    // Открываем попап после разрешения геолокации
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

  // Функции для пешеходных маршрутов
  const handleMapClick = async (event) => {
    const coordinates = [event.lngLat[0], event.lngLat[1]];

    // Генерируем слои для отображения на карте
    const layers = generateLayers(bigResponce, mapglAPIState, mapInstance);
    layers.forEach((layer) => {
      try {
        mapInstance.addLayer(layer);
        console.log(`Layer ${layer.id} added successfully`);
      } catch (error) {
        console.error(`Error adding layer ${layer.id}:`, error);
      }
    });

    // Обновляем данные маршрута в контексте
    const mockRouteData = {
      stages: bigResponce.stages || [],
      totalTime: 45, // Примерное время в минутах
      totalDistance: 2500, // Примерное расстояние в метрах
      startPoint: {
        lat: location?.latitude || 55.75222,
        lng: location?.longitude || 37.61556,
        name: 'Ваше местоположение',
      },
      endPoint: {
        lat: coordinates[1],
        lng: coordinates[0],
        name: 'Выбранная точка',
      },
    };

    updateRouteData(mockRouteData);
  };
  console.log(mapInstance);
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
