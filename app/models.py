from app import db
from datetime import datetime

# Tabla de asociación (Many-to-Many) entre Psicologo y Especialidad
psicologo_especialidad = db.Table('psicologo_especialidad',
    db.Column('psicologo_id', db.Integer, db.ForeignKey('psicologos.id_psicologo'), primary_key=True),
    db.Column('especialidad_id', db.Integer, db.ForeignKey('especialidades.id'), primary_key=True)
)

class Especialidad(db.Model):
    __tablename__ = 'especialidades'
    id_especialidad = db.Column("id", db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    # Relación inversa (opcional, para acceder desde especialidad a psicólogos)
    # psicologos = db.relationship('Psicologo', secondary=psicologo_especialidad, back_populates='especialidades')

class Psicologo(db.Model):
    __tablename__ = 'psicologos'
    id_psicologo = db.Column(db.Integer, primary_key=True)
    correo_electronico = db.Column(db.String(120), unique=True, nullable=False)
    verificado = db.Column(db.Boolean, default=False)
    contrasena_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    dni_nif = db.Column(db.String(20))
    direccion_fiscal = db.Column(db.String(255))
    numero_colegiado = db.Column(db.String(50))
    telefono = db.Column(db.String(20)) # Added phone field
    foto_psicologo = db.Column(db.Text(length=4294967295)) # URL o BLOB (se recomienda URL)
    
    # Campos recuperados (Extra al diagrama)
    bio = db.Column(db.Text)
    anios_experiencia = db.Column(db.Integer)
    precio_online = db.Column(db.Numeric(10, 2))
    
    # Datos bancarios extendidos
    cuenta_bancaria = db.Column(db.String(200)) # IBAN
    banco = db.Column(db.String(100))
    titular_cuenta = db.Column(db.String(200))
    
    # Password reset
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)

    # Onboarding obligatorio
    horario_json = db.Column(db.Text)  # JSON: {"lunes":{"inicio":"09:00","fin":"17:00"}, ...}
    max_pacientes_dia = db.Column(db.Integer, default=8)
    onboarding_completado = db.Column(db.Boolean, default=False)
    video_presentacion_url = db.Column(db.String(500), nullable=True)
    
    # Ofertas de Introducción
    ofrece_sesion_intro = db.Column(db.Boolean, default=False)
    precio_sesion_intro = db.Column(db.Numeric(10, 2), default=0.00)

    # Relaciones
    especialidades = db.relationship('Especialidad', secondary=psicologo_especialidad, 
                                    lazy='subquery',
                                    backref=db.backref('psicologos', lazy=True))
    
    citas = db.relationship('Cita', backref='psicologo', lazy=True)
    informes = db.relationship('Informe', backref='psicologo', lazy=True)
    facturas = db.relationship('Factura', backref='psicologo', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='psicologo', lazy=True)

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id_paciente = db.Column(db.Integer, primary_key=True)
    correo_electronico = db.Column(db.String(120), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    dni_nif = db.Column(db.String(20), nullable=False)
    direccion_fiscal = db.Column(db.String(255))
    foto_paciente = db.Column(db.Text(length=4294967295)) # URL o BLOB
    token_pago = db.Column(db.String(255))
    
    # Campos recuperados (Extra al diagrama)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    
    # Password reset
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)

    # Relaciones
    citas = db.relationship('Cita', backref='paciente', lazy=True)
    informes = db.relationship('Informe', backref='paciente', lazy=True)
    facturas = db.relationship('Factura', backref='paciente', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='paciente', lazy=True)
    anamnesis = db.relationship('Anamnesis', backref='paciente', uselist=False) # 1 a 1

class Cita(db.Model):
    __tablename__ = 'citas'
    id_cita = db.Column("id", db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_especialidad = db.Column(db.Integer, db.ForeignKey('especialidades.id'), nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    tipo_cita = db.Column(db.String(50))
    motivo = db.Column(db.String(255))
    motivo_orientativo = db.Column(db.Text) # Información extra para la primera cita
    es_primera_vez = db.Column(db.Boolean, default=False)
    is_urgente = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(20)) # pendiente, confirmada, cancelada...
    precio_cita = db.Column(db.Numeric(10, 2))
    enlace_meet = db.Column(db.String(500)) # Link a Jitsi Meet
    google_calendar_event_id = db.Column(db.String(255)) # ID del evento en Google Calendar
    stripe_session_id = db.Column(db.String(255)) # ID de pago en Stripe
    motivo_cancelacion = db.Column(db.Text)  # Razón de cancelación del paciente
    documentacion_cancelacion = db.Column(db.Text)  # Documento adjunto (base64)

    # Relaciones
    notas = db.relationship('NotasSesion', backref='cita', lazy=True)
    
    # Un informe puede estar ligado a una cita (opcional según diagrama 0..1)
    informes = db.relationship('Informe', backref='cita', lazy=True)
    facturas = db.relationship('Factura', backref='cita', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='cita', lazy=True)
    anamnesis = db.relationship('Anamnesis', backref='cita', lazy=True)

class Informe(db.Model):
    __tablename__ = 'informes'
    id_informe = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=True) # Nullable según diagrama
    
    titulo_informe = db.Column(db.String(255))
    texto_informe = db.Column(db.Text) # Contenido principal
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    tareas = db.relationship('TareaInforme', backref='informe', lazy=True, cascade="all, delete-orphan")

class TareaInforme(db.Model):
    __tablename__ = 'tareas_informes'
    id_tarea = db.Column(db.Integer, primary_key=True)
    id_informe = db.Column(db.Integer, db.ForeignKey('informes.id_informe'), nullable=False)
    
    descripcion = db.Column(db.String(500), nullable=False)
    completada = db.Column(db.Boolean, default=False)

class Factura(db.Model):
    __tablename__ = 'facturas'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=True)

    numero_factura = db.Column(db.String(50), unique=True)
    fecha_emision = db.Column(db.Date, default=datetime.utcnow)
    base_imponible = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))
    importe_total = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(20)) # pagada, pendiente...
    concepto = db.Column(db.String(255))

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id_notificacion = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=True)
    
    mensaje = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    leido = db.Column(db.Boolean, default=False)

class Anamnesis(db.Model):
    __tablename__ = 'anamnesis'
    id_anamnesis = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), unique=True, nullable=False) # Relación 1:1 con paciente
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=True)
    
    antecedentes = db.Column(db.Text)
    motivo_consulta = db.Column(db.Text)
    alergias = db.Column(db.Text)
    fecha_alta = db.Column(db.Date, default=datetime.utcnow)

class NotasSesion(db.Model):
    __tablename__ = 'notas_sesion'
    id_nota = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    
    tipo_nota = db.Column(db.String(50))
    contenido = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Administrador(db.Model):
    __tablename__ = 'administrador'
    id_admin = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), default="Admin")
    email = db.Column(db.String(120), unique=True, nullable=False) # Diagram dice 'email' aqui, a diferencia de correo_electronico en otros? 
    contrasena_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<Administrador {self.email}>'

class ConsentimientoInformado(db.Model):
    __tablename__ = 'consentimientos_informados'
    id = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    fecha_aceptacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))
    version_documento = db.Column(db.String(20), default='1.0')

    # Unique constraint: un consentimiento por pareja paciente-psicólogo
    __table_args__ = (
        db.UniqueConstraint('id_paciente', 'id_psicologo', name='uq_consentimiento_paciente_psicologo'),
    )

    paciente = db.relationship('Paciente', backref='consentimientos')
    psicologo = db.relationship('Psicologo', backref='consentimientos')

class Resena(db.Model):
    __tablename__ = 'resenas'
    id_resena = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=True) # Opcional si se quiere ligar a una cita
    
    puntuacion = db.Column(db.Integer, nullable=False) # 1 a 5
    comentario = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    paciente_obj = db.relationship('Paciente', backref=db.backref('resenas_enviadas', lazy=True))
    psicologo_obj = db.relationship('Psicologo', backref=db.backref('resenas_recibidas', lazy=True))
