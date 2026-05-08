from app import db
from app.models import NotasSesion, Cita
from datetime import datetime
from app.errors import APIException

class NotaService:
    @staticmethod
    def crear_nota(data):
        if 'id_cita' not in data or 'contenido' not in data:
            raise APIException("Faltan datos (id_cita, contenido)", 400)
            
        cita = Cita.query.get(data['id_cita'])
        if not cita:
             raise APIException("Cita no encontrada", 404)
             
        nueva_nota = NotasSesion(
            id_cita=data['id_cita'],
            tipo_nota=data.get('tipo_nota', 'privada'),
            contenido=data['contenido']
        )
        
        db.session.add(nueva_nota)
        db.session.commit()
        return nueva_nota

    @staticmethod
    def update_nota(id_nota, data):
        nota = NotasSesion.query.get(id_nota)
        if not nota:
            raise APIException("Nota no encontrada", 404)
            
        if 'contenido' in data: nota.contenido = data['contenido']
        if 'tipo_nota' in data: nota.tipo_nota = data['tipo_nota']
        
        nota.fecha = datetime.utcnow()
        
        db.session.commit()
        return nota

    @staticmethod
    def get_notas_cita(id_cita):
        return NotasSesion.query.filter_by(id_cita=id_cita).order_by(NotasSesion.fecha.desc()).all()
