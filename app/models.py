from app import db
from datetime import datetime
from sqlalchemy import func

# Association table for many-to-many relationship between Psicologo and Especialidad
psicologo_especialidad = db.Table('psicologo_especialidad',
    db.Column('psicologo_id', db.Integer, db.ForeignKey('psicologos.id_psicologo'), primary_key=True),
    db.Column('especialidad_id', db.Integer, db.ForeignKey('especialidades.id'), primary_key=True)
)


class Especialidad(db.Model):
    __tablename__ = 'especialidades'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)


class Psicologo(db.Model):
    __tablename__ = 'psicologos'
    id_psicologo = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telefono = db.Column(db.String(20))
    
    # New fields for enhanced profile
    foto_perfil = db.Column(db.String(500), nullable=False)  # URL to profile photo
    bio = db.Column(db.Text)  # Professional description
    verificado = db.Column(db.Boolean, default=False)  # Verification badge
    anios_experiencia = db.Column(db.Integer)  # Years of experience
    precio_presencial = db.Column(db.Float)  # In-person session price
    precio_online = db.Column(db.Float)  # Online/video call session price
    precio_chat = db.Column(db.Float)  # Chat session price
    
    # Bank account information
    numero_cuenta = db.Column(db.String(34))  # IBAN max 34 characters
    banco = db.Column(db.String(100))  # Bank name
    titular_cuenta = db.Column(db.String(200))  # Account holder name
    
    # Campos de acreditación (COPC)
    numero_licencia = db.Column(db.String(50))
    institucion = db.Column(db.String(255))
    documento_acreditacion = db.Column(db.String(255))
    
    # Keep old especialidad_id for backward compatibility (will be deprecated)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'))
    
    # Many-to-many relationship with Especialidad
    especialidades = db.relationship('Especialidad', secondary=psicologo_especialidad, 
                                    lazy='subquery',
                                    backref=db.backref('psicologos', lazy=True))
    
    # Relationships
    citas = db.relationship('Cita', backref='psicologo', lazy=True)
    informes = db.relationship('Informe', backref='psicologo', lazy=True)
    facturas = db.relationship('Factura', backref='psicologo', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='psicologo', lazy=True)
    resumenes_ingresos = db.relationship('ResumenIngresos', backref='psicologo', lazy=True)
    resenas = db.relationship('Resena', backref='psicologo', lazy=True)
    
    def get_rating_promedio(self):
        """Calculate average rating from reviews"""
        if not self.resenas:
            return None
        return db.session.query(func.avg(Resena.puntuacion)).filter(
            Resena.id_psicologo == self.id_psicologo
        ).scalar()
    
    def get_num_resenas(self):
        """Get total number of reviews"""
        return len(self.resenas)


class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id_paciente = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    edad = db.Column(db.Integer)
    fecha_nacimiento = db.Column(db.Date)  # Birth date
    telefono = db.Column(db.String(20))
    foto_perfil = db.Column(db.String(500), nullable=False) # URL to profile photo
    tipo_paciente = db.Column(db.String(50))
    tipo_tarjeta = db.Column(db.String(50))
    
    # Relationships
    citas = db.relationship('Cita', backref='paciente', lazy=True)
    informes = db.relationship('Informe', backref='paciente', lazy=True)
    facturas = db.relationship('Factura', backref='paciente', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='paciente', lazy=True)
    historial_clinico = db.relationship('HistorialClinico', backref='paciente', uselist=False, cascade="all, delete-orphan")
    resenas = db.relationship('Resena', backref='paciente', lazy=True)

class Resena(db.Model):
    __tablename__ = 'resenas'
    id_resena = db.Column(db.Integer, primary_key=True)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comentario = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class Cita(db.Model):
    __tablename__ = 'citas'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    tipo_cita = db.Column(db.String(50))
    precio_cita = db.Column(db.Float)
    estado = db.Column(db.String(20), default='pendiente')

class Informe(db.Model):
    __tablename__ = 'informes'
    id_informe = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Factura(db.Model):
    __tablename__ = 'facturas'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    numero_factura = db.Column(db.String(50), unique=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float) # Kept from previous, usually needed
    pagado = db.Column(db.Boolean, default=False)

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id_notificacion = db.Column(db.Integer, primary_key=True)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id'))
    mensaje = db.Column(db.String(255))
    leida = db.Column(db.Boolean, default=False)

class HistorialClinico(db.Model):
    __tablename__ = 'historiales_clinicos'
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id_paciente'), nullable=False)
    contenido = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class ResumenIngresos(db.Model):
    __tablename__ = 'resumenes_ingresos'
    id = db.Column(db.Integer, primary_key=True)
    psicologo_id = db.Column(db.Integer, db.ForeignKey('psicologos.id_psicologo'), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    total_ingresos = db.Column(db.Float, default=0.0)


class Administrador(db.Model):
    __tablename__ = 'administradores'

    id_admin = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), default="Admin")
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f'<Administrador {self.email}>'

