const ROUTING_API_URL = 'https://routing.api.2gis.com/public_transport/2.0';

class RoutingService {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  /**
   * Построить маршрут на общественном транспорте
   * @param {Object} params - Параметры маршрута
   * @param {Object} params.source - Начальная точка
   * @param {Object} params.target - Конечная точка
   * @param {Array} params.transport - Виды транспорта
   * @param {string} params.locale - Локаль (по умолчанию 'ru')
   * @returns {Promise<Array>} - Массив вариантов маршрутов
   */
  async getPublicTransportRoute(params) {
    const {
      source,
      target,
      transport = ['bus', 'tram', 'trolleybus', 'metro'],
      locale = 'ru'
    } = params;

    const requestBody = {
      locale,
      source: {
        name: source.name || 'Начальная точка',
        point: {
          lat: source.lat,
          lon: source.lon
        }
      },
      target: {
        name: target.name || 'Конечная точка',
        point: {
          lat: target.lat,
          lon: target.lon
        }
      },
      transport
    };

    try {
      const response = await fetch(`${ROUTING_API_URL}?key=${this.apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching public transport route:', error);
      throw error;
    }
  }

  /**
   * Парсит геометрию маршрута из ответа API
   * @param {Array} waypoints - Массив точек маршрута
   * @returns {Array} - Массив координат для отрисовки полилинии
   */
  parseRouteGeometry(waypoints) {
    const coordinates = [];
    
    waypoints.forEach(waypoint => {
      if (waypoint.alternatives && waypoint.alternatives.length > 0) {
        waypoint.alternatives.forEach(alternative => {
          if (alternative.geometry && alternative.geometry.length > 0) {
            alternative.geometry.forEach(geom => {
              if (geom.selection) {
                // Парсим WKT LINESTRING
                const coords = this.parseWKTLineString(geom.selection);
                coordinates.push(...coords);
              }
            });
          }
        });
      }
    });

    return coordinates;
  }

  /**
   * Парсит WKT LINESTRING в массив координат
   * @param {string} wktString - WKT строка
   * @returns {Array} - Массив координат [lon, lat]
   */
  parseWKTLineString(wktString) {
    // Убираем "LINESTRING(" и ")" и парсим координаты
    const coordsString = wktString.replace(/LINESTRING\(|\)/g, '');
    const coordPairs = coordsString.split(',');
    
    return coordPairs.map(pair => {
      const [lon, lat] = pair.trim().split(' ').map(Number);
      return [lon, lat];
    });
  }

  /**
   * Получает информацию о маршруте в удобном формате
   * @param {Object} route - Объект маршрута из API
   * @returns {Object} - Форматированная информация о маршруте
   */
  formatRouteInfo(route) {
    const totalDistance = route.total_distance || 0;
    const totalDuration = route.total_duration || 0;
    const transferCount = route.transfer_count || 0;
    const walkwayDistance = route.total_walkway_distance || '';

    return {
      id: route.id,
      distance: totalDistance,
      duration: totalDuration,
      transferCount,
      walkwayDistance,
      transport: route.transport || [],
      waypoints: route.waypoints || []
    };
  }
}

export default RoutingService;
