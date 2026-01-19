from datetime import datetime
from app import db
from app.models import Informe, Paciente, Factura, Especialidad, HistorialClinico

class InformeService:
    @staticmethod
    def get_informes_paciente(paciente_id):
        return Informe.query.filter_by(id_paciente=paciente_id).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informes_psicologo(psicologo_id):
        return Informe.query.filter_by(id_psicologo=psicologo_id).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informe_detalle(id_informe, user_id, user_role):
        informe = Informe.query.get(id_informe)
        if not informe:
            return None, {"msg": "Informe no encontrado"}, 404
        
        can_access = False
        if user_role == 'paciente' and informe.id_paciente == user_id:
            can_access = True
        elif user_role == 'psicologo' and informe.id_psicologo == user_id:
            can_access = True
        
        if not can_access:
            return None, {"msg": "Acceso denegado a este informe"}, 403
            
        return informe, None, 200

    @staticmethod
    def create_informe(psicologo_id, data):
        if 'id_paciente' not in data or 'contenido' not in data:
            return None, {"msg": "Campos 'id_paciente' y 'contenido' son requeridos"}, 400
        
        paciente = Paciente.query.get(data['id_paciente'])
        if not paciente:
            return None, {"msg": "Paciente no encontrado"}, 404
        
        new_informe = Informe(
            id_paciente=data['id_paciente'],
            id_psicologo=psicologo_id,
            contenido=data['contenido']
        )
        
        db.session.add(new_informe)
        db.session.commit()
        return new_informe, None, 201

class HistorialService:
    @staticmethod
    def get_historial(paciente_id):
        return HistorialClinico.query.filter_by(paciente_id=paciente_id).first()

    @staticmethod
    def update_historial(data):
        paciente_id = data.get('id_paciente')
        contenido = data.get('contenido')
        
        historial = HistorialClinico.query.filter_by(paciente_id=paciente_id).first()
        if historial:
            historial.contenido = contenido
        else:
            historial = HistorialClinico(paciente_id=paciente_id, contenido=contenido)
            db.session.add(historial)
        
        db.session.commit()
        return historial

class FacturaService:
    @staticmethod
    def create_factura(data):
        new_factura = Factura(
            id_paciente=data.get('id_paciente'),
            id_psicologo=data.get('id_psicologo'),
            numero_factura=data.get('numero_factura'),
            total=data.get('total')
        )
        db.session.add(new_factura)
        db.session.commit()
        return new_factura

class EspecialidadService:
    @staticmethod
    def get_all():
        return Especialidad.query.all()
