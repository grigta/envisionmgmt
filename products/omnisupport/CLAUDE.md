# OmniSupport

Омниканальная SaaS-платформа поддержки клиентов.

## Запуск

```bash
# Frontend
cd frontend && npm run dev    # http://localhost:3000

# Backend
cd backend && docker-compose up -d
cd backend/services/core && uvicorn main:app --reload  # http://localhost:8000

# Widget
cd widget && npm run dev      # http://localhost:5173?mock=true
```

## Tech Stack

### Frontend
- Next.js 16 + App Router + Turbopack
- Tailwind CSS v4
- TypeScript (strict mode)
- Lucide React (иконки)

### Backend
- Python 3.11+ / FastAPI
- PostgreSQL (основная БД)
- Redis (кэш, очереди, pub/sub)
- Qdrant (векторная БД для RAG)
- SQLAlchemy async + Alembic
- WebSocket (real-time)

## Документация

| Документ | Описание |
|----------|----------|
| [spec.md](spec.md) | Требования к продукту |
| [architecture.md](architecture.md) | Архитектура системы |
| [site-list.md](site-list.md) | Карта 103 страниц |
| [plan.md](plan.md) | План развития |

## Дизайн-система

| Документ | Описание |
|----------|----------|
| [MASTER.md](../../design-system/omnisupport/MASTER.md) | Токены, типографика, цвета |
| [COMPONENTS.md](../../design-system/omnisupport/COMPONENTS.md) | UI-компоненты |

## Структура проекта

```
omnisupport/
├── frontend/              # Next.js приложение
│   ├── app/
│   │   ├── (auth)/        # Авторизация
│   │   ├── (marketing)/   # Публичные страницы
│   │   ├── (dashboard)/   # Панель оператора/админа
│   │   └── onboarding/    # Онбординг
│   └── components/ui/     # UI-компоненты
│
├── backend/               # FastAPI бэкенд
│   ├── alembic/           # Миграции БД
│   ├── shared/            # Общий код
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── auth/          # JWT, permissions
│   │   └── events/        # Redis pub/sub
│   ├── services/
│   │   ├── core/          # Основной API (api/v1/)
│   │   ├── channel/       # Адаптеры каналов (telegram, whatsapp, widget)
│   │   ├── ai/            # RAG + LLM
│   │   ├── admin/         # Настройки, аналитика, отчёты, биллинг
│   │   └── superadmin/    # Управление платформой
│   └── workers/           # Фоновые задачи
│
└── widget/                # Встраиваемый виджет чата
    ├── src/
    │   ├── components/    # UI, Chat, Layout, Forms
    │   ├── hooks/         # React hooks
    │   ├── stores/        # Zustand store
    │   ├── lib/           # API, WebSocket, utils
    │   └── pages/         # Chat, Articles, OfflineForm
    └── sdk/               # Loader и Embed API
```

## Backend API Endpoints

### Auth (`/api/v1/auth`)
- POST `/register`, `/login`, `/logout`, `/refresh`
- POST `/forgot-password`, `/reset-password`
- POST `/two-factor/enable`, `/verify`, `/disable`

### Team (`/api/v1/team`)
- CRUD `/members`, `/departments`, `/skills`, `/roles`
- POST `/invite`, `/invite/:token/accept`

### Conversations (`/api/v1/conversations`)
- GET `/` (filters: status, assigned_to, channel)
- GET `/:id`, `/:id/messages`
- POST `/:id/messages`, `/:id/assign`, `/:id/transfer`, `/:id/resolve`

### Customers (`/api/v1/customers`)
- CRUD `/`, `/:id`
- GET `/:id/conversations`, `/:id/notes`
- POST `/:id/merge`, `/export`

### Channels (`/api/v1/channels`)
- POST `/telegram`, `/whatsapp`, `/widget`
- PATCH `/:type/:id`, DELETE `/:type/:id`

### AI (`/api/v1/ai`)
- POST `/suggestions`, `/summarize`, `/sentiment`

### Knowledge (`/api/v1/knowledge`)
- CRUD `/documents`, `/crawlers`
- POST `/test`

### Scenarios (`/api/v1/scenarios`)
- CRUD `/`, `/triggers`, `/variables`
- POST `/:id/publish`, `/:id/test`
- GET `/templates`, `/nodes`

### Analytics (`/api/v1/analytics`)
- GET `/dashboard`, `/conversations`, `/operators`, `/channels`, `/csat`, `/ai`, `/tags`
- CRUD `/reports`, POST `/reports/:id/export`

### Billing (`/api/v1/billing`)
- GET `/plans`, `/subscription`, `/invoices`, `/usage`
- POST `/subscribe`, `/change-plan`, `/cancel`, `/activate`
- CRUD `/payment-methods`

### Superadmin (`/admin/v1`)
- CRUD `/tenants`
- GET `/stats`, `/stats/growth`
- CRUD `/plans`
- GET `/settings`, `/health`, `/logs`

## Статус

| Компонент | Статус | Прогресс |
|-----------|--------|----------|
| Frontend UI | ✅ Готово | 98 page.tsx |
| Backend API | ✅ Готово | Все 7 фаз |
| Widget App | ✅ Готово | 4/4 страниц |
| Superadmin UI | ✅ Готово | 5/5 страниц |
| API интеграция | ✅ Готово | Инфраструктура + 12 страниц |
| Real-time (WebSocket) | ⏳ Не начато | — |
| Тесты | ⏳ Не начато | — |

## Widget App

Встраиваемый виджет чата для сайтов клиентов.

```bash
cd widget && npm run dev    # http://localhost:5173?mock=true
cd widget && npm run build  # Production build
```

**Tech Stack:** React 19, Vite, Zustand, Tailwind CSS, Lucide React

**Страницы:**
- `/widget/:tenantId` — Чат с оператором (WebSocket real-time)
- `/widget/:tenantId/articles` — Список FAQ статей
- `/widget/:tenantId/articles/:id` — Просмотр статьи
- `/widget/:tenantId/form` — Офлайн-форма заявки

**SDK для встраивания:**
```html
<script>
  (function(w,d,s,o,f,js,fjs){
    w['OmniSupport']=o;w[o]=w[o]||function(){
    (w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','omni','https://widget.omnisupport.ru/loader.js'));

  omni('init', 'my-company-slug');
</script>
```
