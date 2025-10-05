import React, {useEffect, useState} from 'react';
import {load} from '@2gis/mapgl';
import {useGeolocation} from '../../../Shared/hooks/useGeolocation';
import GeolocationPrompt from '../../../components/GeolocationPrompt';
import markerIcon from '../../../Shared/imgs/mark.png';
import RoutingService from '../../../Api/routingService';
import {ROUTING_API_KEY} from '../../../Api/config';
import axios from 'axios';
import {bigResponce} from '../consts';
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
  function generateLayers(response, mapglAPI, map, isRoute) {
    const colors = ['#0000ff', '#ff0000', '#00ff00', '#ffa500', '#800080'];
    const layers = [];
    console.log(response);
    response?.stages?.forEach((stage, index) => {
      const features = [];
      stage.routes?.forEach((route) => {
        if (isRoute) {
          route?.raw_data?.maneuvers?.forEach((maneuver) => {
            console.log(1);
            maneuver?.outcoming_path?.geometry?.forEach((alternative) => {
              console.log(2);
              const geometry = wellknown.parse(alternative.selection);
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
        } else {
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
        }
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
          width: 4,
        },
      };
      layers.push(layer);
    });
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

        map.on('styleload', () => {
          const layers = generateLayers(bigResponce, mapglAPI, map, true);
          layers.forEach((layer) => {
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
    // const response = await axios.post(`https://2gis.misisxmisis.ru/api/map/plan-route`, {
    //   query:
    //     'Хочу доехать от метро Бунинская аллея до офиса 2гис на Даниловской набережной. Хочу сначала дойти до станции метро Бульвар Дмитрия Донского пешком, чтобы положить деньги в банкомат и где-нибудь поесть в фастфуде. Потом хочу добраться до конечной точки как можно быстрее на такси.',
    //   region_id: 'moscow',
    // });
    const response = await axios.post(`https://2gis.misisxmisis.ru/api/map/plan-route`, {
      query:
        'Хочу доехать от метро Бунинская аллея до офиса 2гис на Даниловской набережной. Хочу сначала дойти до станции метро Бульвар Дмитрия Донского пешком, чтобы положить деньги в банкомат и где-нибудь поесть в фастфуде. Потом хочу добраться до конечной точки как можно быстрее на такси.',
      region_id: 'moscow',
    });
    if (mapInstance) {
      mapInstance.destroy();
    }
    const newMap = new mapglAPIState.Map('map-container', {
      center: coordinates,
      zoom: 15,
      key: 'dcae5afc-c412-4a64-a4a0-53e033d88bc6',
    });
    newMap.on('click', handleMapClick);
    setMapInstance(newMap);
    const layers = generateLayers(response.data, mapglAPIState, newMap, true);
    newMap.on('styleload', () => {
      layers.forEach((layer) => {
        newMap.addLayer(layer);
      });
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
