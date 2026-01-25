"""API v1 router."""

from fastapi import APIRouter

from services.core.api.v1.auth import router as auth_router
from services.core.api.v1.users import router as users_router
from services.core.api.v1.team import router as team_router
from services.core.api.v1.customers import router as customers_router
from services.core.api.v1.conversations import router as conversations_router
from services.core.api.v1.channels import router as channels_router
from services.core.api.v1.ai import router as ai_router
from services.core.api.v1.knowledge import router as knowledge_router
from services.core.api.v1.scenarios import router as scenarios_router
from services.core.api.v1.analytics import router as analytics_router
from services.core.api.v1.settings import router as settings_router
from services.core.api.v1.branding import router as branding_router
from services.core.api.v1.billing import router as billing_router
from services.core.api.v1.integrations import router as integrations_router
from services.core.api.v1.webhooks import router as webhooks_router

router = APIRouter()

# Include all routers
router.include_router(auth_router, prefix="/auth", tags=["Аутентификация"])
router.include_router(users_router, prefix="/users", tags=["Пользователи"])
router.include_router(team_router, prefix="/team", tags=["Команда"])
router.include_router(customers_router, prefix="/customers", tags=["Клиенты"])
router.include_router(conversations_router, prefix="/conversations", tags=["Диалоги"])
router.include_router(channels_router, prefix="/channels", tags=["Каналы"])
router.include_router(ai_router, prefix="/ai", tags=["ИИ"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["База знаний"])
router.include_router(scenarios_router, prefix="/scenarios", tags=["Сценарии"])
router.include_router(analytics_router, prefix="/analytics", tags=["Аналитика"])
router.include_router(settings_router, prefix="/settings", tags=["Настройки"])
router.include_router(branding_router, prefix="/branding", tags=["Брендинг"])
router.include_router(billing_router, prefix="/billing", tags=["Биллинг"])
router.include_router(integrations_router, prefix="/integrations", tags=["Интеграции"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["Вебхуки"])
