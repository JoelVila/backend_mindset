from datetime import datetime, date
from app import db
from app.models import Cita, Psicologo

class CitaService:
    @staticmethod
    def agendar_cita(id_paciente, data):
        # Validar campos requeridos
        required_fields = ['id_psicologo', 'fecha', 'hora', 'tipo_cita']
        for field in required_fields:
            if field not in data:
                return None, {"msg": f"Campo '{field}' es requerido"}, 400
        
        # Validar psicólogo existe
        psicologo = Psicologo.query.get(data['id_psicologo'])
        if not psicologo:
            return None, {"msg": "Psicólogo no encontrado"}, 404
        
        # Validar y parsear fecha/hora
        try:
            fecha_cita = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora_cita = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError:
            return None, {"msg": "Formato de fecha u hora inválido"}, 400
        
        # Validar que la fecha no sea en el pasado
        if fecha_cita < date.today():
             return None, {"msg": "No se pueden agendar citas en fechas pasadas"}, 400

        # Validar tipo de cita
        tipos_validos = ['presencial', 'videollamada', 'chat']
        if data['tipo_cita'] not in tipos_validos:
            return None, {"msg": f"Tipo de cita debe ser uno de: {', '.join(tipos_validos)}"}, 400
        
        # Verificar disponibilidad (no hay otra cita a esa hora)
        cita_existente = Cita.query.filter_by(
            id_psicologo=data['id_psicologo'],
            fecha=fecha_cita,
            hora=hora_cita
        ).filter(
            Cita.estado.in_(['pendiente', 'confirmada', 'programada', 'en_curso'])
        ).first()

        if cita_existente:
             return None, {"msg": "El horario seleccionado ya no está disponible"}, 409

        # Calcular precio automáticamente según tipo de cita
        precio_map = {
            'presencial': psicologo.precio_presencial,
            'videollamada': psicologo.precio_online,
            'chat': psicologo.precio_chat
        }
        precio_cita = precio_map.get(data['tipo_cita'])
        
        if precio_cita is None:
             return None, {"msg": f"El psicólogo no tiene configurado el precio para {data['tipo_cita']}"}, 400
        
        # Crear la cita
        nueva_cita = Cita(
            fecha=fecha_cita,
            hora=hora_cita,
            id_psicologo=data['id_psicologo'],
            id_paciente=id_paciente,
            tipo_cita=data['tipo_cita'],
            precio_cita=precio_cita,
            estado='pendiente'
        )
        
        db.session.add(nueva_cita)
        db.session.commit()
        
        return nueva_cita, None, 201

    @staticmethod
    def get_citas_psicologo(psicologo_id, estado_filter='proximas'):
        query = Cita.query.filter_by(id_psicologo=psicologo_id)
        
        if estado_filter == 'proximas':
            query = query.filter(
                Cita.estado.in_(['pendiente', 'confirmada', 'en_curso', 'programada'])
            ).order_by(Cita.fecha.asc(), Cita.hora.asc())
        elif estado_filter == 'historial':
            query = query.filter(
                Cita.estado.in_(['completada', 'cancelada'])
            ).order_by(Cita.fecha.desc(), Cita.hora.desc())
        
        return query.all()

    @staticmethod
    def get_citas_paciente(paciente_id, estado_filter='proximas'):
        query = Cita.query.filter_by(id_paciente=paciente_id)
        
        if estado_filter == 'proximas':
             query = query.filter(
                Cita.estado.in_(['pendiente', 'confirmada', 'programada', 'en_curso'])
            ).order_by(Cita.fecha.asc(), Cita.hora.asc())
        elif estado_filter == 'historial':
            query = query.filter(
                Cita.estado.in_(['completada', 'cancelada'])
            ).order_by(Cita.fecha.desc(), Cita.hora.desc())
            
        return query.all()

    @staticmethod
    def get_disponibilidad_psicologo(id_psicologo, fecha_str):
        psicologo = Psicologo.query.get(id_psicologo)
        if not psicologo:
            return None, {"msg": "Psicólogo no encontrado"}, 404
        
        try:
            fecha_consulta = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return None, {"msg": "Formato de fecha inválido. Use YYYY-MM-DD"}, 400
        
        if fecha_consulta < date.today():
             return None, {"msg": "No se pueden agendar citas en fechas pasadas"}, 400
        
        horarios_trabajo = [
            "09:00", "10:00", "11:00", "12:00",
            "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"
        ]
        
        citas_ocupadas = Cita.query.filter_by(
            id_psicologo=id_psicologo,
            fecha=fecha_consulta
        ).filter(
            Cita.estado.in_(['pendiente', 'confirmada', 'programada', 'en_curso'])
        ).all()
        
        horas_ocupadas = [str(cita.hora)[0:5] for cita in citas_ocupadas]
        horarios_disponibles = [h for h in horarios_trabajo if h not in horas_ocupadas]
        
        return {
            "fecha": fecha_str,
            "psicologo_id": id_psicologo,
            "psicologo_nombre": psicologo.nombre,
            "horarios_disponibles": horarios_disponibles,
            "total_disponibles": len(horarios_disponibles)
        }, None, 200

    @staticmethod
    def create_simple_cita(data, current_user_role, current_user_id):
        new_cita = Cita(
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
            hora=datetime.strptime(data['hora'], '%H:%M').time(),
            id_psicologo=data['id_psicologo'],
            id_paciente=data['id_paciente'],
            tipo_cita=data.get('tipo_cita'),
            precio_cita=data.get('precio_cita')
        )
        db.session.add(new_cita)
        db.session.commit()
        return new_cita
