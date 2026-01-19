"""Rename pacientes columns to English

Revision ID: rename_pacientes_cols
Revises: dbfd0e25a347
Create Date: 2026-01-09 15:57:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_pacientes_cols'
down_revision = 'dbfd0e25a347'
branch_labels = None
depends_on = None


def upgrade():
    # Rename columns in pacientes table
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.alter_column('correo_electronico',
                              new_column_name='email',
                              existing_type=sa.String(120),
                              existing_nullable=False)
        batch_op.alter_column('contrasena',
                              new_column_name='password_hash',
                              existing_type=sa.String(256),
                              existing_nullable=False)


def downgrade():
    # Revert column names in pacientes table
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.alter_column('email',
                              new_column_name='correo_electronico',
                              existing_type=sa.String(120),
                              existing_nullable=False)
        batch_op.alter_column('password_hash',
                              new_column_name='contrasena',
                              existing_type=sa.String(256),
                              existing_nullable=False)
