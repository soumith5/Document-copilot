"""resize document_chunks.embedding to 384 dims for local bge-small embeddings

Revision ID: f3a1c9d24e7b
Revises: adc8284f5b53
Create Date: 2026-07-16

No embedding rows exist yet (ingestion never got past the OpenAI billing
wall — see handoff notes), so this is a clean column swap rather than a
data migration. The HNSW index is dropped and recreated because it is
built against a specific vector dimension and cannot be altered in place.

If you later switch back to OpenAI's text-embedding-3-small (1536 dims),
write the mirror-image migration (drop this 384-dim column/index, recreate
at 1536) rather than trying to alter the existing one in place — vectors
from the two backends are not compatible, so this should always be a full
column swap + full re-ingestion, never a value-preserving ALTER.
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "f3a1c9d24e7b"
down_revision = "adc8284f5b53"  # <-- CONFIRM this matches your current head; see note below
branch_labels = None
depends_on = None

OLD_DIM = 1536
NEW_DIM = 384


def upgrade() -> None:
    op.drop_index("ix_document_chunks_embedding_hnsw", table_name="document_chunks")
    op.drop_column("document_chunks", "embedding")
    op.add_column(
        "document_chunks",
        sa.Column("embedding", Vector(NEW_DIM), nullable=True),
    )
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_embedding_hnsw", table_name="document_chunks")
    op.drop_column("document_chunks", "embedding")
    op.add_column(
        "document_chunks",
        sa.Column("embedding", Vector(OLD_DIM), nullable=True),
    )
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
