import {useState, useEffect} from 'react';
import {useRegisterSW} from 'virtual:pwa-register/react';
import {useFocusTrap} from '../Shared/hooks/useFocusManagement';

const PWAUpdatePrompt = () => {
  const [showPrompt, setShowPrompt] = useState(false);
  const containerRef = useFocusTrap(showPrompt);
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      console.log('SW Registered: ' + r);
    },
    onRegisterError(error) {
      console.log('SW registration error', error);
    },
  });

  useEffect(() => {
    if (needRefresh) {
      setShowPrompt(true);
    }
  }, [needRefresh]);

  const handleUpdate = () => {
    updateServiceWorker(true);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    setNeedRefresh(false);
  };

  if (!showPrompt) return null;

  return (
    <div
      ref={containerRef}
      className='fixed bottom-4 left-4 right-4 z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-4 mobile-container'
      role='dialog'
      aria-labelledby='update-title'
      aria-describedby='update-description'
      aria-modal='true'
    >
      <div className='space-y-4'>
        <div>
          <h3 id='update-title' className='mobile-subtitle text-gray-900'>
            Доступно обновление
          </h3>
          <p id='update-description' className='mobile-text text-gray-500 mt-1'>
            Новая версия приложения готова к установке
          </p>
        </div>
        <div className='flex space-x-3'>
          <button
            onClick={handleDismiss}
            className='flex-1 mobile-button bg-gray-100 text-gray-700 hover:bg-gray-200 focus-visible'
            aria-label='Отложить обновление'
          >
            Позже
          </button>
          <button
            onClick={handleUpdate}
            className='flex-1 mobile-button bg-blue-600 text-white hover:bg-blue-700 focus-visible'
            aria-label='Обновить приложение сейчас'
          >
            Обновить
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAUpdatePrompt;
