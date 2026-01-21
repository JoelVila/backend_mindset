from datetime import datetime, date, timedelta
from app import db
from app.models import Cita, Psicologo, Paciente
from app.adapters.google_calendar_adapter import GoogleCalendarAdapter

class CitaService:
    @staticmethod
    def agendar_cita(id_paciente, data):
        # ... (código sin cambios hasta aquí) ...

        # Integración con Google Meet si es videollamada
        if data['tipo_cita'] == 'videollamada':
            try:
                # Usamos el Adaptador
                calendar_adapter = GoogleCalendarAdapter()
                paciente = Paciente.query.get(id_paciente)
                
                # Crear fecha hora inicio y fin (asumimos 1 hora de duración)
                start_datetime = datetime.combine(fecha_cita, hora_cita)
                end_datetime = start_datetime + timedelta(hours=1)
                
                summary = f"Consulta Psicológica: {psicologo.nombre} - {paciente.nombre}"
                description = (
                    f"Consulta online agendada desde la plataforma.\n\n"
                    f"🧠 Psicólogo: {psicologo.nombre} {psicologo.apellido}\n"
                    f"📧 Email Psicólogo: {psicologo.correo_electronico}\n\n"
                    f"👤 Paciente: {paciente.nombre} {paciente.apellido}\n"
                    f"📧 Email Paciente: {paciente.correo_electronico}\n\n"
                    f"ℹ️ IMPORTANTE: Si no aparece el enlace de Meet arriba, el psicólogo deberá crear una sala y enviarla a los correos indicados aquí."
                )
                
                # Llamada polimórfica (a través de la interfaz implícita)
                event_result = calendar_adapter.create_event(
                    summary=summary,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    description=description,
                    attendee_emails=[psicologo.correo_electronico, paciente.correo_electronico]
                )
                
                if event_result:
                    nueva_cita.enlace_meet = event_result.get('meetLink') or event_result.get('htmlLink')
                    nueva_cita.google_calendar_event_id = event_result.get('id')
                    db.session.commit()
            except Exception as e:
                print(f"Error generando enlace meet: {e}")
                # No fallamos la request si falla el calendario
        
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
        
        if not fecha_str:
             return None, {"msg": "El parámetro 'fecha' es requerido (formato: YYYY-MM-DD)"}, 400

        try:
            fecha_consulta = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
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
