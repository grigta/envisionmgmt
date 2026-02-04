# OmniSupport + Vue 3

Интеграция чат-виджета в Vue.js приложение.

---

## Установка

```bash
npm install @omnisupport/vue
# или
yarn add @omnisupport/vue
```

---

## Быстрый старт

```javascript
// main.js
import { createApp } from 'vue';
import { OmniSupportPlugin } from '@omnisupport/vue';
import App from './App.vue';

const app = createApp(App);

app.use(OmniSupportPlugin, {
  apiKey: 'pk_live_your_api_key'
});

app.mount('#app');
```

```vue
<!-- App.vue -->
<template>
  <div id="app">
    <router-view />
    <OmniSupportWidget />
  </div>
</template>

<script setup>
import { OmniSupportWidget } from '@omnisupport/vue';
</script>
```

---

## Компоненты

### OmniSupportWidget

```vue
<template>
  <OmniSupportWidget
    :theme="darkMode ? 'dark' : 'light'"
    position="bottom-right"
    greeting="Привет! Чем помочь?"
    @open="onChatOpen"
    @close="onChatClose"
    @message="onNewMessage"
  />
</template>

<script setup>
import { ref } from 'vue';
import { OmniSupportWidget } from '@omnisupport/vue';

const darkMode = ref(false);

const onChatOpen = () => {
  console.log('Чат открыт');
};

const onChatClose = () => {
  console.log('Чат закрыт');
};

const onNewMessage = (message) => {
  console.log('Новое сообщение:', message);
};
</script>
```

**Props:**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| theme | string | 'auto' | 'light' / 'dark' / 'auto' |
| position | string | 'bottom-right' | Позиция виджета |
| greeting | string | - | Приветственное сообщение |
| primaryColor | string | '#6366f1' | Основной цвет |
| launcherHidden | boolean | false | Скрыть кнопку |

**Events:**

| Event | Payload | Description |
|-------|---------|-------------|
| open | - | Чат открыт |
| close | - | Чат закрыт |
| message | Message | Новое сообщение |

---

## Composables

### useOmniSupport

```vue
<template>
  <button @click="toggle">
    Поддержка
    <span v-if="unreadCount" class="badge">{{ unreadCount }}</span>
  </button>
</template>

<script setup>
import { useOmniSupport } from '@omnisupport/vue';

const { open, close, toggle, isOpen, unreadCount } = useOmniSupport();
</script>
```

**Возвращает:**

| Property | Type | Description |
|----------|------|-------------|
| open | () => void | Открыть чат |
| close | () => void | Закрыть чат |
| toggle | () => void | Переключить |
| isOpen | Ref<boolean> | Открыт ли чат |
| unreadCount | Ref<number> | Непрочитанные |
| identify | (user) => void | Идентификация |

### useIdentify

Идентификация пользователя при авторизации.

```vue
<script setup>
import { watch } from 'vue';
import { useIdentify } from '@omnisupport/vue';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const identify = useIdentify();

watch(
  () => auth.user,
  (user) => {
    if (user) {
      identify({
        userId: user.id,
        email: user.email,
        name: user.name,
        metadata: {
          plan: user.subscription
        }
      });
    }
  },
  { immediate: true }
);
</script>
```

---

## Полный пример

```vue
<!-- App.vue -->
<template>
  <div id="app">
    <header>
      <nav>...</nav>
      <SupportButton />
    </header>
    
    <main>
      <router-view />
    </main>
    
    <OmniSupportWidget 
      :theme="theme"
      launcher-hidden
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { OmniSupportWidget } from '@omnisupport/vue';
import { useThemeStore } from '@/stores/theme';
import SupportButton from '@/components/SupportButton.vue';

const themeStore = useThemeStore();
const theme = computed(() => themeStore.isDark ? 'dark' : 'light');
</script>
```

```vue
<!-- components/SupportButton.vue -->
<template>
  <button 
    @click="toggle"
    class="support-btn"
    :class="{ 'has-unread': unreadCount > 0 }"
  >
    <ChatIcon />
    <span v-if="unreadCount" class="badge">{{ unreadCount }}</span>
  </button>
</template>

<script setup>
import { useOmniSupport } from '@omnisupport/vue';
import ChatIcon from '@/icons/ChatIcon.vue';

const { toggle, unreadCount } = useOmniSupport();
</script>

<style scoped>
.support-btn {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  background: #6366f1;
  color: white;
  border-radius: 9999px;
  padding: 1rem;
  transition: transform 0.2s;
}

.support-btn:hover {
  transform: scale(1.1);
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  border-radius: 9999px;
  padding: 2px 6px;
  font-size: 12px;
}
</style>
```

---

## Nuxt 3

```javascript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@omnisupport/nuxt'],
  
  omniSupport: {
    apiKey: process.env.OMNISUPPORT_API_KEY
  }
});
```

```vue
<!-- app.vue -->
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  
  <!-- Виджет добавляется автоматически -->
</template>
```

```vue
<!-- pages/index.vue -->
<script setup>
// Composable доступен глобально
const { open, identify } = useOmniSupport();

// Идентификация
const { data: user } = await useFetch('/api/user');

if (user.value) {
  identify({
    userId: user.value.id,
    email: user.value.email
  });
}
</script>
```

---

## Pinia Store

Интеграция с Pinia для централизованного управления.

```javascript
// stores/support.js
import { defineStore } from 'pinia';
import { useOmniSupport } from '@omnisupport/vue';

export const useSupportStore = defineStore('support', () => {
  const omni = useOmniSupport();
  
  const showHelp = () => {
    omni.open();
  };
  
  const hideHelp = () => {
    omni.close();
  };
  
  return {
    ...omni,
    showHelp,
    hideHelp
  };
});
```

---

## TypeScript

```vue
<script setup lang="ts">
import { 
  OmniSupportWidget, 
  useOmniSupport,
  type OmniUser,
  type OmniMessage 
} from '@omnisupport/vue';

const { identify, unreadCount } = useOmniSupport();

const user: OmniUser = {
  userId: '123',
  email: 'user@example.com',
  name: 'Иван'
};

identify(user);

const handleMessage = (msg: OmniMessage) => {
  console.log(msg.content);
};
</script>
```

---

## Ресурсы

- [Полная документация](https://docs.omnisupport.attention.dev/vue)
- [GitHub репозиторий](https://github.com/omnisupport/sdk-vue)
- [Пример на StackBlitz](https://stackblitz.com/edit/omnisupport-vue)
