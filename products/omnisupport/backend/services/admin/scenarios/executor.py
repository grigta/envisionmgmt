"""Scenario executor - runs scenario workflows."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.scenario import Scenario, ScenarioExecution, ExecutionStatus
from shared.models.conversation import Conversation, Message, ConversationStatus, ConversationPriority
from shared.models.customer import Customer, CustomerNote
from shared.events.publisher import get_publisher
from shared.events.types import EventType

from services.admin.scenarios.nodes import NodeType
from services.ai.llm.service import get_llm_service
from services.ai.rag.retriever import get_rag_service

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for scenario execution."""

    tenant_id: UUID
    scenario_id: UUID
    execution_id: UUID

    # Trigger data
    conversation_id: UUID | None = None
    customer_id: UUID | None = None
    message_id: UUID | None = None
    trigger_event: str | None = None
    trigger_data: dict = field(default_factory=dict)

    # Runtime variables
    variables: dict[str, Any] = field(default_factory=dict)

    # Execution state
    current_node_id: str | None = None
    visited_nodes: list[str] = field(default_factory=list)
    error: str | None = None


class ScenarioExecutor:
    """Executes scenario workflows."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()

    async def execute(
        self,
        scenario_id: UUID,
        trigger_event: str,
        trigger_data: dict,
        tenant_id: UUID,
    ) -> UUID:
        """
        Execute a scenario.

        Returns execution ID.
        """
        async with get_session() as session:
            # Get scenario
            result = await session.execute(
                select(Scenario).where(
                    Scenario.id == scenario_id,
                    Scenario.tenant_id == tenant_id,
                    Scenario.is_active == True,
                )
            )
            scenario = result.scalar_one_or_none()

            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found or inactive")

            # Create execution record
            execution = ScenarioExecution(
                scenario_id=scenario_id,
                tenant_id=tenant_id,
                status=ExecutionStatus.RUNNING,
                trigger_event=trigger_event,
                trigger_data=trigger_data,
                started_at=datetime.now(timezone.utc),
            )
            session.add(execution)
            await session.commit()
            await session.refresh(execution)

            # Build context
            context = ExecutionContext(
                tenant_id=tenant_id,
                scenario_id=scenario_id,
                execution_id=execution.id,
                conversation_id=trigger_data.get("conversation_id"),
                customer_id=trigger_data.get("customer_id"),
                message_id=trigger_data.get("message_id"),
                trigger_event=trigger_event,
                trigger_data=trigger_data,
                variables=dict(scenario.variables or {}),
            )

            # Add trigger data to variables
            context.variables["trigger"] = trigger_data

            try:
                # Execute workflow
                await self._execute_workflow(session, scenario, context)

                # Update execution status
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
                execution.result = {"variables": context.variables}

            except Exception as e:
                logger.error(f"Scenario execution error: {e}", exc_info=True)
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)[:1000]
                context.error = str(e)

            execution.execution_log = {
                "visited_nodes": context.visited_nodes,
                "final_variables": context.variables,
            }
            await session.commit()

            return execution.id

    async def _execute_workflow(
        self,
        session: AsyncSession,
        scenario: Scenario,
        context: ExecutionContext,
    ):
        """Execute the scenario workflow."""
        nodes = scenario.nodes or []
        edges = scenario.edges or []

        # Find start node
        start_node = next((n for n in nodes if n.get("type") == NodeType.START.value), None)
        if not start_node:
            raise ValueError("No start node found")

        # Build adjacency map
        adjacency: dict[str, list[dict]] = {}
        for edge in edges:
            source = edge.get("source")
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append(edge)

        # Execute from start
        await self._execute_node(session, start_node, nodes, adjacency, context)

    async def _execute_node(
        self,
        session: AsyncSession,
        node: dict,
        all_nodes: list[dict],
        adjacency: dict[str, list[dict]],
        context: ExecutionContext,
    ):
        """Execute a single node and continue to next."""
        node_id = node.get("id")
        node_type = node.get("type")
        config = node.get("data", {}).get("config", {})

        context.current_node_id = node_id
        context.visited_nodes.append(node_id)

        logger.debug(f"Executing node {node_id} ({node_type})")

        # Execute node based on type
        output_port = await self._execute_node_action(
            session, NodeType(node_type), config, context
        )

        # Find next node based on output port
        outgoing_edges = adjacency.get(node_id, [])

        next_edge = None
        for edge in outgoing_edges:
            source_handle = edge.get("sourceHandle", "out")
            if source_handle == output_port or (output_port == "out" and source_handle in ("out", None)):
                next_edge = edge
                break

        if next_edge:
            target_id = next_edge.get("target")
            next_node = next((n for n in all_nodes if n.get("id") == target_id), None)

            if next_node and next_node.get("type") != NodeType.END.value:
                await self._execute_node(session, next_node, all_nodes, adjacency, context)

    async def _execute_node_action(
        self,
        session: AsyncSession,
        node_type: NodeType,
        config: dict,
        context: ExecutionContext,
    ) -> str:
        """
        Execute node action and return output port name.
        """
        # Substitute variables in config
        config = self._substitute_variables(config, context.variables)

        try:
            if node_type == NodeType.START:
                return "out"

            elif node_type == NodeType.END:
                return "out"

            elif node_type == NodeType.CONDITION:
                result = await self._evaluate_condition(config, context)
                return "true" if result else "false"

            elif node_type == NodeType.DELAY:
                duration = config.get("duration", 0)
                unit = config.get("unit", "seconds")
                multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
                seconds = duration * multipliers.get(unit, 1)
                await asyncio.sleep(min(seconds, 300))  # Max 5 min delay
                return "out"

            elif node_type == NodeType.SEND_MESSAGE:
                return await self._send_message(session, config, context)

            elif node_type == NodeType.SEND_EMAIL:
                return await self._send_email(config, context)

            elif node_type == NodeType.ASSIGN_OPERATOR:
                await self._assign_operator(session, config, context)
                return "out"

            elif node_type == NodeType.ASSIGN_DEPARTMENT:
                await self._assign_department(session, config, context)
                return "out"

            elif node_type == NodeType.ADD_TAG:
                await self._add_tag(session, config, context)
                return "out"

            elif node_type == NodeType.REMOVE_TAG:
                await self._remove_tag(session, config, context)
                return "out"

            elif node_type == NodeType.SET_PRIORITY:
                await self._set_priority(session, config, context)
                return "out"

            elif node_type == NodeType.SET_VARIABLE:
                self._set_variable(config, context)
                return "out"

            elif node_type == NodeType.CLOSE_CONVERSATION:
                await self._close_conversation(session, config, context)
                return "out"

            elif node_type == NodeType.AI_CLASSIFY:
                await self._ai_classify(config, context)
                return "out"

            elif node_type == NodeType.AI_RESPOND:
                return await self._ai_respond(session, config, context)

            elif node_type == NodeType.HTTP_REQUEST:
                return await self._http_request(config, context)

            elif node_type == NodeType.UPDATE_CUSTOMER:
                await self._update_customer(session, config, context)
                return "out"

            elif node_type == NodeType.CREATE_NOTE:
                await self._create_note(session, config, context)
                return "out"

            else:
                logger.warning(f"Unknown node type: {node_type}")
                return "out"

        except Exception as e:
            logger.error(f"Node execution error: {e}")
            return "error"

    def _substitute_variables(self, config: dict, variables: dict) -> dict:
        """Substitute {{variable}} placeholders in config."""
        def substitute(value: Any) -> Any:
            if isinstance(value, str):
                # Find all {{var}} patterns
                pattern = r"\{\{(\w+(?:\.\w+)*)\}\}"

                def replace(match):
                    var_path = match.group(1)
                    parts = var_path.split(".")
                    result = variables
                    for part in parts:
                        if isinstance(result, dict):
                            result = result.get(part, match.group(0))
                        else:
                            return match.group(0)
                    return str(result) if result is not None else ""

                return re.sub(pattern, replace, value)
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(v) for v in value]
            return value

        return substitute(config)

    async def _evaluate_condition(self, config: dict, context: ExecutionContext) -> bool:
        """Evaluate condition node."""
        field_path = config.get("field", "")
        operator = config.get("operator", "equals")
        expected_value = config.get("value", "")

        # Get actual value from variables
        parts = field_path.split(".")
        actual_value = context.variables
        for part in parts:
            if isinstance(actual_value, dict):
                actual_value = actual_value.get(part)
            else:
                actual_value = None
                break

        # Evaluate
        if operator == "equals":
            return str(actual_value) == str(expected_value)
        elif operator == "not_equals":
            return str(actual_value) != str(expected_value)
        elif operator == "contains":
            return str(expected_value) in str(actual_value or "")
        elif operator == "not_contains":
            return str(expected_value) not in str(actual_value or "")
        elif operator == "greater_than":
            try:
                return float(actual_value or 0) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual_value or 0) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "is_empty":
            return not actual_value
        elif operator == "is_not_empty":
            return bool(actual_value)
        elif operator == "matches_regex":
            try:
                return bool(re.match(expected_value, str(actual_value or "")))
            except re.error:
                return False

        return False

    async def _send_message(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ) -> str:
        """Send message to conversation."""
        if not context.conversation_id:
            return "error"

        message_text = config.get("message", "")
        if not message_text:
            return "error"

        # Create message
        from shared.models.conversation import Message, SenderType, ContentType

        message = Message(
            conversation_id=context.conversation_id,
            sender_type=SenderType.BOT,
            content_type=ContentType.TEXT,
            content={"text": message_text},
            metadata={"scenario_id": str(context.scenario_id)},
        )
        session.add(message)
        await session.commit()

        # Publish event
        publisher = get_publisher()
        await publisher.publish(
            EventType.MESSAGE_SENT,
            {
                "conversation_id": str(context.conversation_id),
                "message_id": str(message.id),
                "tenant_id": str(context.tenant_id),
            },
        )

        return "out"

    async def _send_email(self, config: dict, context: ExecutionContext) -> str:
        """Send email (queue for notification worker)."""
        import json
        import redis.asyncio as redis
        from shared.config import get_settings

        settings = get_settings()

        # Get customer email
        customer_email = context.variables.get("customer", {}).get("email")
        if not customer_email:
            return "error"

        email_data = {
            "to": customer_email,
            "subject": config.get("subject", ""),
            "body_text": config.get("body", ""),
            "body_html": config.get("body", ""),
        }

        # Queue for notification worker
        r = redis.from_url(settings.redis_url)
        await r.rpush("queue:notifications:email", json.dumps(email_data))
        await r.close()

        return "out"

    async def _assign_operator(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Assign conversation to operator."""
        if not context.conversation_id:
            return

        strategy = config.get("strategy", "round_robin")
        operator_id = config.get("operator_id")

        if strategy == "specific" and operator_id:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == context.conversation_id)
                .values(
                    assigned_to_id=UUID(operator_id),
                    status=ConversationStatus.ASSIGNED,
                )
            )
        else:
            # Let router worker handle assignment
            import json
            import redis.asyncio as redis
            from shared.config import get_settings

            settings = get_settings()
            r = redis.from_url(settings.redis_url)
            await r.publish(
                "events:conversation.new",
                json.dumps({
                    "conversation_id": str(context.conversation_id),
                    "tenant_id": str(context.tenant_id),
                }),
            )
            await r.close()

    async def _assign_department(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Assign conversation to department."""
        if not context.conversation_id:
            return

        department_id = config.get("department_id")
        if department_id:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == context.conversation_id)
                .values(department_id=UUID(department_id))
            )

    async def _add_tag(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Add tag to conversation."""
        if not context.conversation_id:
            return

        tag = config.get("tag")
        if not tag:
            return

        result = await session.execute(
            select(Conversation).where(Conversation.id == context.conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation:
            tags = list(conversation.tags or [])
            if tag not in tags:
                tags.append(tag)
                conversation.tags = tags

    async def _remove_tag(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Remove tag from conversation."""
        if not context.conversation_id:
            return

        tag = config.get("tag")
        if not tag:
            return

        result = await session.execute(
            select(Conversation).where(Conversation.id == context.conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation and conversation.tags:
            tags = [t for t in conversation.tags if t != tag]
            conversation.tags = tags

    async def _set_priority(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Set conversation priority."""
        if not context.conversation_id:
            return

        priority = config.get("priority")
        if priority:
            await session.execute(
                update(Conversation)
                .where(Conversation.id == context.conversation_id)
                .values(priority=ConversationPriority(priority))
            )

    def _set_variable(self, config: dict, context: ExecutionContext):
        """Set a variable in context."""
        name = config.get("variable_name")
        value = config.get("value")
        value_type = config.get("value_type", "string")

        if not name:
            return

        if value_type == "number":
            try:
                value = float(value)
            except (ValueError, TypeError):
                pass
        elif value_type == "boolean":
            value = value.lower() in ("true", "1", "yes")

        context.variables[name] = value

    async def _close_conversation(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Close conversation."""
        if not context.conversation_id:
            return

        await session.execute(
            update(Conversation)
            .where(Conversation.id == context.conversation_id)
            .values(
                status=ConversationStatus.CLOSED,
                closed_at=datetime.now(timezone.utc),
            )
        )

    async def _ai_classify(self, config: dict, context: ExecutionContext):
        """Classify message using AI."""
        categories = config.get("categories", [])
        output_var = config.get("output_variable", "classification")

        if not categories:
            return

        # Get last message text
        message_text = context.variables.get("trigger", {}).get("message_text", "")

        if message_text:
            result = await self.llm_service.classify_intent(message_text, categories)
            context.variables[output_var] = result

    async def _ai_respond(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ) -> str:
        """Generate AI response."""
        if not context.conversation_id:
            return "error"

        use_kb = config.get("use_knowledge_base", True)
        system_prompt = config.get("system_prompt", "")
        auto_send = config.get("auto_send", False)

        # Get message text
        message_text = context.variables.get("trigger", {}).get("message_text", "")

        if not message_text:
            return "error"

        # Get context from knowledge base
        kb_context = ""
        if use_kb:
            kb_context = await self.rag_service.retrieve_with_context(
                tenant_id=context.tenant_id,
                query=message_text,
                top_k=3,
            )

        # Generate response
        suggestions = await self.llm_service.generate_suggestions(
            customer_message=message_text,
            context=kb_context,
            num_suggestions=1,
        )

        if suggestions:
            response_text = suggestions[0]
            context.variables["ai_response"] = response_text

            if auto_send:
                return await self._send_message(
                    session,
                    {"message": response_text},
                    context,
                )

        return "out"

    async def _http_request(self, config: dict, context: ExecutionContext) -> str:
        """Make HTTP request."""
        method = config.get("method", "POST")
        url = config.get("url")
        headers = config.get("headers", {})
        body = config.get("body", "")
        output_var = config.get("output_variable")

        if not url:
            return "error"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=body if body else None,
                )

                if output_var:
                    try:
                        context.variables[output_var] = response.json()
                    except Exception:
                        context.variables[output_var] = response.text

                return "out" if response.status_code < 400 else "error"

        except Exception as e:
            logger.error(f"HTTP request error: {e}")
            return "error"

    async def _update_customer(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Update customer fields."""
        if not context.customer_id:
            return

        fields = config.get("fields", {})
        if not fields:
            return

        result = await session.execute(
            select(Customer).where(Customer.id == context.customer_id)
        )
        customer = result.scalar_one_or_none()

        if customer:
            for field_name, value in fields.items():
                if hasattr(customer, field_name):
                    setattr(customer, field_name, value)

    async def _create_note(
        self,
        session: AsyncSession,
        config: dict,
        context: ExecutionContext,
    ):
        """Create customer note."""
        if not context.customer_id:
            return

        content = config.get("content", "")
        if not content:
            return

        note = CustomerNote(
            customer_id=context.customer_id,
            content=content,
            metadata={"scenario_id": str(context.scenario_id)},
        )
        session.add(note)


# Singleton
_executor: ScenarioExecutor | None = None


def get_scenario_executor() -> ScenarioExecutor:
    """Get scenario executor singleton."""
    global _executor
    if _executor is None:
        _executor = ScenarioExecutor()
    return _executor
