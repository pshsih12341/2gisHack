import {create} from 'zustand';

export const useStore = create((set) => {
  return {
    user: {
      name: 'John Doe',
    },
    setUser: (user) => set({user}),
    geolocationPermission: null, // null, 'granted', 'denied'
    setGeolocationPermission: (permission) => set({geolocationPermission: permission}),
    responsePoints: null, // Точки маршрута из ответа API
    setResponsePoints: (points) => set({responsePoints: points}),
    firstRoutePoint: null, // Первая точка маршрута для центрирования карты
    setFirstRoutePoint: (point) => set({firstRoutePoint: point}),
    firstPoint: null, // Первая точка, выбранная кликом на карте
    setFirstPoint: (point) => set({firstPoint: point}),
    chatMessages: [], // Сообщения чата
    addChatMessage: (message) => set((state) => ({ 
      chatMessages: [...state.chatMessages, message] 
    })),
    clearChatMessages: () => set({ chatMessages: [] }),
    secondPoint: null,
    setSecondPoint: (point) => set({secondPoint: point}),
    resultPoints: null, // Точки маршрута для инвалидных колясок
    setResultPoints: (points) => set({resultPoints: points}),
  };
});