# OmniSupport + Vanilla HTML

Интеграция виджета без фреймворков — просто HTML и JavaScript.

---

## Быстрый старт

Добавьте этот код перед `</body>`:

```html
<script>
  (function(o,m,n,i,s,u,p,t){
    o.omni=o.omni||function(){(o.omni.q=o.omni.q||[]).push({method:arguments[0],args:[].slice.call(arguments,1)})};
    s=m.createElement(n);s.async=1;s.src=i;
    u=m.getElementsByTagName(n)[0];u.parentNode.insertBefore(s,u);
  })(window,document,'script','https://widget.omnisupport.ru/loader.js');
  
  omni('init', 'pk_live_your_api_key');
</script>
```

**Готово!** Кнопка чата появится в правом нижнем углу.

---

## Настройка

### Параметры инициализации

```html
<script>
  omni('init', 'pk_live_your_api_key', {
    // Тема: 'light', 'dark', 'auto'
    theme: 'auto',
    
    // Позиция: 'bottom-right', 'bottom-left'
    position: 'bottom-right',
    
    // Основной цвет бренда
    primaryColor: '#6366f1',
    
    // Приветственное сообщение
    greeting: 'Привет! Чем могу помочь?',
    
    // Placeholder в поле ввода
    placeholder: 'Напишите сообщение...',
    
    // Автоматически открывать через N секунд (0 = не открывать)
    autoOpen: 0,
    
    // Скрыть кнопку запуска (для кастомной кнопки)
    launcherHidden: false,
    
    // Z-index виджета
    zIndex: 999999
  });
</script>
```

---

## Команды

### Управление виджетом

```javascript
// Открыть чат
omni('open');

// Закрыть чат
omni('close');

// Переключить (открыть/закрыть)
omni('toggle');
```

### Идентификация пользователя

Если пользователь авторизован на вашем сайте:

```javascript
omni('identify', {
  userId: 'user_123',        // Ваш внутренний ID
  email: 'user@example.com', // Email
  name: 'Иван Иванов',       // Имя
  phone: '+79001234567',     // Телефон (опционально)
  metadata: {                // Любые доп. данные
    plan: 'premium',
    company: 'ООО Рога и Копыта',
    signupDate: '2024-01-15'
  }
});
```

### События

```javascript
// Обработка событий
omni('on', 'open', function() {
  console.log('Чат открыт');
  // Можно отправить аналитику
  gtag('event', 'chat_opened');
});

omni('on', 'close', function() {
  console.log('Чат закрыт');
});

omni('on', 'message', function(message) {
  console.log('Новое сообщение:', message);
});

omni('on', 'unread', function(count) {
  console.log('Непрочитанных:', count);
  // Обновить свой бейдж
  document.getElementById('my-badge').textContent = count;
});
```

---

## Примеры

### Кнопка "Задать вопрос"

```html
<button onclick="omni('open')">
  💬 Задать вопрос
</button>
```

### Автоматическое открытие для новых посетителей

```html
<script>
  omni('init', 'pk_live_...', {
    autoOpen: 10 // Открыть через 10 секунд
  });
</script>
```

### Идентификация после входа

```html
<!-- После успешного входа -->
<script>
  const user = JSON.parse(localStorage.getItem('user'));
  
  if (user) {
    omni('identify', {
      userId: user.id,
      email: user.email,
      name: user.name
    });
  }
</script>
```

### Кастомная кнопка с счётчиком

```html
<style>
  .my-chat-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #6366f1;
    color: white;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    cursor: pointer;
    font-size: 24px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: transform 0.2s;
  }
  
  .my-chat-btn:hover {
    transform: scale(1.1);
  }
  
  .my-chat-btn .badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .my-chat-btn .badge:empty {
    display: none;
  }
</style>

<button class="my-chat-btn" onclick="omni('toggle')">
  💬
  <span class="badge" id="unread-badge"></span>
</button>

<script>
  omni('init', 'pk_live_...', {
    launcherHidden: true // Скрыть стандартную кнопку
  });
  
  omni('on', 'unread', function(count) {
    document.getElementById('unread-badge').textContent = count > 0 ? count : '';
  });
</script>
```

### Открытие по хэшу URL

```html
<script>
  // Если URL содержит #support — открыть чат
  if (window.location.hash === '#support') {
    omni('open');
  }
</script>

<!-- Ссылка на страницу с поддержкой -->
<a href="#support" onclick="omni('open'); return false;">Нужна помощь?</a>
```

### Разные цвета на разных страницах

```html
<script>
  const pageColors = {
    '/': '#6366f1',
    '/pricing': '#10b981',
    '/enterprise': '#1e293b'
  };
  
  const color = pageColors[window.location.pathname] || '#6366f1';
  
  omni('init', 'pk_live_...', {
    primaryColor: color
  });
</script>
```

---

## WordPress

```php
<!-- В файле footer.php темы или через плагин -->
<script>
  (function(o,m,n,i,s,u,p,t){
    o.omni=o.omni||function(){(o.omni.q=o.omni.q||[]).push({method:arguments[0],args:[].slice.call(arguments,1)})};
    s=m.createElement(n);s.async=1;s.src=i;
    u=m.getElementsByTagName(n)[0];u.parentNode.insertBefore(s,u);
  })(window,document,'script','https://widget.omnisupport.ru/loader.js');
  
  omni('init', '<?php echo get_option("omnisupport_api_key"); ?>');
  
  <?php if (is_user_logged_in()): ?>
    <?php $user = wp_get_current_user(); ?>
    omni('identify', {
      userId: '<?php echo $user->ID; ?>',
      email: '<?php echo $user->user_email; ?>',
      name: '<?php echo $user->display_name; ?>'
    });
  <?php endif; ?>
</script>
```

---

## Shopify

```liquid
<!-- В theme.liquid перед </body> -->
<script>
  (function(o,m,n,i,s,u,p,t){
    o.omni=o.omni||function(){(o.omni.q=o.omni.q||[]).push({method:arguments[0],args:[].slice.call(arguments,1)})};
    s=m.createElement(n);s.async=1;s.src=i;
    u=m.getElementsByTagName(n)[0];u.parentNode.insertBefore(s,u);
  })(window,document,'script','https://widget.omnisupport.ru/loader.js');
  
  omni('init', '{{ settings.omnisupport_key }}');
  
  {% if customer %}
    omni('identify', {
      userId: '{{ customer.id }}',
      email: '{{ customer.email }}',
      name: '{{ customer.name }}'
    });
  {% endif %}
</script>
```

---

## Отладка

### Консоль браузера

```javascript
// Проверить статус
console.log(window.OmniSupportWidget);

// Вручную открыть
window.OmniSupportWidget.open();

// Получить состояние
window.OmniSupportWidget.getState();
```

### Режим отладки

```html
<script>
  omni('init', 'pk_live_...', {
    debug: true // Логирование в консоль
  });
</script>
```

---

## FAQ

### Виджет не появляется

1. Проверьте API ключ
2. Откройте консоль браузера (F12) — там будут ошибки
3. Убедитесь, что скрипт загружается (вкладка Network)

### Конфликт стилей

```css
/* Изолировать виджет */
#omnisupport-widget {
  all: initial;
}
```

### Content Security Policy (CSP)

Добавьте в заголовки:
```
script-src 'self' https://widget.omnisupport.ru;
style-src 'self' https://widget.omnisupport.ru 'unsafe-inline';
frame-src https://widget.omnisupport.ru;
connect-src https://api.omnisupport.ru wss://api.omnisupport.ru;
```

---

## Ресурсы

- [Полная документация](https://docs.omnisupport.attention.dev)
- [API Reference](../API.md)
- [Поддержка](mailto:support@attention.dev)
