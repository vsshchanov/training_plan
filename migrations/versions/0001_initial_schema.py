"""initial schema with all tables and new columns

Revision ID: 0001
Revises:
Create Date: 2026-06-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    existing_cols = {t: [c['name'] for c in inspector.get_columns(t)]
                     for t in existing_tables}

    # Таблица users
    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(50), nullable=False),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username'),
        )

    # Таблица workout_days
    if 'workout_days' not in existing_tables:
        op.create_table('workout_days',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        if 'notes' not in existing_cols.get('workout_days', []):
            op.add_column('workout_days', sa.Column('notes', sa.Text(), nullable=True))

    # Таблица exercises
    if 'exercises' not in existing_tables:
        op.create_table('exercises',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workout_day_id', sa.String(36), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        if 'order' not in existing_cols.get('exercises', []):
            op.add_column('exercises', sa.Column('order', sa.Integer(), nullable=False, server_default='0'))

    # Таблица exercise_sets
    if 'exercise_sets' not in existing_tables:
        op.create_table('exercise_sets',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('exercise_id', sa.String(36), nullable=False),
            sa.Column('reps', sa.Integer(), nullable=False),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('rest_time', sa.Integer(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    # Таблица workout_templates
    if 'workout_templates' not in existing_tables:
        op.create_table('workout_templates',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    # Таблица template_exercises
    if 'template_exercises' not in existing_tables:
        op.create_table('template_exercises',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('template_id', sa.String(36), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['template_id'], ['workout_templates.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    # Таблица template_sets
    if 'template_sets' not in existing_tables:
        op.create_table('template_sets',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('exercise_id', sa.String(36), nullable=False),
            sa.Column('reps', sa.Integer(), nullable=False),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('rest_time', sa.Integer(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['exercise_id'], ['template_exercises.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    op.drop_table('template_sets')
    op.drop_table('template_exercises')
    op.drop_table('workout_templates')
    op.drop_table('exercise_sets')
    op.drop_table('exercises')
    op.drop_table('workout_days')
    op.drop_table('users')
