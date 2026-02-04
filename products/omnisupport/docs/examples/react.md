# OmniSupport + React

Интеграция чат-виджета в React-приложение.

---

## Установка

### Вариант 1: npm пакет (рекомендуется)

```bash
npm install @omnisupport/react
# или
yarn add @omnisupport/react
```

### Вариант 2: Script tag

Загрузка через CDN (см. [vanilla HTML](./html.md)).

---

## Быстрый старт

```jsx
// App.jsx
import { OmniSupportProvider, ChatWidget } from '@omnisupport/react';

function App() {
  return (
    <OmniSupportProvider apiKey="pk_live_your_api_key">
      <YourApp />
      <ChatWidget />
    </OmniSupportProvider>
  );
}
```

---

## Компоненты

### OmniSupportProvider

Провайдер контекста. Оберните им корневой компонент.

```jsx
import { OmniSupportProvider } from '@omnisupport/react';

<OmniSupportProvider
  apiKey="pk_live_..."
  options={{
    theme: 'dark',
    position: 'bottom-right',
    primaryColor: '#6366f1',
    greeting: 'Привет! Чем помочь?'
  }}
>
  {children}
</OmniSupportProvider>
```

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| apiKey | string | ✅ | Ваш публичный API ключ |
| options | object | ❌ | Настройки виджета |
| user | object | ❌ | Данные пользователя |

### ChatWidget

Сам виджет. Добавьте в любом месте дерева (внутри Provider).

```jsx
import { ChatWidget } from '@omnisupport/react';

<ChatWidget 
  onOpen={() => console.log('Чат открыт')}
  onClose={() => console.log('Чат закрыт')}
  onMessage={(msg) => console.log('Новое сообщение:', msg)}
/>
```

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| onOpen | function | Колбэк при открытии |
| onClose | function | Колбэк при закрытии |
| onMessage | function | Колбэк при новом сообщении |
| className | string | Дополнительные CSS классы |

---

## Хуки

### useOmniSupport

Доступ к методам виджета.

```jsx
import { useOmniSupport } from '@omnisupport/react';

function SupportButton() {
  const { open, close, toggle, isOpen, unreadCount } = useOmniSupport();

  return (
    <button onClick={toggle}>
      Поддержка {unreadCount > 0 && `(${unreadCount})`}
    </button>
  );
}
```

**Возвращает:**

| Property | Type | Description |
|----------|------|-------------|
| open | function | Открыть чат |
| close | function | Закрыть чат |
| toggle | function | Переключить |
| isOpen | boolean | Открыт ли чат |
| unreadCount | number | Непрочитанные сообщения |
| identify | function | Идентифицировать пользователя |

### useIdentify

Идентификация авторизованного пользователя.

```jsx
import { useIdentify } from '@omnisupport/react';

function Profile({ user }) {
  const identify = useIdentify();

  useEffect(() => {
    if (user) {
      identify({
        userId: user.id,
        email: user.email,
        name: user.name,
        metadata: {
          plan: user.subscription,
          signupDate: user.createdAt
        }
      });
    }
  }, [user]);

  return <div>...</div>;
}
```

---

## Полный пример

```jsx
// src/App.jsx
import { OmniSupportProvider, ChatWidget, useOmniSupport } from '@omnisupport/react';
import { useAuth } from './hooks/useAuth';

function ChatButton() {
  const { toggle, unreadCount } = useOmniSupport();
  
  return (
    <button 
      onClick={toggle}
      className="fixed bottom-4 right-4 bg-indigo-600 text-white rounded-full p-4"
    >
      💬 {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
    </button>
  );
}

function App() {
  const { user } = useAuth();

  return (
    <OmniSupportProvider 
      apiKey={process.env.REACT_APP_OMNISUPPORT_KEY}
      user={user ? {
        userId: user.id,
        email: user.email,
        name: user.displayName
      } : undefined}
      options={{
        theme: 'auto',
        greeting: 'Привет! Как дела?'
      }}
    >
      <Router>
        <Routes>
          {/* ваши маршруты */}
        </Routes>
      </Router>
      
      <ChatWidget />
      {/* или кастомная кнопка: <ChatButton /> */}
    </OmniSupportProvider>
  );
}

export default App;
```

---

## Кастомизация

### Переопределение стилей

```jsx
<ChatWidget 
  className="my-custom-widget"
  style={{ '--omni-primary': '#10b981' }}
/>
```

```css
/* styles.css */
.my-custom-widget {
  --omni-primary: #10b981;
  --omni-radius: 16px;
}

/* Скрыть дефолтную кнопку */
.omni-launcher {
  display: none;
}
```

### Кастомная кнопка запуска

```jsx
function App() {
  const { open, unreadCount } = useOmniSupport();

  return (
    <>
      {/* Скрываем дефолтную кнопку */}
      <ChatWidget launcherHidden />
      
      {/* Своя кнопка */}
      <button onClick={open} className="my-support-btn">
        Нужна помощь? {unreadCount > 0 && `(${unreadCount})`}
      </button>
    </>
  );
}
```

---

## TypeScript

```tsx
import { 
  OmniSupportProvider, 
  ChatWidget, 
  useOmniSupport,
  OmniUser,
  OmniOptions 
} from '@omnisupport/react';

const options: OmniOptions = {
  theme: 'dark',
  position: 'bottom-left'
};

const user: OmniUser = {
  userId: '123',
  email: 'user@example.com'
};

function App() {
  return (
    <OmniSupportProvider apiKey="pk_live_..." options={options} user={user}>
      <ChatWidget />
    </OmniSupportProvider>
  );
}
```

---

## Ресурсы

- [Полная документация](https://docs.omnisupport.attention.dev/react)
- [GitHub репозиторий](https://github.com/omnisupport/sdk-react)
- [Примеры на CodeSandbox](https://codesandbox.io/s/omnisupport-react)
