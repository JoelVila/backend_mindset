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
    contrasena_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    dni_nif = db.Column(db.String(20))
    direccion_fiscal = db.Column(db.String(255))
    numero_colegiado = db.Column(db.String(50))
    telefono = db.Column(db.String(20)) # Added phone field
    foto_psicologo = db.Column(db.String(500)) # URL o BLOB (se recomienda URL)
    
    # Campos recuperados (Extra al diagrama)
    bio = db.Column(db.Text)
    anios_experiencia = db.Column(db.Integer)
    precio_presencial = db.Column(db.Numeric(10, 2))
    precio_online = db.Column(db.Numeric(10, 2))
    precio_chat = db.Column(db.Numeric(10, 2))
    
    # Datos bancarios extendidos
    cuenta_bancaria = db.Column(db.String(50)) # IBAN
    banco = db.Column(db.String(100))
    titular_cuenta = db.Column(db.String(200))

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
    foto_paciente = db.Column(db.String(500)) # URL o BLOB
    token_pago = db.Column(db.String(255))
    
    # Campos recuperados (Extra al diagrama)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    edad = db.Column(db.Integer, nullable=False)

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
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    tipo_cita = db.Column(db.String(50))
    estado = db.Column(db.String(20)) # pendiente, confirmada, cancelada...
    precio_cita = db.Column(db.Numeric(10, 2))

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

