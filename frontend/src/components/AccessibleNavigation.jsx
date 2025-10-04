import React, {useState, useRef, useEffect} from 'react';
import {Link, useLocation} from 'react-router-dom';
import {Button} from './ui/button';

const AccessibleNavigation = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const menuRef = useRef(null);
  const location = useLocation();

  const menuItems = [{path: '/', label: 'Главная', description: 'Перейти на главную страницу'}];

  // Закрытие меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
        setFocusedIndex(-1);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  // Управление фокусом с клавиатуры
  const handleKeyDown = (event) => {
    switch (event.key) {
      case 'Escape':
        setIsMenuOpen(false);
        setFocusedIndex(-1);
        break;
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex((prev) => (prev < menuItems.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : menuItems.length - 1));
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (focusedIndex >= 0) {
          const item = menuItems[focusedIndex];
          window.location.href = item.path;
          setIsMenuOpen(false);
          setFocusedIndex(-1);
        }
        break;
    }
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
    setFocusedIndex(-1);
  };

  return (
    <nav ref={menuRef} className='relative' role='navigation' aria-label='Основная навигация'>
      <Button
        onClick={toggleMenu}
        onKeyDown={handleKeyDown}
        aria-expanded={isMenuOpen}
        aria-haspopup='true'
        aria-controls='navigation-menu'
        className='focus-visible h-10 w-10 p-0'
        aria-label={isMenuOpen ? 'Закрыть меню навигации' : 'Открыть меню навигации'}
      >
        <span className='text-lg' aria-hidden='true'>
          {isMenuOpen ? '✕' : '☰'}
        </span>
        <span className='sr-only'>{isMenuOpen ? 'Закрыть меню' : 'Открыть меню'}</span>
      </Button>

      {isMenuOpen && (
        <ul
          id='navigation-menu'
          role='menu'
          className='absolute top-full right-0 mt-2 bg-white border border-gray-300 rounded-lg shadow-lg py-2 w-48 z-50'
          onKeyDown={handleKeyDown}
        >
          {menuItems.map((item, index) => (
            <li key={item.path} role='none'>
              <Link
                to={item.path}
                role='menuitem'
                tabIndex={focusedIndex === index ? 0 : -1}
                className={`block px-4 py-3 text-base hover:bg-gray-100 focus-visible ${
                  location.pathname === item.path ? 'bg-blue-100 text-blue-700' : 'text-gray-700'
                }`}
                aria-current={location.pathname === item.path ? 'page' : undefined}
                aria-describedby={`nav-desc-${index}`}
                onFocus={() => setFocusedIndex(index)}
              >
                {item.label}
              </Link>
              <div id={`nav-desc-${index}`} className='sr-only'>
                {item.description}
              </div>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
};

export default AccessibleNavigation;
