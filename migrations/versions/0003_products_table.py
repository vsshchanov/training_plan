"""add products table for food catalog

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'products' not in existing_tables:
        op.create_table('products',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('calories', sa.Float(), nullable=False),
            sa.Column('protein', sa.Float(), nullable=False),
            sa.Column('fat', sa.Float(), nullable=False),
            sa.Column('carbs', sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    op.drop_table('products')
