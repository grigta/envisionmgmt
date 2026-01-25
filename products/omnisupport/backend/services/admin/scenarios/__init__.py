"""Scenario automation module."""

from services.admin.scenarios.executor import ScenarioExecutor, get_scenario_executor
from services.admin.scenarios.nodes import (
    NodeType,
    NodeDefinition,
    NodePort,
    NODE_DEFINITIONS,
    get_node_definition,
    get_all_node_definitions,
    get_nodes_by_category,
)
from services.admin.scenarios.templates import (
    ScenarioTemplate,
    TEMPLATES,
    get_template,
    get_all_templates,
    get_templates_by_category,
    get_templates_by_industry,
    get_template_categories,
)
from services.admin.scenarios.triggers import (
    TriggerEventType,
    TriggerEvaluator,
    TriggerService,
    get_trigger_service,
)

__all__ = [
    # Executor
    "ScenarioExecutor",
    "get_scenario_executor",
    # Nodes
    "NodeType",
    "NodeDefinition",
    "NodePort",
    "NODE_DEFINITIONS",
    "get_node_definition",
    "get_all_node_definitions",
    "get_nodes_by_category",
    # Templates
    "ScenarioTemplate",
    "TEMPLATES",
    "get_template",
    "get_all_templates",
    "get_templates_by_category",
    "get_templates_by_industry",
    "get_template_categories",
    # Triggers
    "TriggerEventType",
    "TriggerEvaluator",
    "TriggerService",
    "get_trigger_service",
]
