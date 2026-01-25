"""SQLAlchemy models for OmniSupport."""

from shared.models.tenant import Tenant
from shared.models.user import User, Role, Permission, UserRole
from shared.models.department import Department, DepartmentMember
from shared.models.skill import Skill, UserSkill
from shared.models.customer import Customer, CustomerIdentity, CustomerNote, CustomerTag
from shared.models.conversation import Conversation, Message, CannedResponse
from shared.models.attachment import Attachment, AttachmentType, AttachmentStatus
from shared.models.channel import Channel, WidgetSettings
from shared.models.integration import Integration, Webhook, WebhookDelivery, ApiKey
from shared.models.scenario import Scenario, Trigger, ScenarioVariable
from shared.models.knowledge import KnowledgeDocument, KnowledgeChunk, CrawlerConfig
from shared.models.analytics import AnalyticsSnapshot, Report
from shared.models.billing import Subscription, Plan, Invoice, UsageRecord, PaymentMethod
from shared.models.ai import AIInteraction

__all__ = [
    # Tenant
    "Tenant",
    # User
    "User",
    "Role",
    "Permission",
    "UserRole",
    # Department
    "Department",
    "DepartmentMember",
    # Skill
    "Skill",
    "UserSkill",
    # Customer
    "Customer",
    "CustomerIdentity",
    "CustomerNote",
    "CustomerTag",
    # Conversation
    "Conversation",
    "Message",
    "CannedResponse",
    # Attachment
    "Attachment",
    "AttachmentType",
    "AttachmentStatus",
    # Channel
    "Channel",
    "WidgetSettings",
    # Integration
    "Integration",
    "Webhook",
    "WebhookDelivery",
    "ApiKey",
    # Scenario
    "Scenario",
    "Trigger",
    "ScenarioVariable",
    # Knowledge
    "KnowledgeDocument",
    "KnowledgeChunk",
    "CrawlerConfig",
    # Analytics
    "AnalyticsSnapshot",
    "Report",
    # Billing
    "Subscription",
    "Plan",
    "Invoice",
    "UsageRecord",
    "PaymentMethod",
    # AI
    "AIInteraction",
]
