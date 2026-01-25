"""Scenario templates for common use cases."""

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class ScenarioTemplate:
    """Scenario template definition."""

    id: str
    name: str
    description: str
    category: str
    industry: str | None
    tags: list[str]
    nodes: list[dict]
    edges: list[dict]
    variables: dict[str, Any]
    triggers: list[dict]


def _make_node(
    node_type: str,
    config: dict | None = None,
    position: tuple[int, int] = (0, 0),
) -> dict:
    """Create a node dict."""
    return {
        "id": str(uuid4()),
        "type": node_type,
        "position": {"x": position[0], "y": position[1]},
        "data": {"config": config or {}},
    }


def _make_edge(source_id: str, target_id: str, source_handle: str = "out") -> dict:
    """Create an edge dict."""
    return {
        "id": str(uuid4()),
        "source": source_id,
        "target": target_id,
        "sourceHandle": source_handle,
    }


# ==================== Templates ====================

WELCOME_MESSAGE_TEMPLATE = ScenarioTemplate(
    id="welcome_message",
    name="Приветственное сообщение",
    description="Автоматически отправляет приветствие при новом диалоге",
    category="onboarding",
    industry=None,
    tags=["приветствие", "автоответ"],
    nodes=[],
    edges=[],
    variables={"welcome_text": "Здравствуйте! Чем могу вам помочь?"},
    triggers=[
        {
            "event_type": "conversation.created",
            "conditions": [],
        }
    ],
)

# Build nodes for welcome message
_start = _make_node("start", position=(100, 100))
_send = _make_node(
    "send_message",
    {"message": "{{welcome_text}}"},
    position=(100, 200),
)
_end = _make_node("end", position=(100, 300))
WELCOME_MESSAGE_TEMPLATE.nodes = [_start, _send, _end]
WELCOME_MESSAGE_TEMPLATE.edges = [
    _make_edge(_start["id"], _send["id"]),
    _make_edge(_send["id"], _end["id"]),
]


AUTO_ASSIGN_TEMPLATE = ScenarioTemplate(
    id="auto_assign",
    name="Автоназначение оператору",
    description="Автоматически назначает диалог свободному оператору",
    category="routing",
    industry=None,
    tags=["назначение", "роутинг"],
    nodes=[],
    edges=[],
    variables={},
    triggers=[
        {
            "event_type": "conversation.created",
            "conditions": [],
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_assign = _make_node(
    "assign_operator",
    {"strategy": "round_robin"},
    position=(100, 200),
)
_end = _make_node("end", position=(100, 300))
AUTO_ASSIGN_TEMPLATE.nodes = [_start, _assign, _end]
AUTO_ASSIGN_TEMPLATE.edges = [
    _make_edge(_start["id"], _assign["id"]),
    _make_edge(_assign["id"], _end["id"]),
]


WORKING_HOURS_TEMPLATE = ScenarioTemplate(
    id="working_hours",
    name="Нерабочее время",
    description="Отправляет сообщение о нерабочем времени",
    category="scheduling",
    industry=None,
    tags=["расписание", "автоответ"],
    nodes=[],
    edges=[],
    variables={
        "out_of_hours_message": "К сожалению, сейчас мы не работаем. Мы ответим вам в рабочее время.",
    },
    triggers=[
        {
            "event_type": "conversation.created",
            "conditions": [],  # Would need schedule condition
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_send = _make_node(
    "send_message",
    {"message": "{{out_of_hours_message}}"},
    position=(100, 200),
)
_close = _make_node(
    "close_conversation",
    {"resolution": "out_of_hours"},
    position=(100, 300),
)
_end = _make_node("end", position=(100, 400))
WORKING_HOURS_TEMPLATE.nodes = [_start, _send, _close, _end]
WORKING_HOURS_TEMPLATE.edges = [
    _make_edge(_start["id"], _send["id"]),
    _make_edge(_send["id"], _close["id"]),
    _make_edge(_close["id"], _end["id"]),
]


AI_CLASSIFICATION_TEMPLATE = ScenarioTemplate(
    id="ai_classification",
    name="AI Классификация обращений",
    description="Классифицирует обращения с помощью AI и направляет в нужный отдел",
    category="ai",
    industry=None,
    tags=["ai", "классификация", "роутинг"],
    nodes=[],
    edges=[],
    variables={
        "categories": ["Техподдержка", "Продажи", "Возврат", "Другое"],
    },
    triggers=[
        {
            "event_type": "message.received",
            "conditions": [],
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_classify = _make_node(
    "ai_classify",
    {
        "categories": ["Техподдержка", "Продажи", "Возврат", "Другое"],
        "output_variable": "category",
    },
    position=(100, 200),
)
_cond_tech = _make_node(
    "condition",
    {"field": "category", "operator": "equals", "value": "Техподдержка"},
    position=(100, 300),
)
_cond_sales = _make_node(
    "condition",
    {"field": "category", "operator": "equals", "value": "Продажи"},
    position=(300, 400),
)
_tag_tech = _make_node("add_tag", {"tag": "tech_support"}, position=(0, 400))
_tag_sales = _make_node("add_tag", {"tag": "sales"}, position=(200, 500))
_tag_other = _make_node("add_tag", {"tag": "other"}, position=(400, 500))
_end = _make_node("end", position=(200, 600))

AI_CLASSIFICATION_TEMPLATE.nodes = [
    _start, _classify, _cond_tech, _cond_sales, _tag_tech, _tag_sales, _tag_other, _end
]
AI_CLASSIFICATION_TEMPLATE.edges = [
    _make_edge(_start["id"], _classify["id"]),
    _make_edge(_classify["id"], _cond_tech["id"]),
    _make_edge(_cond_tech["id"], _tag_tech["id"], "true"),
    _make_edge(_cond_tech["id"], _cond_sales["id"], "false"),
    _make_edge(_cond_sales["id"], _tag_sales["id"], "true"),
    _make_edge(_cond_sales["id"], _tag_other["id"], "false"),
    _make_edge(_tag_tech["id"], _end["id"]),
    _make_edge(_tag_sales["id"], _end["id"]),
    _make_edge(_tag_other["id"], _end["id"]),
]


VIP_CUSTOMER_TEMPLATE = ScenarioTemplate(
    id="vip_customer",
    name="VIP клиент",
    description="Устанавливает высокий приоритет для VIP клиентов",
    category="routing",
    industry=None,
    tags=["vip", "приоритет"],
    nodes=[],
    edges=[],
    variables={},
    triggers=[
        {
            "event_type": "conversation.created",
            "conditions": [
                {"field": "customer.tags", "operator": "contains", "value": "vip"}
            ],
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_priority = _make_node("set_priority", {"priority": "urgent"}, position=(100, 200))
_tag = _make_node("add_tag", {"tag": "vip_customer"}, position=(100, 300))
_end = _make_node("end", position=(100, 400))
VIP_CUSTOMER_TEMPLATE.nodes = [_start, _priority, _tag, _end]
VIP_CUSTOMER_TEMPLATE.edges = [
    _make_edge(_start["id"], _priority["id"]),
    _make_edge(_priority["id"], _tag["id"]),
    _make_edge(_tag["id"], _end["id"]),
]


FEEDBACK_REQUEST_TEMPLATE = ScenarioTemplate(
    id="feedback_request",
    name="Запрос обратной связи",
    description="Запрашивает оценку после закрытия диалога",
    category="feedback",
    industry=None,
    tags=["обратная связь", "csat"],
    nodes=[],
    edges=[],
    variables={
        "feedback_message": "Спасибо за обращение! Пожалуйста, оцените качество нашего обслуживания от 1 до 5.",
    },
    triggers=[
        {
            "event_type": "conversation.closed",
            "conditions": [],
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_delay = _make_node("delay", {"duration": 60, "unit": "seconds"}, position=(100, 200))
_send = _make_node(
    "send_message",
    {"message": "{{feedback_message}}"},
    position=(100, 300),
)
_end = _make_node("end", position=(100, 400))
FEEDBACK_REQUEST_TEMPLATE.nodes = [_start, _delay, _send, _end]
FEEDBACK_REQUEST_TEMPLATE.edges = [
    _make_edge(_start["id"], _delay["id"]),
    _make_edge(_delay["id"], _send["id"]),
    _make_edge(_send["id"], _end["id"]),
]


ECOMMERCE_ORDER_TEMPLATE = ScenarioTemplate(
    id="ecommerce_order",
    name="E-commerce: Статус заказа",
    description="Автоответ на вопросы о статусе заказа",
    category="ai",
    industry="ecommerce",
    tags=["ecommerce", "заказ", "ai"],
    nodes=[],
    edges=[],
    variables={},
    triggers=[
        {
            "event_type": "message.received",
            "conditions": [
                {"field": "message_text", "operator": "regex", "value": "(заказ|доставк|статус|где мой)"}
            ],
        }
    ],
)

_start = _make_node("start", position=(100, 100))
_ai_respond = _make_node(
    "ai_respond",
    {
        "use_knowledge_base": True,
        "system_prompt": "Ты помощник интернет-магазина. Отвечай на вопросы о заказах.",
        "auto_send": True,
    },
    position=(100, 200),
)
_tag = _make_node("add_tag", {"tag": "order_inquiry"}, position=(100, 300))
_end = _make_node("end", position=(100, 400))
ECOMMERCE_ORDER_TEMPLATE.nodes = [_start, _ai_respond, _tag, _end]
ECOMMERCE_ORDER_TEMPLATE.edges = [
    _make_edge(_start["id"], _ai_respond["id"]),
    _make_edge(_ai_respond["id"], _tag["id"]),
    _make_edge(_tag["id"], _end["id"]),
]


# ==================== Registry ====================

TEMPLATES: dict[str, ScenarioTemplate] = {
    "welcome_message": WELCOME_MESSAGE_TEMPLATE,
    "auto_assign": AUTO_ASSIGN_TEMPLATE,
    "working_hours": WORKING_HOURS_TEMPLATE,
    "ai_classification": AI_CLASSIFICATION_TEMPLATE,
    "vip_customer": VIP_CUSTOMER_TEMPLATE,
    "feedback_request": FEEDBACK_REQUEST_TEMPLATE,
    "ecommerce_order": ECOMMERCE_ORDER_TEMPLATE,
}


def get_template(template_id: str) -> ScenarioTemplate | None:
    """Get template by ID."""
    return TEMPLATES.get(template_id)


def get_all_templates() -> list[ScenarioTemplate]:
    """Get all available templates."""
    return list(TEMPLATES.values())


def get_templates_by_category(category: str) -> list[ScenarioTemplate]:
    """Get templates by category."""
    return [t for t in TEMPLATES.values() if t.category == category]


def get_templates_by_industry(industry: str) -> list[ScenarioTemplate]:
    """Get templates by industry."""
    return [t for t in TEMPLATES.values() if t.industry == industry]


def get_template_categories() -> list[str]:
    """Get all template categories."""
    return list(set(t.category for t in TEMPLATES.values()))
