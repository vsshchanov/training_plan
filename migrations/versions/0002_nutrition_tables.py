"""add nutrition tables: profiles, days, meals, food_items

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'user_nutrition_profiles' not in existing_tables:
        op.create_table('user_nutrition_profiles',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('sex', sa.String(10), nullable=False),
            sa.Column('weight', sa.Float(), nullable=False),
            sa.Column('height', sa.Float(), nullable=False),
            sa.Column('age', sa.Integer(), nullable=False),
            sa.Column('activity_level', sa.Float(), nullable=False),
            sa.Column('goal', sa.String(20), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id'),
        )

    if 'nutrition_days' not in existing_tables:
        op.create_table('nutrition_days',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'date', name='uq_user_date'),
        )

    if 'meals' not in existing_tables:
        op.create_table('meals',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('nutrition_day_id', sa.String(36), nullable=False),
            sa.Column('meal_type', sa.String(20), nullable=False),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['nutrition_day_id'], ['nutrition_days.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'food_items' not in existing_tables:
        op.create_table('food_items',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('meal_id', sa.String(36), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('weight_grams', sa.Float(), nullable=False),
            sa.Column('calories_per_100g', sa.Float(), nullable=False),
            sa.Column('protein_per_100g', sa.Float(), nullable=False),
            sa.Column('fat_per_100g', sa.Float(), nullable=False),
            sa.Column('carbs_per_100g', sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(['meal_id'], ['meals.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    op.drop_table('food_items')
    op.drop_table('meals')
    op.drop_table('nutrition_days')
    op.drop_table('user_nutrition_profiles')
