"""add user_notes table (multiple named notes per user)

Revision ID: d94b2f6a1c73
Revises: a1f9c3d7e5b2
Create Date: 2026-07-27

Multiple separately-named notes per user, not a single scratchpad — same
list+detail interaction shape as chat_threads, so no unique constraint on
user_id (a user can have any number of notes).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "d94b2f6a1c73"
down_revision = "a1f9c3d7e5b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_notes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_notes")