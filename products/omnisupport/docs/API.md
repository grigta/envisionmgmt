# 📚 OmniSupport API Documentation

**Base URL**: `https://api.omnisupport.ru/api/v1`  
**Version**: 0.1.0

---

## Содержание

1. [Аутентификация](#аутентификация)
2. [Диалоги](#диалоги)
3. [Сообщения](#сообщения)
4. [AI](#ai)
5. [База знаний](#база-знаний)
6. [Клиенты](#клиенты)
7. [Команда](#команда)
8. [Каналы](#каналы)
9. [Аналитика](#аналитика)
10. [Биллинг](#биллинг)
11. [Вебхуки](#вебхуки)
12. [WebSocket](#websocket)
13. [Widget API](#widget-api)

---

## Общие принципы

### Формат ответов

Все успешные ответы возвращаются в JSON:

```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### Ошибки

```json
{
  "detail": "Описание ошибки",
  "code": "ERROR_CODE"
}
```

| HTTP Code | Описание |
|-----------|----------|
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 422 | Ошибка валидации |
| 429 | Слишком много запросов |
| 500 | Внутренняя ошибка |

### Пагинация

```
GET /endpoint?page=1&per_page=20
```

### Rate Limiting

- Free: 100 запросов/минуту
- Pro: 1000 запросов/минуту
- Enterprise: без ограничений

---

## Аутентификация

### Регистрация

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "company_name": "ООО Компания"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Вход

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Ответ:** аналогичен регистрации

### Обновление токена

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

### Выход

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

### Двухфакторная аутентификация

#### Включить 2FA

```http
POST /auth/2fa/enable
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/OmniSupport:user@example.com?...",
  "backup_codes": ["12345678", "87654321", ...]
}
```

#### Подтвердить 2FA

```http
POST /auth/2fa/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "code": "123456"
}
```

---

## Диалоги

### Список диалогов

```http
GET /conversations
Authorization: Bearer {access_token}
```

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| status | string | open, closed, pending |
| channel | string | widget, telegram, whatsapp |
| assigned_to | uuid | ID оператора |
| page | int | Страница (default: 1) |
| per_page | int | Элементов на странице (default: 20) |

**Ответ:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "customer": {
        "id": "...",
        "name": "Клиент",
        "email": "client@example.com"
      },
      "channel": "widget",
      "status": "open",
      "last_message": {
        "content": "Последнее сообщение",
        "created_at": "2026-02-03T12:00:00Z"
      },
      "assigned_to": null,
      "created_at": "2026-02-03T10:00:00Z",
      "updated_at": "2026-02-03T12:00:00Z"
    }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20
  }
}
```

### Получить диалог

```http
GET /conversations/{id}
Authorization: Bearer {access_token}
```

### Создать диалог

```http
POST /conversations
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer_id": "...",
  "channel": "widget",
  "metadata": {}
}
```

### Закрыть диалог

```http
POST /conversations/{id}/close
Authorization: Bearer {access_token}
```

### Назначить оператора

```http
POST /conversations/{id}/assign
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "user_id": "..."
}
```

---

## Сообщения

### Получить сообщения диалога

```http
GET /conversations/{conversation_id}/messages
Authorization: Bearer {access_token}
```

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| before | datetime | Сообщения до этого времени |
| limit | int | Количество (default: 50, max: 100) |

**Ответ:**
```json
{
  "data": [
    {
      "id": "...",
      "conversation_id": "...",
      "sender_type": "customer",
      "sender_id": "...",
      "content": "Текст сообщения",
      "attachments": [],
      "metadata": {},
      "created_at": "2026-02-03T12:00:00Z"
    }
  ]
}
```

### Отправить сообщение

```http
POST /conversations/{conversation_id}/messages
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "Текст сообщения",
  "attachments": []
}
```

---

## AI

### Сгенерировать ответ

```http
POST /ai/generate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "conversation_id": "...",
  "context_messages": 10
}
```

**Ответ:**
```json
{
  "response": "Сгенерированный AI ответ",
  "confidence": 0.95,
  "sources": [
    {
      "document_id": "...",
      "title": "FAQ",
      "relevance": 0.87
    }
  ]
}
```

### Настройки AI

```http
GET /ai/settings
Authorization: Bearer {access_token}
```

```http
PUT /ai/settings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet",
  "temperature": 0.7,
  "system_prompt": "Ты помощник службы поддержки...",
  "auto_respond": true,
  "confidence_threshold": 0.8
}
```

**Доступные провайдеры:**
- `anthropic` — Claude 3.5 Sonnet, Claude 4 Sonnet
- `openai` — GPT-4o, GPT-4o-mini
- `yandex` — YandexGPT
- `sber` — GigaChat

---

## База знаний

### Список документов

```http
GET /knowledge/documents
Authorization: Bearer {access_token}
```

### Загрузить документ

```http
POST /knowledge/documents
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: (binary)
title: "FAQ"
category: "general"
```

**Поддерживаемые форматы:** PDF, DOCX, TXT, MD, HTML

### Удалить документ

```http
DELETE /knowledge/documents/{id}
Authorization: Bearer {access_token}
```

### Поиск по базе знаний

```http
POST /knowledge/search
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "как вернуть товар",
  "limit": 5
}
```

**Ответ:**
```json
{
  "results": [
    {
      "document_id": "...",
      "title": "Политика возврата",
      "content": "Релевантный фрагмент...",
      "score": 0.92
    }
  ]
}
```

---

## Клиенты

### Список клиентов

```http
GET /customers
Authorization: Bearer {access_token}
```

### Получить клиента

```http
GET /customers/{id}
Authorization: Bearer {access_token}
```

### Идентифицировать клиента

```http
POST /customers/identify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "session_id": "...",
  "user_id": "external_user_123",
  "email": "user@example.com",
  "name": "Имя Фамилия",
  "metadata": {
    "plan": "pro",
    "company": "Acme Inc"
  }
}
```

---

## Команда

### Список сотрудников

```http
GET /team
Authorization: Bearer {access_token}
```

### Пригласить сотрудника

```http
POST /team/invite
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email": "colleague@example.com",
  "role_id": "...",
  "departments": ["support", "sales"]
}
```

### Изменить роль

```http
PUT /team/{user_id}/role
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role_id": "..."
}
```

---

## Каналы

### Список каналов

```http
GET /channels
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "data": [
    {
      "id": "...",
      "type": "widget",
      "name": "Виджет на сайте",
      "status": "active",
      "config": {}
    },
    {
      "id": "...",
      "type": "telegram",
      "name": "Telegram бот",
      "status": "active",
      "config": {
        "bot_username": "@mybot"
      }
    }
  ]
}
```

### Настроить канал

```http
PUT /channels/{id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Новое имя",
  "config": {
    "greeting": "Привет! Чем помочь?"
  }
}
```

---

## Аналитика

### Статистика

```http
GET /analytics/stats
Authorization: Bearer {access_token}
```

**Query параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| from | date | Начало периода |
| to | date | Конец периода |
| granularity | string | hour, day, week, month |

**Ответ:**
```json
{
  "conversations": {
    "total": 1500,
    "open": 45,
    "closed": 1455,
    "avg_response_time": 120,
    "avg_resolution_time": 3600
  },
  "messages": {
    "total": 15000,
    "from_customers": 8000,
    "from_agents": 5000,
    "from_ai": 2000
  },
  "satisfaction": {
    "average": 4.5,
    "responses": 500
  }
}
```

### Экспорт

```http
POST /analytics/export
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "from": "2026-01-01",
  "to": "2026-01-31",
  "format": "csv"
}
```

---

## Биллинг

### Текущий план

```http
GET /billing/subscription
Authorization: Bearer {access_token}
```

### Использование

```http
GET /billing/usage
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "plan": "pro",
  "period": {
    "start": "2026-02-01",
    "end": "2026-02-28"
  },
  "messages": {
    "used": 2500,
    "limit": 5000
  },
  "storage": {
    "used_mb": 150,
    "limit_mb": 1000
  }
}
```

### Изменить план

```http
POST /billing/subscription/change
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "plan": "enterprise"
}
```

---

## Вебхуки

### Список вебхуков

```http
GET /webhooks
Authorization: Bearer {access_token}
```

### Создать вебхук

```http
POST /webhooks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "url": "https://yoursite.com/webhook",
  "events": [
    "conversation.created",
    "conversation.closed",
    "message.received"
  ],
  "secret": "your_secret_key"
}
```

### События вебхуков

| Событие | Описание |
|---------|----------|
| conversation.created | Новый диалог |
| conversation.closed | Диалог закрыт |
| conversation.assigned | Назначен оператор |
| message.received | Новое сообщение от клиента |
| message.sent | Сообщение отправлено |
| customer.identified | Клиент идентифицирован |

**Формат payload:**
```json
{
  "event": "message.received",
  "timestamp": "2026-02-03T12:00:00Z",
  "data": {
    "conversation_id": "...",
    "message": {
      "id": "...",
      "content": "..."
    }
  }
}
```

**Подпись:** Заголовок `X-Webhook-Signature` содержит HMAC-SHA256 подпись payload.

---

## WebSocket

### Подключение

```javascript
const ws = new WebSocket('wss://api.omnisupport.ru/ws');

// Авторизация
ws.send(JSON.stringify({
  type: 'auth',
  token: 'Bearer eyJ...'
}));

// Подписка на события
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['conversations', 'messages']
}));
```

### События

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'message.new':
      // Новое сообщение
      break;
    case 'conversation.updated':
      // Обновление диалога
      break;
    case 'typing.start':
      // Клиент печатает
      break;
  }
};
```

### Отправка

```javascript
// Индикатор "печатает"
ws.send(JSON.stringify({
  type: 'typing',
  conversation_id: '...'
}));

// Прочитано
ws.send(JSON.stringify({
  type: 'read',
  conversation_id: '...',
  message_id: '...'
}));
```

---

## Widget API

Публичные эндпоинты для виджета (без авторизации).

### Инициализация

```http
POST /widget/v1/init
Content-Type: application/json

{
  "api_key": "pk_live_...",
  "session_id": "browser_session_123"
}
```

### Отправка сообщения

```http
POST /widget/v1/messages
Content-Type: application/json

{
  "api_key": "pk_live_...",
  "session_id": "...",
  "content": "Привет!"
}
```

### Получение истории

```http
GET /widget/v1/messages?api_key=pk_live_...&session_id=...
```

---

## SDK и библиотеки

- [JavaScript/TypeScript](https://github.com/omnisupport/sdk-js)
- [Python](https://github.com/omnisupport/sdk-python)
- [PHP](https://github.com/omnisupport/sdk-php)

---

## Примеры

### cURL

```bash
# Получить диалоги
curl -X GET "https://api.omnisupport.ru/api/v1/conversations" \
  -H "Authorization: Bearer eyJ..."

# Отправить сообщение
curl -X POST "https://api.omnisupport.ru/api/v1/conversations/{id}/messages" \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"content": "Ответ оператора"}'
```

### JavaScript

```javascript
const OmniSupport = require('@omnisupport/sdk');

const client = new OmniSupport({
  apiKey: 'sk_live_...'
});

// Получить диалоги
const conversations = await client.conversations.list({
  status: 'open'
});

// Отправить сообщение
await client.messages.send(conversationId, {
  content: 'Здравствуйте! Чем могу помочь?'
});
```

### Python

```python
from omnisupport import OmniSupport

client = OmniSupport(api_key="sk_live_...")

# Получить диалоги
conversations = client.conversations.list(status="open")

# Отправить сообщение
client.messages.send(
    conversation_id="...",
    content="Здравствуйте! Чем могу помочь?"
)
```

---

## Поддержка

- 📧 Email: api@attention.dev
- 📚 Docs: https://docs.omnisupport.attention.dev
- 💬 Discord: https://discord.gg/omnisupport

---

*Последнее обновление: 3 февраля 2026 г.*
