import React, {useEffect, useRef} from 'react';

const AccessibleAlert = ({type = 'info', message, isVisible, onClose, autoClose = false, duration = 5000}) => {
  const alertRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (isVisible && autoClose) {
      timeoutRef.current = setTimeout(() => {
        onClose();
      }, duration);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isVisible, autoClose, duration, onClose]);

  useEffect(() => {
    if (isVisible && alertRef.current) {
      // Фокусируемся на уведомлении для скринридеров
      alertRef.current.focus();
    }
  }, [isVisible]);

  if (!isVisible) return null;

  const getAlertStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-100 border-green-500 text-green-800';
      case 'error':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'warning':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      default:
        return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  const getAriaLabel = () => {
    switch (type) {
      case 'success':
        return 'Успешное уведомление';
      case 'error':
        return 'Ошибка';
      case 'warning':
        return 'Предупреждение';
      default:
        return 'Информационное уведомление';
    }
  };

  return (
    <div
      ref={alertRef}
      role='alert'
      aria-live='assertive'
      aria-label={getAriaLabel()}
      className={`fixed top-4 left-4 right-4 z-50 p-4 border-l-4 rounded-md shadow-lg ${getAlertStyles()} focus-visible`}
      tabIndex='-1'
    >
      <div className='flex items-start'>
        <div className='flex-shrink-0 mr-3' aria-hidden='true'>
          <span className='text-lg'>{getIcon()}</span>
        </div>

        <div className='flex-1'>
          <p className='text-sm font-medium'>{message}</p>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className='flex-shrink-0 ml-3 text-lg font-bold hover:opacity-75 focus-visible'
            aria-label='Закрыть уведомление'
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default AccessibleAlert;
