import React, {useState, useEffect} from 'react';

const BottomDrawer = ({children, isOpen, onToggle, title = 'Информация'}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [currentY, setCurrentY] = useState(0);
  const [drawerHeight, setDrawerHeight] = useState(0);

  // Вычисляем высоту попапа в зависимости от состояния
  const getDrawerHeight = () => {
    if (!isOpen) return '60px'; // Свернутое состояние
    return `${Math.max(200, Math.min(400, window.innerHeight * 0.6))}px`; // Развернутое состояние
  };

  // Обработка начала перетаскивания
  const handleTouchStart = (e) => {
    setIsDragging(true);
    setStartY(e.touches[0].clientY);
    setCurrentY(e.touches[0].clientY);
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartY(e.clientY);
    setCurrentY(e.clientY);
  };

  // Обработка перетаскивания
  const handleTouchMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    setCurrentY(e.touches[0].clientY);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    setCurrentY(e.clientY);
  };

  // Обработка окончания перетаскивания
  const handleTouchEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);

    const deltaY = currentY - startY;
    const threshold = 50; // Порог для переключения состояния

    if (Math.abs(deltaY) > threshold) {
      if (deltaY > 0 && isOpen) {
        // Перетаскивание вниз - сворачиваем
        onToggle(false);
      } else if (deltaY < 0 && !isOpen) {
        // Перетаскивание вверх - разворачиваем
        onToggle(true);
      }
    }

    setCurrentY(0);
    setStartY(0);
  };

  const handleMouseUp = () => {
    handleTouchEnd();
  };

  // Добавляем обработчики событий
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('touchmove', handleTouchMove, {passive: false});
      document.addEventListener('touchend', handleTouchEnd);
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, currentY, startY, isOpen]);

  // Вычисляем смещение для анимации
  const getTransform = () => {
    if (!isDragging) return '';
    const deltaY = currentY - startY;
    return `translateY(${deltaY}px)`;
  };

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 bg-[#222222] border-t border-gray-200 shadow-lg transition-all duration-300 ease-out z-50 ${
        isOpen ? 'rounded-t-xl' : ''
      }`}
      style={{
        height: getDrawerHeight(),
        transform: getTransform(),
      }}
    >
      {/* Заголовок с ручкой для перетаскивания */}
      <div
        className='flex items-center justify-between p-2 cursor-pointer select-none'
        onTouchStart={handleTouchStart}
        onMouseDown={handleMouseDown}
        onClick={() => onToggle(!isOpen)}
      ></div>

      {/* Содержимое попапа */}
      <div className='flex-1 overflow-y-auto h-full'>
        {isOpen && <div className='p-[15px] pt-0 h-full'>{children}</div>}
      </div>
    </div>
  );
};

export default BottomDrawer;
