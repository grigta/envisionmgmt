# attention.dev

Лендинг веб-студии полного цикла.

## Технологии

- **HTML5** - семантическая разметка
- **CSS3** - кастомные переменные, Grid, Flexbox, анимации
- **JavaScript** - Intersection Observer API, без фреймворков

## Структура

```
attention.dev/
├── index.html      # Главная страница
├── styles.css      # Все стили
├── scripts.js      # JavaScript логика
└── CLAUDE.md       # Документация
```

## Секции

1. **Hero** - главный экран с CTA кнопками
2. **Stats** - статистика компании
3. **About** - о компании
4. **Services** - услуги с ценами
5. **Process** - как мы работаем (4 шага)
6. **Projects** - портфолио
7. **CTA** - призыв к действию
8. **FAQ** - аккордеон с вопросами
9. **Contact** - форма обратной связи
10. **Footer** - контакты и навигация

## Особенности

- Floating navbar с blur эффектом
- Scroll-анимации (Intersection Observer)
- Анимированные счётчики
- FAQ аккордеон
- Адаптивный дизайн (mobile-first)
- Поддержка `prefers-reduced-motion`
- Кастомные CSS-переменные для темизации

## Запуск

Просто открыть `index.html` в браузере или использовать локальный сервер:

```bash
# Python
python -m http.server 8000

# Node.js
npx serve .
```

## Дизайн-система

- **Шрифт**: Inter (Google Fonts)
- **Основной цвет**: #0F172A (slate-900)
- **Акцент**: #3B82F6 (blue-500)
- **Градиент**: linear-gradient(135deg, #3B82F6, #8B5CF6)
