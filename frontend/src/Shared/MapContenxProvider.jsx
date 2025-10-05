import React from 'react';

const MapContext = React.createContext([undefined, () => {}]);
const MapProvider = (props) => {
  const [mapInstance, setMapInstance] = React.useState();

  return <MapContext.Provider value={[mapInstance, setMapInstance]}>{props.children}</MapContext.Provider>;
};

export {MapContext};
export default MapProvider;
