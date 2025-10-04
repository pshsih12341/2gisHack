# Руководство по доступности (Accessibility)

## Обзор

Это приложение разработано с учетом принципов инклюзивности и доступности для людей с ограниченными возможностями. Мы следуем стандартам WCAG 2.1 AA и обеспечиваем полную поддержку скринридеров.

## Основные принципы доступности

### 1. Семантическая разметка

- Используем семантические HTML теги (`<main>`, `<header>`, `<nav>`, `<section>`, `<article>`)
- Правильная иерархия заголовков (h1 → h2 → h3)
- Логическая структура контента

### 2. ARIA атрибуты

- `role` - определяет роль элемента
- `aria-label` - краткое описание элемента
- `aria-labelledby` - связь с элементом-заголовком
- `aria-describedby` - связь с элементом-описанием
- `aria-live` - для динамических обновлений
- `aria-expanded` - состояние раскрытия/сворачивания

### 3. Навигация с клавиатуры

- Все интерактивные элементы доступны с клавиатуры
- Логический порядок табуляции
- Видимые индикаторы фокуса
- Управление фокусом в модальных окнах

### 4. Поддержка скринридеров

- Скрытый текст для контекста (`.sr-only`)
- Альтернативный текст для изображений
- Описания для кнопок и ссылок
- Объявления изменений (`aria-live`)

## Компоненты доступности

### AccessibleNavigation

- Полностью управляемая с клавиатуры
- Поддержка стрелок для навигации
- Escape для закрытия
- Правильные ARIA роли

### AccessibleAlert

- Автоматические объявления скринридерам
- Различные типы уведомлений
- Автоматическое закрытие
- Правильные ARIA атрибуты

### PWA компоненты

- Модальные окна с ловушкой фокуса
- Правильные роли и метки
- Управление с клавиатуры

## CSS классы для доступности

### .sr-only

Скрывает элемент визуально, но оставляет доступным для скринридеров:

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

### .focus-visible

Улучшенные стили фокуса:

```css
.focus-visible {
  @apply focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2;
}
```

### .skip-link

Ссылка для быстрого перехода к основному контенту:

```css
.skip-link {
  @apply sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md;
}
```

## Хуки для доступности

### useFocusManagement

Управление фокусом в модальных окнах:

```javascript
const containerRef = useFocusManagement(isOpen, 'button, input');
```

### useFocusTrap

Ловушка фокуса для модальных окон:

```javascript
const containerRef = useFocusTrap(isActive);
```

### useScreenReaderAnnouncement

Объявления для скринридеров:

```javascript
useScreenReaderAnnouncement(message, isVisible);
```

## Тестирование доступности

### Автоматическое тестирование

1. Запустите Lighthouse в Chrome DevTools
2. Проверьте раздел "Accessibility"
3. Убедитесь в прохождении всех тестов

### Ручное тестирование

1. **Навигация с клавиатуры:**

   - Используйте Tab для навигации
   - Проверьте логический порядок
   - Убедитесь в видимых индикаторах фокуса

2. **Тестирование скринридеров:**

   - Используйте NVDA (Windows) или VoiceOver (Mac)
   - Проверьте объявления контента
   - Убедитесь в правильной навигации

3. **Мобильная доступность:**
   - Тестируйте на реальных устройствах
   - Проверьте жесты и касания
   - Убедитесь в правильном масштабировании

## Рекомендации для разработчиков

### 1. Всегда используйте семантические теги

```jsx
// ✅ Правильно
<main role="main">
  <h1>Заголовок</h1>
  <section aria-labelledby="section-title">
    <h2 id="section-title">Подзаголовок</h2>
  </section>
</main>

// ❌ Неправильно
<div>
  <div>Заголовок</div>
  <div>Контент</div>
</div>
```

### 2. Добавляйте ARIA метки

```jsx
// ✅ Правильно
<button aria-label="Закрыть модальное окно">
  ×
</button>

// ❌ Неправильно
<button>×</button>
```

### 3. Обеспечивайте контекст для скринридеров

```jsx
// ✅ Правильно
<button aria-describedby="button-help">
  Сохранить
</button>
<p id="button-help" className="sr-only">
  Нажмите для сохранения изменений
</p>
```

### 4. Используйте правильные роли

```jsx
// ✅ Правильно
<div role='dialog' aria-modal='true' aria-labelledby='dialog-title'>
  <h2 id='dialog-title'>Заголовок диалога</h2>
</div>
```

## Соответствие стандартам

- **WCAG 2.1 AA** - основной стандарт доступности
- **Section 508** - стандарт для государственных сайтов США
- **EN 301 549** - европейский стандарт доступности

## Полезные ресурсы

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)
- [Accessibility Testing Tools](https://webaim.org/resources/tools/)

## Поддержка

Если вы обнаружили проблемы с доступностью, пожалуйста, сообщите об этом через:

- GitHub Issues
- Email: accessibility@2gishack.com
- Телефон: +7 (XXX) XXX-XX-XX
