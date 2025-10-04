import {useEffect, useRef} from 'react';

/**
 * Хук для управления фокусом в модальных окнах и других компонентах
 * @param {boolean} isOpen - открыт ли компонент
 * @param {string} focusSelector - селектор элемента для фокуса
 */
export const useFocusManagement = (isOpen, focusSelector = 'button, input, select, textarea, [tabindex]:not([tabindex="-1"])') => {
  const containerRef = useRef(null);
  const previousActiveElement = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Сохраняем предыдущий активный элемент
      previousActiveElement.current = document.activeElement;
      
      // Фокусируемся на первом фокусируемом элементе
      if (containerRef.current) {
        const focusableElement = containerRef.current.querySelector(focusSelector);
        if (focusableElement) {
          focusableElement.focus();
        }
      }
    } else {
      // Возвращаем фокус на предыдущий элемент
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    }
  }, [isOpen, focusSelector]);

  return containerRef;
};

/**
 * Хук для ловушки фокуса (удерживает фокус внутри компонента)
 * @param {boolean} isActive - активна ли ловушка
 */
export const useFocusTrap = (isActive) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    const handleEscapeKey = (e) => {
      if (e.key === 'Escape') {
        // Можно добавить логику закрытия
        const event = new CustomEvent('escape-pressed');
        container.dispatchEvent(event);
      }
    };

    container.addEventListener('keydown', handleTabKey);
    container.addEventListener('keydown', handleEscapeKey);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      container.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isActive]);

  return containerRef;
};

/**
 * Хук для объявления изменений для скринридеров
 * @param {string} message - сообщение для объявления
 * @param {boolean} isVisible - видимо ли сообщение
 */
export const useScreenReaderAnnouncement = (message, isVisible) => {
  useEffect(() => {
    if (isVisible && message) {
      // Создаем временный элемент для объявления
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = message;
      
      document.body.appendChild(announcement);
      
      // Удаляем элемент после объявления
      setTimeout(() => {
        document.body.removeChild(announcement);
      }, 1000);
    }
  }, [message, isVisible]);
};
