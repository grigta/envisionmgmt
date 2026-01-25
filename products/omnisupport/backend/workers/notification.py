"""Notification worker.

Handles sending notifications via various channels:
- Email (SMTP)
- Push notifications
- In-app notifications
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import get_session
from shared.models.user import User
from shared.models.tenant import Tenant

from workers.base import BaseWorker

logger = logging.getLogger(__name__)
settings = get_settings()

QUEUE_EMAIL = "queue:notifications:email"
QUEUE_PUSH = "queue:notifications:push"


class NotificationWorker(BaseWorker):
    """Worker for sending notifications."""

    name = "notification_worker"

    async def process(self):
        """Main processing loop - handle multiple notification queues."""
        tasks = [
            asyncio.create_task(self.process_email_queue()),
            asyncio.create_task(self.process_push_queue()),
        ]
        self._tasks.extend(tasks)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_email_queue(self):
        """Process email notification queue."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_EMAIL, timeout=5)
                if item:
                    await self.send_email(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing email: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def process_push_queue(self):
        """Process push notification queue."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_PUSH, timeout=5)
                if item:
                    await self.send_push(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing push: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def send_email(self, item: dict):
        """Send email notification."""
        to_email = item.get("to")
        subject = item.get("subject")
        body_html = item.get("body_html")
        body_text = item.get("body_text")
        template = item.get("template")
        template_data = item.get("template_data", {})

        if not to_email or not subject:
            logger.warning("Email missing required fields")
            return

        # Render template if provided
        if template:
            body_html, body_text = await self.render_email_template(
                template, template_data
            )

        if not body_html and not body_text:
            logger.warning("Email has no body")
            return

        # Build message
        message = MIMEMultipart("alternative")
        message["From"] = settings.smtp_from or settings.smtp_user
        message["To"] = to_email
        message["Subject"] = subject

        if body_text:
            message.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            message.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=settings.smtp_tls,
                start_tls=not settings.smtp_tls,
            )
            logger.info(f"Email sent to {to_email}: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            # Could implement retry logic here

    async def render_email_template(
        self, template: str, data: dict
    ) -> tuple[str, str]:
        """Render email template with data."""
        templates = {
            "welcome": {
                "html": """
                <h1>Добро пожаловать в OmniSupport!</h1>
                <p>Здравствуйте, {name}!</p>
                <p>Ваш аккаунт успешно создан.</p>
                """,
                "text": "Добро пожаловать в OmniSupport!\n\nЗдравствуйте, {name}!\nВаш аккаунт успешно создан.",
            },
            "verify_email": {
                "html": """
                <h1>Подтвердите email</h1>
                <p>Перейдите по ссылке для подтверждения:</p>
                <p><a href="{link}">{link}</a></p>
                """,
                "text": "Подтвердите email\n\nПерейдите по ссылке:\n{link}",
            },
            "reset_password": {
                "html": """
                <h1>Сброс пароля</h1>
                <p>Вы запросили сброс пароля.</p>
                <p><a href="{link}">Нажмите для сброса</a></p>
                <p>Если вы не запрашивали сброс, проигнорируйте это письмо.</p>
                """,
                "text": "Сброс пароля\n\nПерейдите по ссылке:\n{link}\n\nЕсли вы не запрашивали сброс, проигнорируйте это письмо.",
            },
            "invite": {
                "html": """
                <h1>Приглашение в команду</h1>
                <p>{inviter_name} приглашает вас в команду {team_name}.</p>
                <p><a href="{link}">Принять приглашение</a></p>
                """,
                "text": "{inviter_name} приглашает вас в команду {team_name}.\n\nПринять: {link}",
            },
            "new_conversation": {
                "html": """
                <h1>Новый диалог</h1>
                <p>Вам назначен новый диалог от {customer_name}.</p>
                <p><a href="{link}">Перейти к диалогу</a></p>
                """,
                "text": "Новый диалог от {customer_name}.\n\nПерейти: {link}",
            },
        }

        tmpl = templates.get(template)
        if not tmpl:
            logger.warning(f"Unknown email template: {template}")
            return "", ""

        html = tmpl["html"].format(**data) if tmpl.get("html") else ""
        text = tmpl["text"].format(**data) if tmpl.get("text") else ""

        return html, text

    async def send_push(self, item: dict):
        """Send push notification."""
        user_id = item.get("user_id")
        title = item.get("title")
        body = item.get("body")
        data = item.get("data", {})

        if not user_id or not title:
            logger.warning("Push notification missing required fields")
            return

        # Get user's push tokens
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()

            if not user or not user.push_tokens:
                logger.debug(f"No push tokens for user {user_id}")
                return

            # Send to each token
            for token_info in user.push_tokens:
                platform = token_info.get("platform")
                token = token_info.get("token")

                if platform == "fcm":
                    await self.send_fcm(token, title, body, data)
                elif platform == "apns":
                    await self.send_apns(token, title, body, data)
                elif platform == "web":
                    await self.send_web_push(token_info, title, body, data)

    async def send_fcm(
        self, token: str, title: str, body: str, data: dict
    ):
        """Send Firebase Cloud Messaging notification."""
        # Placeholder - implement with firebase-admin SDK
        logger.info(f"FCM notification: {title} (token: {token[:20]}...)")

    async def send_apns(
        self, token: str, title: str, body: str, data: dict
    ):
        """Send Apple Push Notification."""
        # Placeholder - implement with aioapns
        logger.info(f"APNS notification: {title} (token: {token[:20]}...)")

    async def send_web_push(
        self, subscription: dict, title: str, body: str, data: dict
    ):
        """Send Web Push notification."""
        # Placeholder - implement with pywebpush
        logger.info(f"Web Push notification: {title}")


async def main():
    """Run notification worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = NotificationWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
