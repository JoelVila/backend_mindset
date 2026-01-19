"""Add enhanced psychologist fields and reviews

Revision ID: enhanced_psychologist_profile
Revises: rename_pacientes_cols
Create Date: 2026-01-09 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enhanced_psychologist_profile'
down_revision = 'rename_pacientes_cols'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to psicologos table
    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('foto_perfil', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('verificado', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('anios_experiencia', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('precio_presencial', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('precio_online', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('precio_chat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('numero_cuenta', sa.String(34), nullable=True))
        batch_op.add_column(sa.Column('banco', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('titular_cuenta', sa.String(200), nullable=True))

    
    # Create resenas table
    op.create_table('resenas',
        sa.Column('id_resena', sa.Integer(), nullable=False),
        sa.Column('id_psicologo', sa.Integer(), nullable=False),
        sa.Column('id_paciente', sa.Integer(), nullable=False),
        sa.Column('puntuacion', sa.Integer(), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
        sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
        sa.PrimaryKeyConstraint('id_resena')
    )
    
    # Create psicologo_especialidad association table
    op.create_table('psicologo_especialidad',
        sa.Column('psicologo_id', sa.Integer(), nullable=False),
        sa.Column('especialidad_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['especialidad_id'], ['especialidades.id'], ),
        sa.ForeignKeyConstraint(['psicologo_id'], ['psicologos.id_psicologo'], ),
        sa.PrimaryKeyConstraint('psicologo_id', 'especialidad_id')
    )
    
    # Migrate existing especialidad_id to many-to-many relationship
    # This SQL will copy existing relationships to the new table
    op.execute("""
        INSERT INTO psicologo_especialidad (psicologo_id, especialidad_id)
        SELECT id_psicologo, especialidad_id 
        FROM psicologos 
        WHERE especialidad_id IS NOT NULL
    """)


def downgrade():
    # Drop association table
    op.drop_table('psicologo_especialidad')
    
    # Drop resenas table
    op.drop_table('resenas')
    
    # Remove new columns from psicologos
    with op.batch_alter_table('psicologos', schema=None) as batch_op:
        batch_op.drop_column('titular_cuenta')
        batch_op.drop_column('banco')
        batch_op.drop_column('numero_cuenta')
        batch_op.drop_column('precio_chat')
        batch_op.drop_column('precio_online')
        batch_op.drop_column('precio_presencial')
        batch_op.drop_column('anios_experiencia')
        batch_op.drop_column('verificado')
        batch_op.drop_column('bio')
        batch_op.drop_column('foto_perfil')
