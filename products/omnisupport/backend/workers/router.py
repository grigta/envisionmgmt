"""Conversation routing worker.

Handles automatic assignment of conversations to operators
based on routing rules (round-robin, skill-based, load balancing).
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.conversation import Conversation, ConversationStatus
from shared.models.user import User
from shared.models.skill import Skill, UserSkill
from shared.models.department import DepartmentMember
from shared.events.types import EventType
from shared.events.publisher import get_publisher

from workers.base import BaseWorker

logger = logging.getLogger(__name__)


class RouterWorker(BaseWorker):
    """Worker for routing conversations to operators."""

    name = "router_worker"

    async def process(self):
        """Main processing loop."""
        # Subscribe to new conversation events
        await self.subscribe_to_channel("events:conversation.new", self.handle_new_conversation)

    async def handle_new_conversation(self, data: bytes):
        """Handle new conversation event."""
        try:
            event = json.loads(data)
            conversation_id = event.get("conversation_id")
            tenant_id = event.get("tenant_id")

            if not conversation_id or not tenant_id:
                return

            async with get_session() as session:
                await self.route_conversation(
                    session,
                    UUID(conversation_id),
                    UUID(tenant_id),
                )

        except Exception as e:
            logger.error(f"Error routing conversation: {e}", exc_info=True)

    async def route_conversation(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        tenant_id: UUID,
    ):
        """Route conversation to an available operator."""
        # Get conversation
        result = await session.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == tenant_id,
                    Conversation.status == ConversationStatus.PENDING,
                )
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            logger.debug(f"Conversation {conversation_id} not found or not pending")
            return

        # Find available operator
        operator = await self.find_available_operator(
            session,
            tenant_id,
            conversation.department_id,
            conversation.required_skills or [],
        )

        if operator:
            conversation.assigned_to_id = operator.id
            conversation.status = ConversationStatus.ASSIGNED
            conversation.assigned_at = datetime.now(timezone.utc)
            await session.commit()

            # Publish assignment event
            publisher = get_publisher()
            await publisher.publish(
                EventType.CONVERSATION_ASSIGNED,
                {
                    "conversation_id": str(conversation_id),
                    "tenant_id": str(tenant_id),
                    "operator_id": str(operator.id),
                },
            )

            logger.info(f"Conversation {conversation_id} assigned to {operator.id}")
        else:
            logger.info(f"No available operator for conversation {conversation_id}")

    async def find_available_operator(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None,
        required_skills: list[str],
    ) -> User | None:
        """Find an available operator using round-robin with skill matching."""
        # Build query for online operators
        query = (
            select(User)
            .where(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_active == True,
                    User.is_online == True,
                )
            )
        )

        # Filter by department if specified
        if department_id:
            query = query.join(DepartmentMember).where(
                DepartmentMember.department_id == department_id
            )

        result = await session.execute(query)
        candidates = result.scalars().all()

        if not candidates:
            return None

        # Filter by skills if required
        if required_skills:
            skilled_candidates = []
            for candidate in candidates:
                user_skills = await session.execute(
                    select(Skill.name)
                    .join(UserSkill)
                    .where(UserSkill.user_id == candidate.id)
                )
                user_skill_names = {s for s in user_skills.scalars().all()}

                if all(skill in user_skill_names for skill in required_skills):
                    skilled_candidates.append(candidate)

            candidates = skilled_candidates

        if not candidates:
            return None

        # Round-robin: select operator with least active conversations
        operator_loads = []
        for candidate in candidates:
            count_result = await session.execute(
                select(func.count(Conversation.id)).where(
                    and_(
                        Conversation.assigned_to_id == candidate.id,
                        Conversation.status.in_([
                            ConversationStatus.ASSIGNED,
                            ConversationStatus.ACTIVE,
                        ]),
                    )
                )
            )
            load = count_result.scalar() or 0
            operator_loads.append((candidate, load))

        # Sort by load and return least loaded operator
        operator_loads.sort(key=lambda x: x[1])
        return operator_loads[0][0]


async def main():
    """Run router worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = RouterWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
