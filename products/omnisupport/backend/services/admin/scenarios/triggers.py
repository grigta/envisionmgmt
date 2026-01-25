"""Trigger system for scenarios."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.scenario import Scenario, Trigger, TriggerType
from shared.models.conversation import Conversation
from shared.models.customer import Customer

from services.admin.scenarios.executor import get_scenario_executor

logger = logging.getLogger(__name__)


class TriggerEventType(str, Enum):
    """Types of trigger events."""

    # Conversation events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_ASSIGNED = "conversation.assigned"
    CONVERSATION_CLOSED = "conversation.closed"
    CONVERSATION_REOPENED = "conversation.reopened"

    # Message events
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"

    # Time-based
    SCHEDULE = "schedule"

    # Manual
    MANUAL = "manual"


@dataclass
class TriggerCondition:
    """Single trigger condition."""

    field: str
    operator: str  # equals, not_equals, contains, regex, etc.
    value: Any


class TriggerEvaluator:
    """Evaluates trigger conditions against event data."""

    def evaluate_condition(self, condition: dict, data: dict) -> bool:
        """Evaluate a single condition."""
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected = condition.get("value")

        # Get actual value from data (supports nested paths like "customer.email")
        actual = self._get_nested_value(data, field)

        return self._compare(actual, operator, expected)

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get value from nested dict using dot notation."""
        parts = path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values using operator."""
        if operator == "equals":
            return str(actual) == str(expected)
        elif operator == "not_equals":
            return str(actual) != str(expected)
        elif operator == "contains":
            return str(expected).lower() in str(actual or "").lower()
        elif operator == "not_contains":
            return str(expected).lower() not in str(actual or "").lower()
        elif operator == "starts_with":
            return str(actual or "").lower().startswith(str(expected).lower())
        elif operator == "ends_with":
            return str(actual or "").lower().endswith(str(expected).lower())
        elif operator == "regex":
            try:
                return bool(re.search(str(expected), str(actual or ""), re.IGNORECASE))
            except re.error:
                return False
        elif operator == "greater_than":
            try:
                return float(actual or 0) > float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual or 0) < float(expected)
            except (ValueError, TypeError):
                return False
        elif operator == "is_empty":
            return not actual
        elif operator == "is_not_empty":
            return bool(actual)
        elif operator == "in":
            if isinstance(expected, list):
                return actual in expected
            return str(actual) in str(expected).split(",")
        elif operator == "not_in":
            if isinstance(expected, list):
                return actual not in expected
            return str(actual) not in str(expected).split(",")

        return False

    def evaluate_all_conditions(
        self,
        conditions: list[dict],
        data: dict,
        logic: str = "and",
    ) -> bool:
        """
        Evaluate multiple conditions with AND/OR logic.

        logic: "and" - all must match, "or" - any must match
        """
        if not conditions:
            return True

        results = [self.evaluate_condition(c, data) for c in conditions]

        if logic == "or":
            return any(results)
        return all(results)


class TriggerService:
    """Service for managing and firing triggers."""

    def __init__(self):
        self.evaluator = TriggerEvaluator()
        self.executor = get_scenario_executor()

    async def fire_event(
        self,
        event_type: str,
        tenant_id: UUID,
        data: dict,
    ):
        """
        Fire an event and execute matching scenarios.

        Args:
            event_type: Event type (e.g., "message.received")
            tenant_id: Tenant ID
            data: Event data (conversation, customer, message info)
        """
        logger.info(f"Firing event: {event_type} for tenant {tenant_id}")

        async with get_session() as session:
            # Find active triggers for this event type
            result = await session.execute(
                select(Trigger)
                .join(Scenario)
                .where(
                    and_(
                        Trigger.tenant_id == tenant_id,
                        Trigger.event_type == event_type,
                        Trigger.is_active == True,
                        Scenario.is_active == True,
                    )
                )
            )
            triggers = list(result.scalars().all())

            logger.debug(f"Found {len(triggers)} triggers for event {event_type}")

            # Evaluate and execute matching triggers
            for trigger in triggers:
                if self._should_fire(trigger, data):
                    logger.info(f"Firing trigger {trigger.id} -> scenario {trigger.scenario_id}")

                    # Execute scenario asynchronously
                    try:
                        await self.executor.execute(
                            scenario_id=trigger.scenario_id,
                            trigger_event=event_type,
                            trigger_data=data,
                            tenant_id=tenant_id,
                        )
                    except Exception as e:
                        logger.error(f"Error executing scenario for trigger {trigger.id}: {e}")

    def _should_fire(self, trigger: Trigger, data: dict) -> bool:
        """Check if trigger conditions are met."""
        conditions = trigger.conditions or []

        if not conditions:
            return True

        logic = trigger.condition_logic or "and"
        return self.evaluator.evaluate_all_conditions(conditions, data, logic)

    async def fire_conversation_event(
        self,
        event_type: str,
        conversation_id: UUID,
        tenant_id: UUID,
        extra_data: dict | None = None,
    ):
        """Fire event with conversation data."""
        async with get_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                return

            # Build event data
            data = {
                "conversation_id": str(conversation_id),
                "conversation": {
                    "id": str(conversation.id),
                    "status": conversation.status.value,
                    "channel": conversation.channel.value,
                    "priority": conversation.priority.value,
                    "tags": conversation.tags or [],
                    "subject": conversation.subject,
                },
                "customer_id": str(conversation.customer_id) if conversation.customer_id else None,
                **(extra_data or {}),
            }

            # Get customer data
            if conversation.customer_id:
                cust_result = await session.execute(
                    select(Customer).where(Customer.id == conversation.customer_id)
                )
                customer = cust_result.scalar_one_or_none()

                if customer:
                    data["customer"] = {
                        "id": str(customer.id),
                        "email": customer.email,
                        "phone": customer.phone,
                        "name": customer.name,
                        "tags": customer.tags or [],
                    }

        await self.fire_event(event_type, tenant_id, data)

    async def fire_message_event(
        self,
        event_type: str,
        message_id: UUID,
        conversation_id: UUID,
        tenant_id: UUID,
        message_text: str,
    ):
        """Fire message event."""
        async with get_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                return

            data = {
                "message_id": str(message_id),
                "message_text": message_text,
                "conversation_id": str(conversation_id),
                "conversation": {
                    "id": str(conversation.id),
                    "status": conversation.status.value,
                    "channel": conversation.channel.value,
                    "priority": conversation.priority.value,
                    "tags": conversation.tags or [],
                },
                "customer_id": str(conversation.customer_id) if conversation.customer_id else None,
            }

            # Get customer
            if conversation.customer_id:
                cust_result = await session.execute(
                    select(Customer).where(Customer.id == conversation.customer_id)
                )
                customer = cust_result.scalar_one_or_none()

                if customer:
                    data["customer"] = {
                        "id": str(customer.id),
                        "email": customer.email,
                        "phone": customer.phone,
                        "name": customer.name,
                    }

        await self.fire_event(event_type, tenant_id, data)


# Singleton
_trigger_service: TriggerService | None = None


def get_trigger_service() -> TriggerService:
    """Get trigger service singleton."""
    global _trigger_service
    if _trigger_service is None:
        _trigger_service = TriggerService()
    return _trigger_service
