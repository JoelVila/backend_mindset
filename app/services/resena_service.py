from app import db
from app.models import Resena, Cita, Psicologo
from sqlalchemy import func

class ResenaService:
    @staticmethod
    def create_or_update_resena(id_paciente, data):
        id_psicologo = data.get('id_psicologo')
        puntuacion = data.get('puntuacion')
        comentario = data.get('comentario')

        if not id_psicologo or not puntuacion:
            return None, {"msg": "id_psicologo y puntuacion son requeridos"}, 400

        # Verificar elegibilidad: al menos una cita COMPLETADA
        cita_completada = Cita.query.filter_by(
            id_paciente=id_paciente, 
            id_psicologo=id_psicologo, 
            estado='completada'
        ).first()

        if not cita_completada:
            return None, {"msg": "No puedes dejar una reseña sin haber completado al menos una sesión con este psicólogo"}, 403

        # Buscar si ya existe una reseña para actualizarla (estilo Google Maps)
        resena = Resena.query.filter_by(id_paciente=id_paciente, id_psicologo=id_psicologo).first()

        if resena:
            resena.puntuacion = puntuacion
            resena.comentario = comentario
            resena.fecha_creacion = db.func.now()
        else:
            resena = Resena(
                id_paciente=id_paciente,
                id_psicologo=id_psicologo,
                puntuacion=puntuacion,
                comentario=comentario
            )
            db.session.add(resena)

        db.session.commit()
        return resena, None, 200

    @staticmethod
    def get_resenas_psicologo(id_psicologo, sort_by='newest'):
        query = Resena.query.filter_by(id_psicologo=id_psicologo)

        if sort_by == 'rating_desc':
            query = query.order_by(Resena.puntuacion.desc())
        elif sort_by == 'rating_asc':
            query = query.order_by(Resena.puntuacion.asc())
        else: # newest
            query = query.order_by(Resena.fecha_creacion.desc())

        return query.all()

    @staticmethod
    def get_rating_stats(id_psicologo):
        stats = db.session.query(
            func.avg(Resena.puntuacion).label('avg'),
            func.count(Resena.id_resena).label('count')
        ).filter(Resena.id_psicologo == id_psicologo).first()

        return {
            "puntuacion_media": float(stats.avg) if stats.avg else 0.0,
            "total_resenas": stats.count or 0
        }
