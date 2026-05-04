from app import db
from app.models import Informe, Paciente, Psicologo, Cita, TareaInforme
from datetime import datetime
from app.errors import APIException

class InformeService:
    @staticmethod
    def crear_informe(data):
        if 'id_paciente' not in data or 'id_psicologo' not in data:
            raise APIException("Faltan datos obligatorios (id_paciente, id_psicologo)", 400)

        paciente = Paciente.query.get(data['id_paciente'])
        psicologo = Psicologo.query.get(data['id_psicologo'])
        
        if not paciente or not psicologo:
             raise APIException("Paciente o Psicólogo no encontrado", 404)
        
        nuevo_informe = Informe(
            id_paciente=data['id_paciente'],
            id_psicologo=data['id_psicologo'],
            id_cita=data.get('id_cita'),
            titulo_informe=data.get('titulo_informe', 'Sin Título'),
            texto_informe=data.get('texto_informe', ''),
            diagnostico=data.get('diagnostico', ''),
            tratamiento=data.get('tratamiento', '')
        )
        
        tareas_data = data.get('tareas', [])
        for t in tareas_data:
            if isinstance(t, str):
                nueva_tarea = TareaInforme(descripcion=t)
                nuevo_informe.tareas.append(nueva_tarea)
            elif isinstance(t, dict) and 'descripcion' in t:
                nueva_tarea = TareaInforme(descripcion=t['descripcion'], completada=t.get('completada', False))
                nuevo_informe.tareas.append(nueva_tarea)

        db.session.add(nuevo_informe)
        db.session.commit()
        return nuevo_informe

    @staticmethod
    def toggle_tarea(id_tarea):
        tarea = TareaInforme.query.get(id_tarea)
        if not tarea:
            raise APIException("Tarea no encontrada", 404)
        
        tarea.completada = not tarea.completada
        db.session.commit()
        return tarea.completada

    @staticmethod
    def update_informe(id_informe, data):
        informe = Informe.query.get(id_informe)
        if not informe:
            raise APIException("Informe no encontrado", 404)
            
        if 'titulo_informe' in data: informe.titulo_informe = data['titulo_informe']
        if 'texto_informe' in data: informe.texto_informe = data['texto_informe']
        if 'diagnostico' in data: informe.diagnostico = data['diagnostico']
        if 'tratamiento' in data: informe.tratamiento = data['tratamiento']
        
        informe.fecha_modificacion = datetime.utcnow()
        
        db.session.commit()
        return informe

    @staticmethod
    def get_informes_paciente(id_paciente):
        return Informe.query.filter_by(id_paciente=id_paciente).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informe_id(id_informe):
        return Informe.query.get(id_informe)
