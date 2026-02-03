"""fix_psicologos_add_precio_telefono

Revision ID: 93d9214fd848
Revises: 29862f56de33
Create Date: 2026-02-02 21:30:27.257854

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93d9214fd848'
down_revision = '29862f56de33'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('precio_telefono', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.drop_column('precio_chat')

def downgrade():
    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('precio_chat', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.drop_column('precio_telefono')
