from app import db
from app.models import NotasSesion, Cita
from datetime import datetime

class NotaService:
    @staticmethod
    def crear_nota(data):
        if 'id_cita' not in data or 'contenido' not in data:
            return None, {"msg": "Faltan datos (id_cita, contenido)"}, 400
            
        cita = Cita.query.get(data['id_cita'])
        if not cita:
             return None, {"msg": "Cita no encontrada"}, 404
             
        nueva_nota = NotasSesion(
            id_cita=data['id_cita'],
            tipo_nota=data.get('tipo_nota', 'privada'), # Default privada
            contenido=data['contenido']
        )
        
        try:
            db.session.add(nueva_nota)
            db.session.commit()
            return nueva_nota, {"msg": "Nota guardada"}, 201
        except Exception as e:
            db.session.rollback()
            return None, {"msg": str(e)}, 500

    @staticmethod
    def update_nota(id_nota, data):
        nota = NotasSesion.query.get(id_nota)
        if not nota:
            return None, {"msg": "Nota no encontrada"}, 404
            
        if 'contenido' in data: nota.contenido = data['contenido']
        if 'tipo_nota' in data: nota.tipo_nota = data['tipo_nota']
        
        # Opcional: Actualizar fecha al editar
        nota.fecha = datetime.utcnow()
        
        try:
            db.session.commit()
            return nota, {"msg": "Nota actualizada"}, 200
        except Exception as e:
            db.session.rollback()
            return None, {"msg": str(e)}, 500

    @staticmethod
    def get_notas_cita(id_cita):
        return NotasSesion.query.filter_by(id_cita=id_cita).order_by(NotasSesion.fecha.desc()).all()
