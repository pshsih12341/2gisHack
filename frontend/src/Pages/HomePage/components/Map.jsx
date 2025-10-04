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
  const [isMapLoading, setIsMapLoading] = useState(true);
  const [mapError, setMapError] = useState(null);
  const [showGeolocationPrompt, setShowGeolocationPrompt] = useState(false);
  const [hasRequestedLocation, setHasRequestedLocation] = useState(false);

  const {location, error: geoError, isLoading: isGeoLoading, getCurrentPosition} = useGeolocation();

  useEffect(() => {
    if (!hasRequestedLocation && !isGeoLoading && !location && !geoError) {
      setShowGeolocationPrompt(true);
    }
  }, [hasRequestedLocation, isGeoLoading, location, geoError]);

  useEffect(() => {
    if (location && mapInstance && markerInstance) {
      mapInstance.setCenter([location.longitude, location.latitude]);
      mapInstance.setZoom(15);
      markerInstance.setCoordinates([location.longitude, location.latitude]);
    }
  }, [location, mapInstance, markerInstance]);
  function mapResponseToFeatures(response) {
    const features = [];
    const currentRes = response?.stages[0].routes;
    response?.stages[0]?.routes?.forEach((route) => {
      route?.raw_data?.movements?.forEach((movement) => {
        movement?.alternatives?.forEach((alternative) => {
          alternative?.geometry?.forEach((geom) => {
            const geometry = wellknown.parse(geom.selection);
            if (geometry) {
              features.push({
                type: 'Feature',
                geometry: geometry,
              });
            }
          });
        });
      });
    });
    return {
      type: 'FeatureCollection',
      features: features,
    };
  }

  useEffect(() => {
    let map;
    setIsMapLoading(true);
    setMapError(null);

    const initMap = async () => {
      try {
        const mapglAPI = await load();
        const center = location ? [location.longitude, location.latitude] : [37.61556, 55.75222];

        map = new mapglAPI.Map('map-container', {
          center,
          zoom: location ? 15 : 10,
          key: 'dcae5afc-c412-4a64-a4a0-53e033d88bc6',
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

        const source = new mapglAPI.GeoJsonSource(map, {
          data: mapResponseToFeatures(bigResponce),
          attributes: {
            bar: 'asd',
          },
        });
        setSourceInstance(source);
        const layer = {
          id: 'my-polygons-layer', // ID каждого слоя должен быть уникальным

          // Логика фильтрации или выбора данных для этого слоя
          filter: [
            'match',
            ['sourceAttr', 'bar'],
            ['asd'],
            true, // Значение при совпадении атрибута bar источника cо значением "asd"
            false, // Значение при несовпадении
          ],

          // Тип объекта отрисовки
          type: 'line',

          // Стиль объекта отрисовки
          style: {
            color: '#0000ff',
            width: 2,
          },
        };
        map.on('styleload', () => {
          map.addLayer(layer);
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
    getCurrentPosition();
  };

  const handleDenyGeolocation = () => {
    setShowGeolocationPrompt(false);
    setHasRequestedLocation(true);
  };

  // Функции для пешеходных маршрутов
  const handleMapClick = async (event) => {
    const coordinates = [event.lngLat[0], event.lngLat[1]];
    // const route = axios.post(
    //   'https://routing.api.2gis.com/public_transport/2.0?key=dcae5afc-c412-4a64-a4a0-53e033d88bc6',
    //   {
    //     locale: 'ru',
    //     source: {
    //       name: 'Начальная точка',
    //       point: {
    //         lat: location.latitude,
    //         lon: location.longitude,
    //       },
    //     },
    //     target: {
    //       name: 'Конечная точка',
    //       point: {
    //         lat: coordinates[1],
    //         lon: coordinates[0],
    //       },
    //     },
    //     transport: ['bus', 'tram', 'pedestrian', 'metro'],
    //   }
    // );
    // console.log(route);
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
