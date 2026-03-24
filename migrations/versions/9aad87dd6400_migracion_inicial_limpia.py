"""Migracion inicial limpia

Revision ID: 9aad87dd6400
Revises: 
Create Date: 2026-02-03 16:44:54.425177

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9aad87dd6400'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 0. Clean previous failed states (Don't drop alembic_version)
    op.execute('DROP TABLE IF EXISTS psicologo_especialidad, citas, pacientes, psicologos, administrador, especialidades, anamnesis, notas_sesion, informes, facturas, notificaciones, tareas_informes, consentimientos_informados, resenas')
    
    # 1. Tables with no foreign keys
    op.create_table('especialidades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    
    op.create_table('administrador',
    sa.Column('id_admin', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('contrasena_hash', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id_admin'),
    sa.UniqueConstraint('email')
    )

    # 2. Base tables (Psicologos, Pacientes)
    op.create_table('psicologos',
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('correo_electronico', sa.String(length=120), nullable=False),
    sa.Column('verificado', sa.Boolean(), nullable=True),
    sa.Column('contrasena_hash', sa.String(length=256), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('apellido', sa.String(length=100), nullable=True),
    sa.Column('dni_nif', sa.String(length=20), nullable=True),
    sa.Column('direccion_fiscal', sa.String(length=255), nullable=True),
    sa.Column('numero_colegiado', sa.String(length=50), nullable=True),
    sa.Column('telefono', sa.String(length=20), nullable=True),
    sa.Column('foto_psicologo', sa.Text(length=4294967295), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('anios_experiencia', sa.Integer(), nullable=True),
    sa.Column('precio_online', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('cuenta_bancaria', sa.String(length=200), nullable=True),
    sa.Column('banco', sa.String(length=100), nullable=True),
    sa.Column('titular_cuenta', sa.String(length=200), nullable=True),
    sa.Column('reset_token', sa.String(length=255), nullable=True),
    sa.Column('reset_token_expiry', sa.DateTime(), nullable=True),
    sa.Column('horario_json', sa.Text(), nullable=True),
    sa.Column('max_pacientes_dia', sa.Integer(), nullable=True),
    sa.Column('onboarding_completado', sa.Boolean(), nullable=True),
    sa.Column('video_presentacion_url', sa.String(length=500), nullable=True),
    sa.Column('ofrece_sesion_intro', sa.Boolean(), nullable=True),
    sa.Column('precio_sesion_intro', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.PrimaryKeyConstraint('id_psicologo'),
    sa.UniqueConstraint('correo_electronico')
    )

    op.create_table('pacientes',
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('correo_electronico', sa.String(length=120), nullable=False),
    sa.Column('contrasena_hash', sa.String(length=256), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('apellido', sa.String(length=100), nullable=False),
    sa.Column('telefono', sa.String(length=20), nullable=False),
    sa.Column('dni_nif', sa.String(length=20), nullable=False),
    sa.Column('direccion_fiscal', sa.String(length=255), nullable=True),
    sa.Column('foto_paciente', sa.Text(length=4294967295), nullable=True),
    sa.Column('token_pago', sa.String(length=255), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=False),
    sa.Column('edad', sa.Integer(), nullable=False),
    sa.Column('reset_token', sa.String(length=255), nullable=True),
    sa.Column('reset_token_expiry', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id_paciente'),
    sa.UniqueConstraint('correo_electronico')
    )

    # 3. Tables depending on base tables (Citas, Psicologo_Especialidad)
    op.create_table('psicologo_especialidad',
    sa.Column('psicologo_id', sa.Integer(), nullable=False),
    sa.Column('especialidad_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['especialidad_id'], ['especialidades.id'], ),
    sa.ForeignKeyConstraint(['psicologo_id'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('psicologo_id', 'especialidad_id')
    )

    op.create_table('citas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('id_especialidad', sa.Integer(), nullable=True),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('hora', sa.Time(), nullable=False),
    sa.Column('tipo_cita', sa.String(length=50), nullable=True),
    sa.Column('motivo', sa.String(length=255), nullable=True),
    sa.Column('motivo_orientativo', sa.Text(), nullable=True),
    sa.Column('es_primera_vez', sa.Boolean(), nullable=True),
    sa.Column('is_urgente', sa.Boolean(), nullable=True),
    sa.Column('estado', sa.String(length=20), nullable=True),
    sa.Column('precio_cita', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('enlace_meet', sa.String(length=500), nullable=True),
    sa.Column('google_calendar_event_id', sa.String(length=255), nullable=True),
    sa.Column('stripe_session_id', sa.String(length=255), nullable=True),
    sa.Column('motivo_cancelacion', sa.Text(), nullable=True),
    sa.Column('documentacion_cancelacion', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['id_especialidad'], ['especialidades.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # 4. Tables depending on Citas (Anamnesis, Notas, Informes, Facturas, Notificaciones, Resenas)
    op.create_table('anamnesis',
    sa.Column('id_anamnesis', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=True),
    sa.Column('antecedentes', sa.Text(), nullable=True),
    sa.Column('motivo_consulta', sa.Text(), nullable=True),
    sa.Column('alergias', sa.Text(), nullable=True),
    sa.Column('fecha_alta', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.PrimaryKeyConstraint('id_anamnesis'),
    sa.UniqueConstraint('id_paciente')
    )

    op.create_table('notas_sesion',
    sa.Column('id_nota', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=False),
    sa.Column('tipo_nota', sa.String(length=50), nullable=True),
    sa.Column('contenido', sa.Text(), nullable=True),
    sa.Column('fecha', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.PrimaryKeyConstraint('id_nota')
    )

    op.create_table('informes',
    sa.Column('id_informe', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=True),
    sa.Column('titulo_informe', sa.String(length=255), nullable=True),
    sa.Column('texto_informe', sa.Text(), nullable=True),
    sa.Column('diagnostico', sa.Text(), nullable=True),
    sa.Column('tratamiento', sa.Text(), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
    sa.Column('fecha_modificacion', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id_informe')
    )

    op.create_table('tareas_informes',
    sa.Column('id_tarea', sa.Integer(), nullable=False),
    sa.Column('id_informe', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=False),
    sa.Column('completada', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['id_informe'], ['informes.id_informe'], ),
    sa.PrimaryKeyConstraint('id_tarea')
    )

    op.create_table('facturas',
    sa.Column('id_factura', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=True),
    sa.Column('numero_factura', sa.String(length=50), nullable=True),
    sa.Column('fecha_emision', sa.Date(), nullable=True),
    sa.Column('base_imponible', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('iva', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('importe_total', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('estado', sa.String(length=20), nullable=True),
    sa.Column('concepto', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id_factura'),
    sa.UniqueConstraint('numero_factura')
    )

    op.create_table('notificaciones',
    sa.Column('id_notificacion', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=True),
    sa.Column('mensaje', sa.Text(), nullable=True),
    sa.Column('fecha_envio', sa.DateTime(), nullable=True),
    sa.Column('leido', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id_notificacion')
    )

    op.create_table('consentimientos_informados',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('fecha_aceptacion', sa.DateTime(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('version_documento', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id_paciente', 'id_psicologo', name='uq_consentimiento_paciente_psicologo')
    )

    op.create_table('resenas',
    sa.Column('id_resena', sa.Integer(), nullable=False),
    sa.Column('id_paciente', sa.Integer(), nullable=False),
    sa.Column('id_psicologo', sa.Integer(), nullable=False),
    sa.Column('id_cita', sa.Integer(), nullable=True),
    sa.Column('puntuacion', sa.Integer(), nullable=False),
    sa.Column('comentario', sa.Text(), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_cita'], ['citas.id'], ),
    sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ),
    sa.ForeignKeyConstraint(['id_psicologo'], ['psicologos.id_psicologo'], ),
    sa.PrimaryKeyConstraint('id_resena')
    )

def downgrade():
    op.drop_table('resenas')
    op.drop_table('consentimientos_informados')
    op.drop_table('notificaciones')
    op.drop_table('facturas')
    op.drop_table('tareas_informes')
    op.drop_table('informes')
    op.drop_table('notas_sesion')
    op.drop_table('anamnesis')
    op.drop_table('citas')
    op.drop_table('psicologo_especialidad')
    op.drop_table('pacientes')
    op.drop_table('psicologos')
    op.drop_table('administrador')
    op.drop_table('especialidades')
    # ### end Alembic commands ###
