# 🚀 OmniSupport Quick Start

**Время**: ~5 минут  
**Результат**: Рабочий AI-чат на вашем сайте

---

## Шаг 1: Получите API ключ

1. Зарегистрируйтесь на [omnisupport.attention.dev](https://omnisupport.attention.dev)
2. Создайте новый проект
3. Скопируйте API ключ из настроек проекта

> 💡 **Free tier**: 100 сообщений/месяц бесплатно

---

## Шаг 2: Добавьте виджет на сайт

Вставьте этот код перед закрывающим тегом `</body>`:

```html
<!-- OmniSupport Widget -->
<script>
  (function(o,m,n,i,s,u,p,t){
    o.omni=o.omni||function(){(o.omni.q=o.omni.q||[]).push({method:arguments[0],args:[].slice.call(arguments,1)})};
    s=m.createElement(n);s.async=1;s.src=i;
    u=m.getElementsByTagName(n)[0];u.parentNode.insertBefore(s,u);
  })(window,document,'script','https://widget.omnisupport.ru/loader.js');
  
  omni('init', 'YOUR_API_KEY');
</script>
```

**Замените** `YOUR_API_KEY` на ваш ключ из Шага 1.

---

## Шаг 3: Готово! 🎉

Обновите страницу — в правом нижнем углу появится кнопка чата.

---

## Настройка (опционально)

### Тема оформления

```javascript
omni('init', 'YOUR_API_KEY', {
  theme: 'dark',        // 'light' | 'dark' | 'auto'
  position: 'bottom-right',  // 'bottom-right' | 'bottom-left'
  primaryColor: '#6366f1',   // Ваш бренд-цвет
  greeting: 'Привет! Чем могу помочь?'
});
```

### Идентификация пользователя

Если пользователь авторизован на вашем сайте:

```javascript
omni('identify', {
  userId: 'user_123',
  email: 'user@example.com',
  name: 'Иван Иванов'
});
```

### Программное управление

```javascript
omni('open');   // Открыть чат
omni('close');  // Закрыть чат
omni('toggle'); // Переключить
```

---

## Настройка AI

В панели управления вы можете:

1. **Выбрать модель AI**:
   - Claude 3.5 Sonnet (рекомендуется)
   - GPT-4o
   - YandexGPT
   - GigaChat

2. **Загрузить базу знаний**:
   - FAQ документы
   - Информация о продуктах
   - Политики и правила

3. **Настроить поведение**:
   - Тон общения (формальный/дружелюбный)
   - Язык ответов
   - Эскалация на человека

---

## Интеграция с фреймворками

### React

```jsx
import { useEffect } from 'react';

export function OmniSupportWidget({ apiKey }) {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://widget.omnisupport.ru/loader.js';
    script.async = true;
    script.onload = () => {
      window.omni('init', apiKey);
    };
    document.body.appendChild(script);
    
    return () => {
      document.body.removeChild(script);
    };
  }, [apiKey]);
  
  return null;
}
```

### Vue 3

```vue
<script setup>
import { onMounted, onUnmounted } from 'vue';

const props = defineProps(['apiKey']);

onMounted(() => {
  const script = document.createElement('script');
  script.src = 'https://widget.omnisupport.ru/loader.js';
  script.async = true;
  script.onload = () => window.omni('init', props.apiKey);
  document.body.appendChild(script);
});
</script>

<template>
  <!-- Widget renders automatically -->
</template>
```

### Next.js

```jsx
// components/OmniSupport.js
'use client';
import Script from 'next/script';

export function OmniSupport({ apiKey }) {
  return (
    <Script
      src="https://widget.omnisupport.ru/loader.js"
      strategy="lazyOnload"
      onLoad={() => window.omni('init', apiKey)}
    />
  );
}
```

---

## Проверка работоспособности

После установки убедитесь, что:

- [ ] Кнопка чата видна на странице
- [ ] Чат открывается по клику
- [ ] AI отвечает на тестовое сообщение
- [ ] На мобильных устройствах всё работает

---

## Проблемы?

| Проблема | Решение |
|----------|---------|
| Кнопка не появляется | Проверьте API ключ и консоль браузера |
| AI не отвечает | Проверьте баланс и лимиты в панели |
| Конфликт стилей | Добавьте `!important` или изолируйте виджет |

📧 Поддержка: support@attention.dev

---

*Следующий шаг: [API Documentation](./API.md)*
