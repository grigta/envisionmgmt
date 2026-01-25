"""Initial schema with all models.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-20 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tenants
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('domain', sa.String(255)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('subscription_plan', sa.String(50)),
        sa.Column('subscription_status', sa.String(50)),
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])

    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('phone', sa.String(50)),
        sa.Column('role', sa.String(50), nullable=False, server_default='operator'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_verified', sa.Boolean, server_default='false'),
        sa.Column('last_seen_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(50), server_default='offline'),
        sa.Column('two_factor_enabled', sa.Boolean, server_default='false'),
        sa.Column('two_factor_secret', sa.String(100)),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_user_email_per_tenant'),
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Departments
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    op.create_index('ix_departments_tenant_id', 'departments', ['tenant_id'])

    # Customers
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('name', sa.String(255)),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('notes', sa.Text),
        sa.Column('last_seen_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_customers_tenant_id', 'customers', ['tenant_id'])
    op.create_index('ix_customers_email', 'customers', ['email'])
    op.create_index('ix_customers_phone', 'customers', ['phone'])

    # Customer identities
    op.create_table(
        'customer_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.UniqueConstraint('channel', 'external_id', name='uq_customer_identity'),
    )
    op.create_index('ix_customer_identities_customer_id', 'customer_identities', ['customer_id'])

    # Channels
    op.create_table(
        'channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('config', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('credentials', postgresql.JSONB, server_default='{}'),
    )
    op.create_index('ix_channels_tenant_id', 'channels', ['tenant_id'])

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='SET NULL')),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL')),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('channels.id', ondelete='SET NULL')),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(50), server_default='normal'),
        sa.Column('subject', sa.String(500)),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('external_id', sa.String(255)),
        sa.Column('first_response_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('last_message_at', sa.DateTime(timezone=True)),
        sa.Column('unread_count', sa.Integer, server_default='0'),
    )
    op.create_index('ix_conversations_tenant_id', 'conversations', ['tenant_id'])
    op.create_index('ix_conversations_customer_id', 'conversations', ['customer_id'])
    op.create_index('ix_conversations_assigned_to', 'conversations', ['assigned_to'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_channel', 'conversations', ['channel'])

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(50), server_default='text'),
        sa.Column('attachments', postgresql.JSONB, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('is_internal', sa.Boolean, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('external_id', sa.String(255)),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])

    # Canned responses
    op.create_table(
        'canned_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('shortcut', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('is_shared', sa.Boolean, server_default='true'),
        sa.UniqueConstraint('tenant_id', 'shortcut', name='uq_canned_response_shortcut'),
    )
    op.create_index('ix_canned_responses_tenant_id', 'canned_responses', ['tenant_id'])

    # Scenarios
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(7)),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('is_template', sa.Boolean, server_default='false'),
        sa.Column('template_category', sa.String(100)),
        sa.Column('nodes', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('edges', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('variables', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='false'),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('published_version', sa.Integer),
        sa.Column('executions_count', sa.Integer, server_default='0'),
        sa.Column('successful_executions', sa.Integer, server_default='0'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_scenario_tenant_name'),
    )
    op.create_index('ix_scenarios_tenant_id', 'scenarios', ['tenant_id'])

    # Triggers
    op.create_table(
        'triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(100)),
        sa.Column('conditions', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('condition_logic', sa.String(10), server_default='and'),
        sa.Column('config', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('channel_filter', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('priority', sa.Integer, server_default='0'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    op.create_index('ix_triggers_tenant_id', 'triggers', ['tenant_id'])
    op.create_index('ix_triggers_scenario_id', 'triggers', ['scenario_id'])
    op.create_index('ix_triggers_event_type', 'triggers', ['event_type'])

    # Scenario executions
    op.create_table(
        'scenario_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('trigger_event', sa.String(100)),
        sa.Column('trigger_data', postgresql.JSONB, server_default='{}'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('result', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('execution_log', postgresql.JSONB),
    )
    op.create_index('ix_scenario_executions_tenant_id', 'scenario_executions', ['tenant_id'])
    op.create_index('ix_scenario_executions_scenario_id', 'scenario_executions', ['scenario_id'])

    # Scenario variables
    op.create_table(
        'scenario_variables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('var_type', sa.String(50), nullable=False),
        sa.Column('default_value', postgresql.JSONB),
        sa.Column('required', sa.Boolean, server_default='false'),
        sa.Column('validation', postgresql.JSONB),
        sa.UniqueConstraint('scenario_id', 'name', name='uq_scenario_variable_name'),
    )
    op.create_index('ix_scenario_variables_scenario_id', 'scenario_variables', ['scenario_id'])

    # Knowledge documents
    op.create_table(
        'knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_url', sa.String(1000)),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_type', sa.String(50)),
        sa.Column('content', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('indexed_at', sa.DateTime(timezone=True)),
        sa.Column('chunks_count', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text),
    )
    op.create_index('ix_knowledge_documents_tenant_id', 'knowledge_documents', ['tenant_id'])

    # Knowledge chunks
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('token_count', sa.Integer),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('vector_id', sa.String(100)),
    )
    op.create_index('ix_knowledge_chunks_document_id', 'knowledge_chunks', ['document_id'])

    # Crawler configs
    op.create_table(
        'crawler_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('base_url', sa.String(1000), nullable=False),
        sa.Column('max_depth', sa.Integer, server_default='3'),
        sa.Column('max_pages', sa.Integer, server_default='100'),
        sa.Column('include_patterns', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('exclude_patterns', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('schedule', sa.String(100)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(timezone=True)),
        sa.Column('pages_crawled', sa.Integer, server_default='0'),
    )
    op.create_index('ix_crawler_configs_tenant_id', 'crawler_configs', ['tenant_id'])

    # API keys
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    op.create_index('ix_api_keys_tenant_id', 'api_keys', ['tenant_id'])
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])

    # Webhooks
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('secret', sa.String(255)),
        sa.Column('events', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('headers', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True)),
        sa.Column('failure_count', sa.Integer, server_default='0'),
    )
    op.create_index('ix_webhooks_tenant_id', 'webhooks', ['tenant_id'])

    # Webhook deliveries
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB, nullable=False),
        sa.Column('response_status', sa.Integer),
        sa.Column('response_body', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('error_message', sa.Text),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])

    # Analytics snapshots
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('conversations_total', sa.Integer, server_default='0'),
        sa.Column('conversations_new', sa.Integer, server_default='0'),
        sa.Column('conversations_resolved', sa.Integer, server_default='0'),
        sa.Column('conversations_closed', sa.Integer, server_default='0'),
        sa.Column('messages_total', sa.Integer, server_default='0'),
        sa.Column('messages_inbound', sa.Integer, server_default='0'),
        sa.Column('messages_outbound', sa.Integer, server_default='0'),
        sa.Column('avg_first_response_time', sa.Integer),
        sa.Column('avg_resolution_time', sa.Integer),
        sa.Column('median_first_response_time', sa.Integer),
        sa.Column('median_resolution_time', sa.Integer),
        sa.Column('customers_active', sa.Integer, server_default='0'),
        sa.Column('customers_new', sa.Integer, server_default='0'),
        sa.Column('csat_responses', sa.Integer, server_default='0'),
        sa.Column('csat_score_avg', sa.Float),
        sa.Column('csat_score_distribution', postgresql.JSONB, server_default='{}'),
        sa.Column('channel_metrics', postgresql.JSONB, server_default='{}'),
        sa.Column('operator_metrics', postgresql.JSONB, server_default='{}'),
        sa.Column('ai_suggestions_total', sa.Integer, server_default='0'),
        sa.Column('ai_suggestions_accepted', sa.Integer, server_default='0'),
        sa.Column('ai_suggestions_modified', sa.Integer, server_default='0'),
        sa.Column('tag_metrics', postgresql.JSONB, server_default='{}'),
    )
    op.create_index('ix_analytics_snapshots_tenant_id', 'analytics_snapshots', ['tenant_id'])
    op.create_index('ix_analytics_snapshots_period_start', 'analytics_snapshots', ['period_start'])

    # Reports
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('date_from', sa.Date, nullable=False),
        sa.Column('date_to', sa.Date, nullable=False),
        sa.Column('filters', postgresql.JSONB, server_default='{}'),
        sa.Column('config', postgresql.JSONB, server_default='{}'),
        sa.Column('data', postgresql.JSONB),
        sa.Column('export_format', sa.String(50)),
        sa.Column('export_url', sa.String(500)),
        sa.Column('exported_at', sa.DateTime(timezone=True)),
        sa.Column('is_scheduled', sa.Boolean, server_default='false'),
        sa.Column('schedule_cron', sa.String(100)),
        sa.Column('schedule_recipients', postgresql.JSONB, server_default='[]'),
    )
    op.create_index('ix_reports_tenant_id', 'reports', ['tenant_id'])

    # ==================== Billing ====================

    # Plans
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('price_monthly', sa.Integer, nullable=False),
        sa.Column('price_yearly', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), server_default='RUB'),
        sa.Column('features', postgresql.JSONB, server_default='[]'),
        sa.Column('limits', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_featured', sa.Boolean, server_default='false'),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('trial_days', sa.Integer, server_default='14'),
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plans.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(50), server_default='trialing'),
        sa.Column('billing_period', sa.String(50), server_default='monthly'),
        sa.Column('trial_start', sa.Date),
        sa.Column('trial_end', sa.Date),
        sa.Column('current_period_start', sa.Date, nullable=False),
        sa.Column('current_period_end', sa.Date, nullable=False),
        sa.Column('canceled_at', sa.DateTime(timezone=True)),
        sa.Column('cancel_at_period_end', sa.Boolean, server_default='false'),
        sa.Column('external_subscription_id', sa.String(255)),
    )
    op.create_index('ix_subscriptions_tenant_id', 'subscriptions', ['tenant_id'])
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'])

    # Invoices
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('number', sa.String(50), nullable=False, unique=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('subtotal', sa.Integer, nullable=False),
        sa.Column('tax', sa.Integer, server_default='0'),
        sa.Column('discount', sa.Integer, server_default='0'),
        sa.Column('total', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), server_default='RUB'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('items', postgresql.JSONB, server_default='[]'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('payment_reference', sa.String(255)),
        sa.Column('pdf_url', sa.String(500)),
    )
    op.create_index('ix_invoices_subscription_id', 'invoices', ['subscription_id'])
    op.create_index('ix_invoices_number', 'invoices', ['number'])

    # Usage records
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('usage_type', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('limit', sa.Integer),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    op.create_index('ix_usage_records_tenant_id', 'usage_records', ['tenant_id'])
    op.create_index('ix_usage_records_period_start', 'usage_records', ['period_start'])

    # Payment methods
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('card_brand', sa.String(50)),
        sa.Column('card_last4', sa.String(4)),
        sa.Column('card_exp_month', sa.Integer),
        sa.Column('card_exp_year', sa.Integer),
        sa.Column('bank_name', sa.String(255)),
        sa.Column('external_id', sa.String(255)),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    op.create_index('ix_payment_methods_tenant_id', 'payment_methods', ['tenant_id'])

    # AI interactions (for usage tracking)
    op.create_table(
        'ai_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100)),
        sa.Column('prompt', sa.Text),
        sa.Column('response', sa.Text),
        sa.Column('input_tokens', sa.Integer),
        sa.Column('output_tokens', sa.Integer),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('status', sa.String(50), server_default='completed'),
        sa.Column('feedback', sa.String(50)),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
    )
    op.create_index('ix_ai_interactions_tenant_id', 'ai_interactions', ['tenant_id'])
    op.create_index('ix_ai_interactions_created_at', 'ai_interactions', ['created_at'])


def downgrade() -> None:
    # Billing
    op.drop_table('ai_interactions')
    op.drop_table('payment_methods')
    op.drop_table('usage_records')
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    # Reports & Analytics
    op.drop_table('reports')
    op.drop_table('analytics_snapshots')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
    op.drop_table('api_keys')
    op.drop_table('crawler_configs')
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('scenario_variables')
    op.drop_table('scenario_executions')
    op.drop_table('triggers')
    op.drop_table('scenarios')
    op.drop_table('canned_responses')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('channels')
    op.drop_table('customer_identities')
    op.drop_table('customers')
    op.drop_table('departments')
    op.drop_table('users')
    op.drop_table('tenants')
