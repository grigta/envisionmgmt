# OmniSupport — План развития

## Текущий статус

**Фаза 1: Frontend UI — ЗАВЕРШЕНА**

- 87 маршрутов создано (включая Superadmin)
- Все страницы из site-list.md реализованы
- Дизайн-система применена
- Build проходит успешно
- Mock-данные для демонстрации UI

**Фаза 2: Backend API — ЗАВЕРШЕНА**

- Phase 1: Foundation (Project setup, Database schema, Auth)
- Phase 2: Core Entities (Team, Customers, Conversations)
- Phase 3: Real-time & Channels (WebSocket, Telegram, WhatsApp, Widget adapters)
- Phase 4: AI & Knowledge (Qdrant, RAG pipeline, YandexGPT/GigaChat)
- Phase 5: Scenarios & Automation (Scenario engine, Triggers, Templates)
- Phase 6: Analytics & Admin (Metrics aggregation, Reports PDF/Excel/CSV)
- Phase 7: Billing & Superadmin (Subscriptions, Usage tracking, Platform management)

**Фаза 3: Widget App — ЗАВЕРШЕНА**

- 4/4 страницы: Chat, Articles, Article, OfflineForm
- React 19 + Vite + Zustand + Tailwind CSS
- WebSocket real-time с auto-reconnect
- Prechat форма с валидацией
- SDK для встраивания на сайты (loader.js, embed.ts)
- Mock режим для тестирования без backend
- Build: 78KB gzipped

---

## Следующие шаги

### Приоритет 1: Интеграция Frontend + Backend

| # | Задача | Описание | Статус |
|---|--------|----------|--------|
| 1.1 | ~~**API клиент**~~ | Axios instance, interceptors, token refresh | ✅ Готово |
| 1.2 | ~~**Авторизация**~~ | JWT, refresh tokens, auth store, protected routes | ✅ Готово |
| 1.3 | ~~**State management**~~ | Zustand stores, React Query provider | ✅ Готово |
| 1.4 | ~~**API для страниц**~~ | Интеграция API в dashboard страницы | ✅ Готово |
| 1.5 | **Real-time чат** | WebSocket для мгновенных сообщений | ⏳ Не начато |
| 1.6 | **Загрузка файлов** | Отправка изображений/документов в чате | ⏳ Не начато |

#### Реализовано (24 января 2026):

**Инфраструктура:**
- `lib/api/client.ts` — Axios instance с interceptors и auto token refresh
- `lib/api/auth.ts` — Auth API (login, register, logout, 2FA, forgot/reset password)
- `stores/auth.ts` — Zustand auth store
- `components/providers/` — AuthProvider, QueryProvider
- `components/auth/protected-route.tsx` — Защита роутов (role, permission, superadmin)
- Обновлён `app/layout.tsx` — подключены провайдеры
- Обновлён `app/(auth)/login/page.tsx` — интеграция с auth store

**API модули:**
- `lib/api/conversations.ts` — Диалоги, сообщения, назначение, резолв
- `lib/api/customers.ts` — Клиенты, заметки, теги, объединение
- `lib/api/team.ts` — Команда, отделы, роли, навыки, приглашения
- `lib/api/analytics.ts` — Дашборд, операторы, каналы, CSAT, AI

**React Query хуки:**
- `hooks/use-conversations.ts` — useConversations, useConversation, useSendMessage
- `hooks/use-customers.ts` — useCustomers, useCustomer, useCreateCustomer
- `hooks/use-team.ts` — useTeamMembers, useDepartments, useRoles, useSkills
- `hooks/use-analytics.ts` — useAnalyticsDashboard, useOperatorAnalytics

**Интегрированные страницы (24 января 2026):**

| Страница | Хуки | Статус |
|----------|------|--------|
| `/login` | useAuthStore | ✅ |
| `/customers` | useCustomers | ✅ |
| `/customers/[id]` | useCustomer, useCustomerConversations, useCustomerNotes | ✅ |
| `/analytics` | useAnalyticsDashboard, useChannelAnalytics, useOperatorAnalytics, useAIAnalytics | ✅ |
| `/analytics/operators` | useOperatorAnalytics | ✅ |
| `/team` | useTeamMembers | ✅ |
| `/team/[userId]` | useTeamMember, useDepartments, useRoles, useSkills, useUpdateTeamMember | ✅ |
| `/team/departments` | useDepartments | ✅ |
| `/team/roles` | useRoles | ✅ |
| `/team/skills` | useSkills | ✅ |
| `/inbox` (ConversationsPanel) | useConversations | ✅ |
| `/inbox/[id]` (ChatView) | useConversation, useConversationMessages, useSendMessage | ✅ |

**Примечание:** Все страницы имеют fallback на mock-данные при недоступности API

### Приоритет 2: Отдельные приложения

| # | Задача | Описание | Страницы |
|---|--------|----------|----------|
| 2.1 | ~~**Widget App**~~ | ✅ Завершено | 4/4 страниц |
| 2.2 | ~~**Superadmin UI**~~ | ✅ Завершено | 5/5 страниц |

### Приоритет 3: Качество кода

| # | Задача | Описание | Технологии |
|---|--------|----------|------------|
| 3.1 | **Unit-тесты** | Тестирование компонентов, API endpoints | Vitest, pytest |
| 3.2 | **E2E-тесты** | Сквозные тесты критических флоу | Playwright |
| 3.3 | **Формы и валидация** | Типизированные формы с валидацией | react-hook-form, Zod |
| 3.4 | **Error boundaries** | Глобальная обработка ошибок | React Error Boundary |
| 3.5 | **Loading states** | Скелетоны и спиннеры | Suspense, кастомные компоненты |

### Приоритет 4: UX и полировка

| # | Задача | Описание | Технологии |
|---|--------|----------|------------|
| 4.1 | **Mobile responsive** | Проверка и доработка всех страниц на мобильных | Tailwind responsive |
| 4.2 | **Dark mode** | Переключатель светлой/тёмной темы | CSS variables, next-themes |
| 4.3 | **Accessibility** | ARIA-атрибуты, keyboard navigation | axe-core, eslint-plugin-jsx-a11y |
| 4.4 | **Анимации** | Плавные переходы и микроанимации | Framer Motion |
| 4.5 | **i18n** | Мультиязычность (RU/EN) | next-intl |
| 4.6 | **SEO** | Meta-теги, Open Graph, sitemap | next-seo |

---

## Структура проекта

```
omnisupport/
├── frontend/              # Next.js приложение (87 роутов)
│   ├── app/
│   │   ├── (auth)/        # Авторизация
│   │   ├── (marketing)/   # Публичные страницы
│   │   ├── (dashboard)/   # Панель оператора/админа
│   │   └── onboarding/    # Онбординг
│   └── components/ui/     # UI-компоненты
│
├── backend/               # FastAPI бэкенд (✅ готов)
│   ├── alembic/           # Миграции БД
│   ├── shared/            # Модели, схемы, auth
│   ├── services/
│   │   ├── core/          # REST API endpoints
│   │   ├── channel/       # Telegram, WhatsApp, Widget
│   │   ├── ai/            # RAG, LLM интеграции
│   │   ├── admin/         # Аналитика, отчёты, биллинг
│   │   └── superadmin/    # Управление платформой
│   └── workers/           # Фоновые задачи
│
├── widget/                # ✅ Встраиваемый виджет (React 19 + Vite)
│
├── design-system/         # Дизайн-токены
│   └── MASTER.md
│
├── site-list.md           # Карта всех 103 страниц
└── plan.md                # Этот файл
```

---

## Метрики готовности

| Компонент | Статус | Прогресс |
|-----------|--------|----------|
| Frontend UI | ✅ Готово | 98 page.tsx (87 роутов) |
| Backend API | ✅ Готово | 7/7 фаз |
| Widget App | ✅ Готово | 4/4 страниц |
| Superadmin UI | ✅ Готово | 5/5 страниц |
| API интеграция | ✅ Готово | Инфраструктура + 12 страниц |
| Real-time (WebSocket) | ⏳ Не начато | — |
| Тесты | ⏳ Не начато | — |

---

## Backend API Структура

### Модели БД (shared/models/)
- `Tenant` — SaaS-клиенты
- `User`, `Role`, `Permission` — пользователи и роли
- `Department`, `Skill` — отделы и навыки
- `Customer`, `CustomerIdentity` — клиенты
- `Conversation`, `Message` — диалоги
- `Channel`, `WidgetSettings` — каналы
- `Scenario`, `Trigger`, `ScenarioVariable` — автоматизация
- `KnowledgeDocument`, `KnowledgeChunk` — база знаний
- `AnalyticsSnapshot`, `Report` — аналитика
- `Plan`, `Subscription`, `Invoice`, `UsageRecord`, `PaymentMethod` — биллинг
- `AIInteraction` — трекинг AI

### API Endpoints
- `/api/v1/auth` — авторизация, 2FA
- `/api/v1/team` — команда, отделы, роли
- `/api/v1/conversations` — диалоги, сообщения
- `/api/v1/customers` — клиенты
- `/api/v1/channels` — каналы
- `/api/v1/ai` — AI suggestions, summarize
- `/api/v1/knowledge` — база знаний, краулер
- `/api/v1/scenarios` — сценарии, триггеры
- `/api/v1/analytics` — метрики, отчёты
- `/api/v1/billing` — подписки, счета
- `/admin/v1` — superadmin API

---

## Заметки

- API клиент и авторизация настроены (axios, zustand, react-query)
- Login страница интегрирована с backend API
- Backend полностью готов, включая миграции
- Widget App готов, включая SDK для встраивания
- Дизайн-система в `design-system/omnisupport/MASTER.md`
- CSS-переменные определены в `frontend/app/globals.css`
- **24.01.2026:** Завершена интеграция API в ключевые страницы dashboard (customers, analytics, team, inbox)
- Все интегрированные страницы имеют fallback на mock-данные при недоступности backend
- TypeScript типы синхронизированы между mock-данными и API-типами

---

*Обновлено: 24 января 2026*
