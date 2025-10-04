import {useState, useEffect} from 'react';

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const {outcome} = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('PWA установлено');
    } else {
      console.log('PWA не установлено');
    }

    setDeferredPrompt(null);
    setShowInstallPrompt(false);
  };

  const handleDismiss = () => {
    setShowInstallPrompt(false);
  };

  if (!showInstallPrompt) return null;

  return (
    <div
      className='fixed bottom-4 left-4 right-4 z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-4 mobile-container'
      role='dialog'
      aria-labelledby='install-title'
      aria-describedby='install-description'
      aria-modal='true'
    >
      <div className='space-y-4'>
        <div>
          <h3 id='install-title' className='mobile-subtitle text-gray-900'>
            Установить приложение
          </h3>
          <p id='install-description' className='mobile-text text-gray-500 mt-1'>
            Добавьте приложение на главный экран для быстрого доступа
          </p>
        </div>
        <div className='flex space-x-3'>
          <button
            onClick={handleDismiss}
            className='flex-1 mobile-button bg-gray-100 text-gray-700 hover:bg-gray-200 focus-visible'
            aria-label='Отложить установку приложения'
          >
            Позже
          </button>
          <button
            onClick={handleInstallClick}
            className='flex-1 mobile-button bg-green-600 text-white hover:bg-green-700 focus-visible'
            aria-label='Установить приложение на устройство'
          >
            Установить
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;
