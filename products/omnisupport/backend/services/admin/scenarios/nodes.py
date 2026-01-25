"""Scenario node types and definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class NodeType(str, Enum):
    """Types of scenario nodes."""

    # Flow control
    START = "start"
    END = "end"
    CONDITION = "condition"
    DELAY = "delay"
    SPLIT = "split"  # Parallel execution
    MERGE = "merge"  # Wait for parallel branches

    # Actions
    SEND_MESSAGE = "send_message"
    SEND_EMAIL = "send_email"
    ASSIGN_OPERATOR = "assign_operator"
    ASSIGN_DEPARTMENT = "assign_department"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    SET_PRIORITY = "set_priority"
    SET_VARIABLE = "set_variable"
    CLOSE_CONVERSATION = "close_conversation"
    TRANSFER_CONVERSATION = "transfer_conversation"

    # AI actions
    AI_CLASSIFY = "ai_classify"
    AI_RESPOND = "ai_respond"
    AI_SUMMARIZE = "ai_summarize"
    AI_SENTIMENT = "ai_sentiment"

    # Integrations
    HTTP_REQUEST = "http_request"
    WEBHOOK = "webhook"

    # Customer actions
    UPDATE_CUSTOMER = "update_customer"
    CREATE_NOTE = "create_note"


@dataclass
class NodePort:
    """Connection port for a node."""

    id: str
    name: str
    type: str = "default"  # default, true, false, error


@dataclass
class NodeDefinition:
    """Definition of a node type."""

    type: NodeType
    name: str
    description: str
    category: str
    icon: str
    inputs: list[NodePort] = field(default_factory=list)
    outputs: list[NodePort] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)


# Node definitions registry
NODE_DEFINITIONS: dict[NodeType, NodeDefinition] = {
    NodeType.START: NodeDefinition(
        type=NodeType.START,
        name="Начало",
        description="Точка входа сценария",
        category="flow",
        icon="play",
        inputs=[],
        outputs=[NodePort("out", "Выход")],
        config_schema={},
    ),
    NodeType.END: NodeDefinition(
        type=NodeType.END,
        name="Конец",
        description="Завершение сценария",
        category="flow",
        icon="stop",
        inputs=[NodePort("in", "Вход")],
        outputs=[],
        config_schema={},
    ),
    NodeType.CONDITION: NodeDefinition(
        type=NodeType.CONDITION,
        name="Условие",
        description="Ветвление по условию",
        category="flow",
        icon="git-branch",
        inputs=[NodePort("in", "Вход")],
        outputs=[
            NodePort("true", "Да", "true"),
            NodePort("false", "Нет", "false"),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "field": {"type": "string", "title": "Поле"},
                "operator": {
                    "type": "string",
                    "enum": ["equals", "not_equals", "contains", "not_contains",
                             "greater_than", "less_than", "is_empty", "is_not_empty",
                             "matches_regex"],
                    "title": "Оператор",
                },
                "value": {"type": "string", "title": "Значение"},
            },
            "required": ["field", "operator"],
        },
    ),
    NodeType.DELAY: NodeDefinition(
        type=NodeType.DELAY,
        name="Задержка",
        description="Пауза перед следующим действием",
        category="flow",
        icon="clock",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "duration": {"type": "integer", "title": "Длительность (сек)", "minimum": 1},
                "unit": {
                    "type": "string",
                    "enum": ["seconds", "minutes", "hours", "days"],
                    "default": "seconds",
                },
            },
            "required": ["duration"],
        },
    ),
    NodeType.SEND_MESSAGE: NodeDefinition(
        type=NodeType.SEND_MESSAGE,
        name="Отправить сообщение",
        description="Отправить сообщение клиенту",
        category="actions",
        icon="message-square",
        inputs=[NodePort("in", "Вход")],
        outputs=[
            NodePort("out", "Успех"),
            NodePort("error", "Ошибка", "error"),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "title": "Сообщение"},
                "use_template": {"type": "boolean", "title": "Использовать шаблон"},
                "template_id": {"type": "string", "title": "ID шаблона"},
            },
            "required": ["message"],
        },
    ),
    NodeType.SEND_EMAIL: NodeDefinition(
        type=NodeType.SEND_EMAIL,
        name="Отправить email",
        description="Отправить email клиенту",
        category="actions",
        icon="mail",
        inputs=[NodePort("in", "Вход")],
        outputs=[
            NodePort("out", "Успех"),
            NodePort("error", "Ошибка", "error"),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "subject": {"type": "string", "title": "Тема"},
                "body": {"type": "string", "title": "Текст"},
                "template_id": {"type": "string", "title": "ID шаблона"},
            },
            "required": ["subject", "body"],
        },
    ),
    NodeType.ASSIGN_OPERATOR: NodeDefinition(
        type=NodeType.ASSIGN_OPERATOR,
        name="Назначить оператора",
        description="Назначить диалог оператору",
        category="actions",
        icon="user-plus",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "operator_id": {"type": "string", "title": "ID оператора"},
                "strategy": {
                    "type": "string",
                    "enum": ["specific", "round_robin", "least_busy", "random"],
                    "default": "round_robin",
                    "title": "Стратегия",
                },
            },
        },
    ),
    NodeType.ASSIGN_DEPARTMENT: NodeDefinition(
        type=NodeType.ASSIGN_DEPARTMENT,
        name="Назначить отдел",
        description="Передать в отдел",
        category="actions",
        icon="users",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "department_id": {"type": "string", "title": "ID отдела"},
            },
            "required": ["department_id"],
        },
    ),
    NodeType.ADD_TAG: NodeDefinition(
        type=NodeType.ADD_TAG,
        name="Добавить тег",
        description="Добавить тег к диалогу",
        category="actions",
        icon="tag",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "tag": {"type": "string", "title": "Тег"},
            },
            "required": ["tag"],
        },
    ),
    NodeType.REMOVE_TAG: NodeDefinition(
        type=NodeType.REMOVE_TAG,
        name="Удалить тег",
        description="Удалить тег диалога",
        category="actions",
        icon="tag",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "tag": {"type": "string", "title": "Тег"},
            },
            "required": ["tag"],
        },
    ),
    NodeType.SET_PRIORITY: NodeDefinition(
        type=NodeType.SET_PRIORITY,
        name="Установить приоритет",
        description="Изменить приоритет диалога",
        category="actions",
        icon="alert-triangle",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "title": "Приоритет",
                },
            },
            "required": ["priority"],
        },
    ),
    NodeType.SET_VARIABLE: NodeDefinition(
        type=NodeType.SET_VARIABLE,
        name="Установить переменную",
        description="Сохранить значение в переменную",
        category="actions",
        icon="variable",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "variable_name": {"type": "string", "title": "Имя переменной"},
                "value": {"type": "string", "title": "Значение"},
                "value_type": {
                    "type": "string",
                    "enum": ["string", "number", "boolean", "expression"],
                    "default": "string",
                },
            },
            "required": ["variable_name", "value"],
        },
    ),
    NodeType.CLOSE_CONVERSATION: NodeDefinition(
        type=NodeType.CLOSE_CONVERSATION,
        name="Закрыть диалог",
        description="Закрыть текущий диалог",
        category="actions",
        icon="x-circle",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "resolution": {"type": "string", "title": "Причина закрытия"},
            },
        },
    ),
    NodeType.AI_CLASSIFY: NodeDefinition(
        type=NodeType.AI_CLASSIFY,
        name="AI Классификация",
        description="Классифицировать сообщение с помощью AI",
        category="ai",
        icon="brain",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "title": "Категории",
                },
                "output_variable": {"type": "string", "title": "Сохранить в переменную"},
            },
            "required": ["categories"],
        },
    ),
    NodeType.AI_RESPOND: NodeDefinition(
        type=NodeType.AI_RESPOND,
        name="AI Ответ",
        description="Сгенерировать ответ с помощью AI",
        category="ai",
        icon="message-circle",
        inputs=[NodePort("in", "Вход")],
        outputs=[
            NodePort("out", "Успех"),
            NodePort("error", "Ошибка", "error"),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "use_knowledge_base": {"type": "boolean", "default": True},
                "system_prompt": {"type": "string", "title": "Системный промпт"},
                "auto_send": {"type": "boolean", "default": False, "title": "Автоотправка"},
            },
        },
    ),
    NodeType.HTTP_REQUEST: NodeDefinition(
        type=NodeType.HTTP_REQUEST,
        name="HTTP запрос",
        description="Выполнить HTTP запрос",
        category="integrations",
        icon="globe",
        inputs=[NodePort("in", "Вход")],
        outputs=[
            NodePort("out", "Успех"),
            NodePort("error", "Ошибка", "error"),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    "default": "POST",
                },
                "url": {"type": "string", "title": "URL"},
                "headers": {"type": "object", "title": "Заголовки"},
                "body": {"type": "string", "title": "Тело запроса"},
                "output_variable": {"type": "string", "title": "Сохранить ответ в"},
            },
            "required": ["url"],
        },
    ),
    NodeType.UPDATE_CUSTOMER: NodeDefinition(
        type=NodeType.UPDATE_CUSTOMER,
        name="Обновить клиента",
        description="Обновить данные клиента",
        category="actions",
        icon="user-edit",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "fields": {
                    "type": "object",
                    "title": "Поля для обновления",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["fields"],
        },
    ),
    NodeType.CREATE_NOTE: NodeDefinition(
        type=NodeType.CREATE_NOTE,
        name="Создать заметку",
        description="Добавить заметку к клиенту",
        category="actions",
        icon="file-text",
        inputs=[NodePort("in", "Вход")],
        outputs=[NodePort("out", "Выход")],
        config_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "title": "Текст заметки"},
            },
            "required": ["content"],
        },
    ),
}


def get_node_definition(node_type: NodeType) -> NodeDefinition | None:
    """Get node definition by type."""
    return NODE_DEFINITIONS.get(node_type)


def get_all_node_definitions() -> list[NodeDefinition]:
    """Get all available node definitions."""
    return list(NODE_DEFINITIONS.values())


def get_nodes_by_category(category: str) -> list[NodeDefinition]:
    """Get node definitions by category."""
    return [n for n in NODE_DEFINITIONS.values() if n.category == category]
