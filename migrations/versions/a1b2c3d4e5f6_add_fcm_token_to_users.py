"""Add fcm_token to pacientes and psicologos

Revision ID: a1b2c3d4e5f6
Revises: 0bd35de4d198
Create Date: 2026-05-12 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '0bd35de4d198'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fcm_token', sa.Text(), nullable=True))

    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fcm_token', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.drop_column('fcm_token')

    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.drop_column('fcm_token')
