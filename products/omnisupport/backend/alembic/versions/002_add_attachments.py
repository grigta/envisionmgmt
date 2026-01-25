"""Add attachments table.

Revision ID: 002_add_attachments
Revises: 001_initial_schema
Create Date: 2026-01-24 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_attachments'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE attachmenttype AS ENUM ('image', 'document', 'audio', 'video')")
    op.execute("CREATE TYPE attachmentstatus AS ENUM ('pending', 'attached', 'orphaned', 'deleted')")

    # Attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Owner
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL')),

        # Message relationship
        sa.Column('message_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('messages.id', ondelete='SET NULL')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('conversations.id', ondelete='SET NULL')),

        # File info
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(255), nullable=False),
        sa.Column('size', sa.Integer, nullable=False),

        # Storage
        sa.Column('storage_key', sa.String(1000), nullable=False, unique=True),
        sa.Column('storage_url', sa.Text),
        sa.Column('checksum', sa.String(64)),

        # Type
        sa.Column('attachment_type',
                  postgresql.ENUM('image', 'document', 'audio', 'video', name='attachmenttype', create_type=False),
                  nullable=False),

        # Image-specific
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('thumbnail_key', sa.String(1000)),

        # Status
        sa.Column('status',
                  postgresql.ENUM('pending', 'attached', 'orphaned', 'deleted', name='attachmentstatus', create_type=False),
                  server_default='pending', nullable=False),

        # Timestamps
        sa.Column('attached_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),

        # Soft delete
        sa.Column('is_deleted', sa.Boolean, server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    # Indexes
    op.create_index('ix_attachments_tenant_id', 'attachments', ['tenant_id'])
    op.create_index('ix_attachments_uploaded_by_id', 'attachments', ['uploaded_by_id'])
    op.create_index('ix_attachments_message_id', 'attachments', ['message_id'])
    op.create_index('ix_attachments_conversation_id', 'attachments', ['conversation_id'])
    op.create_index('ix_attachments_status', 'attachments', ['status'])
    op.create_index('ix_attachments_storage_key', 'attachments', ['storage_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_attachments_storage_key')
    op.drop_index('ix_attachments_status')
    op.drop_index('ix_attachments_conversation_id')
    op.drop_index('ix_attachments_message_id')
    op.drop_index('ix_attachments_uploaded_by_id')
    op.drop_index('ix_attachments_tenant_id')
    op.drop_table('attachments')

    op.execute("DROP TYPE attachmentstatus")
    op.execute("DROP TYPE attachmenttype")
