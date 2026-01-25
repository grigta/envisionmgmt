# OmniSupport — Техническая архитектура

## Обзор системы

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              КЛИЕНТЫ (End Users)                            │
├─────────────┬─────────────┬─────────────┬───────────────────────────────────┤
│  Telegram   │  WhatsApp   │ Web Widget  │         Будущие каналы            │
└──────┬──────┴──────┬──────┴──────┬──────┴───────────────────────────────────┘
       │             │             │
       ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / LOAD BALANCER                         │
│                              (Nginx / Traefik)                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
       ▼                          ▼                          ▼
┌─────────────┐          ┌─────────────┐          ┌─────────────────┐
│  Channel    │          │    Core     │          │   Admin/Web     │
│  Service    │          │   Service   │          │    Service      │
│ (Adapters)  │          │   (Main)    │          │  (Dashboard)    │
└──────┬──────┘          └──────┬──────┘          └────────┬────────┘
       │                        │                          │
       └────────────────────────┼──────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MESSAGE BROKER                                   │
│                         (Redis / RabbitMQ)                                  │
└───────┬─────────────┬─────────────┬─────────────┬─────────────┬────────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  Router   │  │    AI     │  │ Analytics │  │  Webhook  │  │  Notify   │
│  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │  │  Worker   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │              │              │
      └──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────────────┤
│ PostgreSQL  │    Redis    │   Qdrant    │ Elasticsearch│   S3 Storage      │
│  (Primary)  │   (Cache)   │  (Vectors)  │   (Search)   │   (Files)         │
└─────────────┴─────────────┴─────────────┴─────────────┴────────────────────┘
```

---

## Микросервисы

### 1. Channel Service (Адаптеры каналов)

**Ответственность**: Приём и отправка сообщений через различные каналы

```
channel-service/
├── adapters/
│   ├── telegram/
│   │   ├── webhook.py      # Приём webhook от Telegram
│   │   ├── sender.py       # Отправка сообщений
│   │   └── parser.py       # Парсинг форматов (текст, фото, документы)
│   ├── whatsapp/
│   │   ├── webhook.py
│   │   ├── sender.py
│   │   └── parser.py
│   └── web_widget/
│       ├── websocket.py    # WebSocket соединения
│       └── api.py          # REST API для виджета
├── models/
│   └── message.py          # Унифицированная модель сообщения
└── router.py               # Роутинг в Core Service
```

**Унифицированная модель сообщения**:
```python
class UnifiedMessage:
    id: UUID
    tenant_id: UUID              # ID клиента SaaS
    channel: ChannelType         # telegram | whatsapp | web
    channel_message_id: str      # ID в исходном канале
    channel_user_id: str         # ID пользователя в канале
    customer_id: UUID | None     # Связанный профиль клиента
    conversation_id: UUID        # ID диалога
    direction: Direction         # inbound | outbound
    content_type: ContentType    # text | image | file | audio
    content: MessageContent
    metadata: dict
    created_at: datetime
```

### 2. Core Service (Ядро системы)

**Ответственность**: Бизнес-логика, управление диалогами, клиентами

```
core-service/
├── domains/
│   ├── conversations/
│   │   ├── models.py       # Conversation, Message
│   │   ├── service.py      # Логика диалогов
│   │   └── repository.py   # Работа с БД
│   ├── customers/
│   │   ├── models.py       # Customer, CustomerIdentity
│   │   ├── service.py      # Идентификация, объединение
│   │   └── repository.py
│   ├── operators/
│   │   ├── models.py       # Operator, Team, Skill
│   │   ├── service.py      # Статусы, нагрузка
│   │   └── repository.py
│   └── routing/
│       ├── strategies.py   # Round-robin, skill-based
│       └── service.py      # Распределение диалогов
├── api/
│   ├── v1/
│   │   ├── conversations.py
│   │   ├── customers.py
│   │   └── operators.py
│   └── websocket.py        # Real-time для операторов
└── events/
    ├── publishers.py       # Отправка событий в брокер
    └── handlers.py         # Обработка входящих событий
```

### 3. AI Service (ИИ-ассистент)

**Ответственность**: RAG, генерация подсказок, классификация

```
ai-service/
├── rag/
│   ├── indexer.py          # Индексация документов
│   ├── retriever.py        # Поиск релевантных чанков
│   ├── chunker.py          # Разбиение на чанки
│   └── embeddings.py       # Генерация эмбеддингов
├── llm/
│   ├── providers/
│   │   ├── yandexgpt.py    # YandexGPT API
│   │   └── gigachat.py     # GigaChat API
│   ├── prompts/
│   │   ├── suggestion.py   # Промпт для подсказок
│   │   ├── summary.py      # Промпт для суммаризации
│   │   └── sentiment.py    # Промпт для анализа тональности
│   └── service.py          # Оркестрация LLM вызовов
├── knowledge_base/
│   ├── documents.py        # Загрузка документов
│   ├── crawler.py          # Краулинг сайтов
│   └── history.py          # Обучение на истории
└── api/
    └── v1/
        ├── suggestions.py  # Endpoint для подсказок
        └── knowledge.py    # Управление базой знаний
```

**RAG Pipeline**:
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Запрос    │────▶│  Embedding  │────▶│   Vector    │────▶│   Top-K     │
│  оператора  │     │   Model     │     │   Search    │     │  Chunks     │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
│  Подсказка  │◀────│     LLM     │◀────│   Prompt    │◀───────────┘
│             │     │  YandexGPT  │     │  + Context  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 4. Admin Service (Админ-панель)

**Ответственность**: Настройки, конструктор, аналитика

```
admin-service/
├── scenarios/
│   ├── models.py           # ScenarioNode, Trigger, Action
│   ├── builder.py          # Валидация и сборка сценария
│   ├── executor.py         # Исполнение сценария
│   └── templates.py        # Отраслевые шаблоны
├── settings/
│   ├── tenant.py           # Настройки тенанта
│   ├── channels.py         # Настройки каналов
│   └── branding.py         # White-label настройки
├── analytics/
│   ├── collectors.py       # Сбор метрик
│   ├── aggregators.py      # Агрегация
│   └── exporters.py        # Экспорт отчётов
└── api/
    └── v1/
        ├── scenarios.py
        ├── settings.py
        └── analytics.py
```

### 5. Worker Services (Фоновые задачи)

```
workers/
├── router_worker/          # Распределение диалогов
│   └── main.py
├── ai_worker/              # Асинхронная генерация подсказок
│   └── main.py
├── analytics_worker/       # Расчёт метрик
│   └── main.py
├── webhook_worker/         # Отправка вебхуков
│   └── main.py
└── notify_worker/          # Уведомления (email, push)
    └── main.py
```

---

## Модели данных

### PostgreSQL Schema

```sql
-- Тенанты (клиенты SaaS)
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    branding JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Пользователи (операторы, админы)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- admin, operator, viewer
    skills TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'offline',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- Клиенты (конечные пользователи)
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    phone VARCHAR(50),
    email VARCHAR(255),
    name VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Идентификаторы клиентов в каналах
CREATE TABLE customer_identities (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    channel VARCHAR(50) NOT NULL,
    channel_user_id VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel, channel_user_id)
);

-- Диалоги
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    customer_id UUID REFERENCES customers(id),
    assigned_to UUID REFERENCES users(id),
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'open', -- open, pending, resolved, closed
    priority VARCHAR(50) DEFAULT 'normal',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Сообщения
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    sender_type VARCHAR(50) NOT NULL, -- customer, operator, bot
    sender_id UUID,
    channel_message_id VARCHAR(255),
    content_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Сценарии
CREATE TABLE scenarios (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT false,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB NOT NULL,
    nodes JSONB NOT NULL, -- Дерево сценария
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- База знаний
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    source_type VARCHAR(50) NOT NULL, -- file, url, history
    source_url TEXT,
    title VARCHAR(255),
    content TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, indexed, failed
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP
);

-- Индексы
CREATE INDEX idx_conversations_tenant_status ON conversations(tenant_id, status);
CREATE INDEX idx_conversations_assigned ON conversations(assigned_to, status);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_customers_tenant ON customers(tenant_id);
CREATE INDEX idx_customer_identities_channel ON customer_identities(channel, channel_user_id);
```

### Qdrant Collections

```python
# Коллекция для документов базы знаний
knowledge_collection = {
    "name": "knowledge_{tenant_id}",
    "vectors": {
        "size": 1024,  # YandexGPT embeddings
        "distance": "Cosine"
    },
    "payload_schema": {
        "document_id": "uuid",
        "chunk_index": "integer",
        "content": "text",
        "source_type": "keyword",
        "metadata": "json"
    }
}

# Коллекция для истории диалогов
history_collection = {
    "name": "history_{tenant_id}",
    "vectors": {
        "size": 1024,
        "distance": "Cosine"
    },
    "payload_schema": {
        "message_id": "uuid",
        "conversation_id": "uuid",
        "question": "text",
        "answer": "text",
        "rating": "integer",  # Оценка ответа
        "operator_id": "uuid"
    }
}
```

---

## API Contracts

### REST API

#### Conversations

```yaml
# Получить диалоги оператора
GET /api/v1/conversations
Query:
  status: open | pending | resolved | closed
  assigned_to: uuid | "me" | "unassigned"
  channel: telegram | whatsapp | web
  limit: integer
  offset: integer
Response:
  items: Conversation[]
  total: integer

# Отправить сообщение
POST /api/v1/conversations/{id}/messages
Body:
  content_type: text | image | file
  content: object
Response:
  message: Message

# Назначить на оператора
POST /api/v1/conversations/{id}/assign
Body:
  operator_id: uuid
Response:
  conversation: Conversation
```

#### AI Suggestions

```yaml
# Получить подсказку
POST /api/v1/ai/suggestions
Body:
  conversation_id: uuid
  context_messages: integer  # Сколько последних сообщений включить
Response:
  suggestion: string
  confidence: float
  sources: Source[]  # Откуда взята информация

# Суммаризировать диалог
POST /api/v1/ai/summarize
Body:
  conversation_id: uuid
Response:
  summary: string
  key_points: string[]
```

### WebSocket Events

```typescript
// Подключение оператора
interface OperatorConnect {
  type: "operator.connect";
  operator_id: string;
  token: string;
}

// Новое сообщение
interface NewMessage {
  type: "message.new";
  conversation_id: string;
  message: Message;
}

// Новый диалог в очереди
interface ConversationQueued {
  type: "conversation.queued";
  conversation: Conversation;
}

// Диалог назначен
interface ConversationAssigned {
  type: "conversation.assigned";
  conversation_id: string;
  operator_id: string;
}

// ИИ-подсказка готова
interface AISuggestionReady {
  type: "ai.suggestion";
  conversation_id: string;
  suggestion: string;
  confidence: float;
}

// Клиент печатает
interface CustomerTyping {
  type: "customer.typing";
  conversation_id: string;
  is_typing: boolean;
}
```

---

## Процессы

### 1. Обработка входящего сообщения

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Channel  │───▶│  Parse   │───▶│ Identify │───▶│  Route   │
│ Webhook  │    │ Message  │    │ Customer │    │ Message  │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
     ┌───────────────────────────────────────────────┤
     │                                               │
     ▼                                               ▼
┌──────────┐                                   ┌──────────┐
│ Execute  │                                   │  Assign  │
│ Scenario │                                   │ Operator │
└────┬─────┘                                   └────┬─────┘
     │                                              │
     ▼                                              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐  ┌──────────┐
│   Save   │───▶│  Notify  │───▶│ Generate │──▶│  WebSocket│
│ Message  │    │ Operator │    │ AI Hint  │   │   Push   │
└──────────┘    └──────────┘    └──────────┘  └──────────┘
```

### 2. Идентификация клиента

```python
async def identify_customer(
    tenant_id: UUID,
    channel: str,
    channel_user_id: str,
    contact_info: dict  # phone, email из профиля канала
) -> Customer:

    # 1. Поиск по channel identity
    identity = await find_identity(channel, channel_user_id)
    if identity:
        return identity.customer

    # 2. Поиск по контактным данным
    if contact_info.get("phone"):
        customer = await find_by_phone(tenant_id, contact_info["phone"])
        if customer:
            await create_identity(customer.id, channel, channel_user_id)
            return customer

    if contact_info.get("email"):
        customer = await find_by_email(tenant_id, contact_info["email"])
        if customer:
            await create_identity(customer.id, channel, channel_user_id)
            return customer

    # 3. Создание нового клиента
    customer = await create_customer(tenant_id, contact_info)
    await create_identity(customer.id, channel, channel_user_id)
    return customer
```

### 3. Распределение диалогов

```python
class RoutingStrategy(ABC):
    @abstractmethod
    async def select_operator(
        self,
        conversation: Conversation,
        available_operators: list[Operator]
    ) -> Operator | None:
        pass

class RoundRobinStrategy(RoutingStrategy):
    async def select_operator(self, conversation, operators):
        # Выбираем оператора с наименьшим количеством активных диалогов
        sorted_ops = sorted(operators, key=lambda o: o.active_conversations)
        return sorted_ops[0] if sorted_ops else None

class SkillBasedStrategy(RoutingStrategy):
    async def select_operator(self, conversation, operators):
        # Определяем требуемые навыки по тегам/категории
        required_skills = await classify_conversation(conversation)

        # Фильтруем операторов по навыкам
        matching = [o for o in operators if set(required_skills) <= set(o.skills)]

        if matching:
            return min(matching, key=lambda o: o.active_conversations)

        # Fallback на любого свободного
        return min(operators, key=lambda o: o.active_conversations)

class ManualPickStrategy(RoutingStrategy):
    async def select_operator(self, conversation, operators):
        # Не назначаем автоматически, оставляем в общей очереди
        return None
```

---

## Безопасность

### Аутентификация

```python
# JWT токены
ACCESS_TOKEN_EXPIRE = 15  # минут
REFRESH_TOKEN_EXPIRE = 7  # дней

class TokenPayload:
    user_id: UUID
    tenant_id: UUID
    role: str
    permissions: list[str]
    exp: datetime

# API Key для интеграций
class APIKey:
    id: UUID
    tenant_id: UUID
    name: str
    key_hash: str
    permissions: list[str]
    rate_limit: int  # requests per minute
    expires_at: datetime | None
```

### RBAC

```python
ROLES = {
    "owner": ["*"],  # Все права
    "admin": [
        "conversations:*",
        "customers:*",
        "operators:manage",
        "settings:*",
        "analytics:*",
        "knowledge:*",
        "scenarios:*"
    ],
    "operator": [
        "conversations:read",
        "conversations:reply",
        "conversations:assign_self",
        "customers:read",
        "customers:update",
        "knowledge:read"
    ],
    "viewer": [
        "conversations:read",
        "customers:read",
        "analytics:read"
    ]
}
```

### Rate Limiting

```python
RATE_LIMITS = {
    "api": {
        "default": "100/minute",
        "ai_suggestions": "30/minute",
        "file_upload": "10/minute"
    },
    "webhook": {
        "telegram": "1000/second",
        "whatsapp": "500/second"
    }
}
```

---

## Масштабирование

### Горизонтальное масштабирование

```yaml
# Kubernetes deployment example
services:
  channel-service:
    replicas: 3
    resources:
      cpu: 500m
      memory: 512Mi

  core-service:
    replicas: 5
    resources:
      cpu: 1000m
      memory: 1Gi

  ai-service:
    replicas: 2
    resources:
      cpu: 2000m
      memory: 2Gi

  admin-service:
    replicas: 2
    resources:
      cpu: 500m
      memory: 512Mi
```

### Очереди и партиционирование

```python
# Партиционирование очередей по tenant_id
QUEUE_PARTITIONS = {
    "messages": 16,      # Партиции для входящих сообщений
    "ai_tasks": 8,       # Партиции для AI задач
    "webhooks": 4,       # Партиции для исходящих вебхуков
    "analytics": 4       # Партиции для аналитики
}

# Consumer groups
def get_partition(tenant_id: UUID, num_partitions: int) -> int:
    return hash(str(tenant_id)) % num_partitions
```

---

## Мониторинг

### Метрики (Prometheus)

```python
# Бизнес-метрики
messages_total = Counter("messages_total", ["tenant", "channel", "direction"])
conversations_total = Counter("conversations_total", ["tenant", "channel", "status"])
ai_suggestions_total = Counter("ai_suggestions_total", ["tenant", "accepted"])

# Технические метрики
request_duration = Histogram("request_duration_seconds", ["service", "endpoint"])
queue_size = Gauge("queue_size", ["queue_name"])
active_websockets = Gauge("active_websockets", ["tenant"])
```

### Алерты

```yaml
alerts:
  - name: HighResponseTime
    condition: request_duration_seconds > 2
    severity: warning

  - name: QueueBacklog
    condition: queue_size > 10000
    severity: critical

  - name: AIServiceDown
    condition: up{service="ai-service"} == 0
    severity: critical

  - name: HighErrorRate
    condition: rate(errors_total[5m]) > 0.01
    severity: warning
```

---

## Деплой

### Инфраструктура

```
┌─────────────────────────────────────────────────────────────┐
│                    Yandex Cloud / VK Cloud                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Kubernetes  │  │  Managed    │  │   Object Storage    │ │
│  │   Cluster   │  │ PostgreSQL  │  │      (S3)           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Managed   │  │  Managed    │  │    Container        │ │
│  │    Redis    │  │ Elasticsearch│  │    Registry         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - pytest --cov=app tests/
    - ruff check app/
    - mypy app/

build:
  stage: build
  script:
    - docker build -t $REGISTRY/$SERVICE:$CI_COMMIT_SHA .
    - docker push $REGISTRY/$SERVICE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/$SERVICE $SERVICE=$REGISTRY/$SERVICE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/$SERVICE
```

---

*Версия документа: 1.0*
*Последнее обновление: 20 января 2026*
