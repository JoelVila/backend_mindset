from app import db
from app.models import Informe, Paciente, Psicologo, Cita
from datetime import datetime

class InformeService:
    @staticmethod
    def crear_informe(data):
        # Validar campos básicos
        if 'id_paciente' not in data or 'id_psicologo' not in data:
            return None, {"msg": "Faltan datos obligatorios (id_paciente, id_psicologo)"}, 400

        # Verificar existencia
        paciente = Paciente.query.get(data['id_paciente'])
        psicologo = Psicologo.query.get(data['id_psicologo'])
        
        if not paciente or not psicologo:
             return None, {"msg": "Paciente o Psicólogo no encontrado"}, 404
        
        nuevo_informe = Informe(
            id_paciente=data['id_paciente'],
            id_psicologo=data['id_psicologo'],
            id_cita=data.get('id_cita'), # Opcional
            titulo_informe=data.get('titulo_informe', 'Sin Título'),
            texto_informe=data.get('texto_informe', ''),
            diagnostico=data.get('diagnostico', ''),
            tratamiento=data.get('tratamiento', '')
        )
        
        try:
            db.session.add(nuevo_informe)
            db.session.commit()
            return nuevo_informe, {"msg": "Informe creado correctamente"}, 201
        except Exception as e:
            db.session.rollback()
            return None, {"msg": f"Error creando informe: {str(e)}"}, 500

    @staticmethod
    def update_informe(id_informe, data):
        informe = Informe.query.get(id_informe)
        if not informe:
            return None, {"msg": "Informe no encontrado"}, 404
            
        # Actualizar campos permitidos
        if 'titulo_informe' in data: informe.titulo_informe = data['titulo_informe']
        if 'texto_informe' in data: informe.texto_informe = data['texto_informe']
        if 'diagnostico' in data: informe.diagnostico = data['diagnostico']
        if 'tratamiento' in data: informe.tratamiento = data['tratamiento']
        
        # Fecha modificación se actualiza sola por onupdate en modelo, 
        # pero forzamos por si acaso en algunas DBs
        informe.fecha_modificacion = datetime.utcnow()
        
        try:
            db.session.commit()
            return informe, {"msg": "Informe actualizado"}, 200
        except Exception as e:
            db.session.rollback()
            return None, {"msg": f"Error actualizando: {str(e)}"}, 500

    @staticmethod
    def get_informes_paciente(id_paciente):
        return Informe.query.filter_by(id_paciente=id_paciente).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informe_id(id_informe):
        return Informe.query.get(id_informe)
