"""Update notifications inbox

Revision ID: e7f8g9h0i1j2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-13 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7f8g9h0i1j2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Modify id_paciente and id_psicologo to be nullable
    # Note: Using batch_op for SQLite compatibility if needed, but here it's likely MySQL
    with op.batch_alter_table('notificaciones', schema=None) as batch_op:
        batch_op.alter_column('id_paciente',
                   existing_type=sa.Integer(),
                   nullable=True)
        batch_op.alter_column('id_psicologo',
                   existing_type=sa.Integer(),
                   nullable=True)
        batch_op.add_column(sa.Column('titulo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tipo', sa.String(length=50), nullable=True, server_default='general'))

def downgrade():
    with op.batch_alter_table('notificaciones', schema=None) as batch_op:
        batch_op.drop_column('tipo')
        batch_op.drop_column('titulo')
        batch_op.alter_column('id_psicologo',
                   existing_type=sa.Integer(),
                   nullable=False)
        batch_op.alter_column('id_paciente',
                   existing_type=sa.Integer(),
                   nullable=False)
