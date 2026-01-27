from datetime import datetime, date, timedelta
from app import db
from app.models import Cita, Psicologo, Paciente
from app.adapters.google_calendar_adapter import GoogleCalendarAdapter
from app.adapters.smtp_email_adapter import SmtpEmailAdapter

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

        # Integración con Google Calendar y Jitsi para videollamadas
        if data['tipo_cita'] == 'videollamada':
            try:
                # Generar enlace único de Jitsi
                import uuid
                jitsi_link = f"https://meet.jit.si/PsicoApp-{uuid.uuid4().hex[:12]}"
                
                # Usamos el Adaptador
                calendar_adapter = GoogleCalendarAdapter()
                paciente = Paciente.query.get(id_paciente)
                
                # Crear fecha hora inicio y fin (asumimos 1 hora de duración)
                start_datetime = datetime.combine(fecha_cita, hora_cita)
                end_datetime = start_datetime + timedelta(hours=1)
                
                summary = f"Consulta Psicológica: {psicologo.nombre} - {paciente.nombre}"
                description = (
                    f"Consulta online agendada desde la plataforma.\n\n"
                    f"🔗 **ENLACE A LA VIDEOLLAMADA:** {jitsi_link}\n\n"
                    f"🧠 Psicólogo: {psicologo.nombre} {psicologo.apellido}\n"
                    f"📧 Email Psicólogo: {psicologo.correo_electronico}\n\n"
                    f"👤 Paciente: {paciente.nombre} {paciente.apellido}\n"
                    f"📧 Email Paciente: {paciente.correo_electronico}\n\n"
                    f"Nota: Por favor unirse a la hora programada haciendo clic en el enlace."
                )
                
                # Llamada al adaptador con el enlace de Jitsi como ubicación
                event_result = calendar_adapter.create_event(
                    summary=summary,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    description=description,
                    attendee_emails=[psicologo.correo_electronico, paciente.correo_electronico],
                    location=jitsi_link
                )
                
                # Guardamos el enlace generado en la base de datos
                nueva_cita.enlace_meet = jitsi_link
                
                if event_result:
                    nueva_cita.google_calendar_event_id = event_result.get('id')
                
                db.session.commit()

                # --- Notificación por Email (Opción "Casera") ---
                try:
                    email_adapter = SmtpEmailAdapter()
                    subject = f"Confirmación Cita Videollamada - {fecha_cita} {hora_cita}"
                    
                    # Email para Paciente
                    body_paciente = (
                        f"Hola {paciente.nombre},<br><br>"
                        f"Tu cita online con {psicologo.nombre} ha sido confirmada.<br>"
                        f"📅 Fecha: {fecha_cita}<br>"
                        f"⏰ Hora: {hora_cita}<br>"
                        f"🔗 <b>Enlace Videollamada:</b> <a href='{jitsi_link}'>{jitsi_link}</a><br><br>"
                        f"Gracias por confiar en nosotros."
                    )
                    email_adapter.send_email(paciente.correo_electronico, subject, body_paciente, is_html=True)

                    # Email para Psicólogo
                    body_psicologo = (
                        f"Hola Dr/a. {psicologo.nombre},<br><br>"
                        f"Has recibido una nueva cita online con el paciente {paciente.nombre} {paciente.apellido}.<br>"
                        f"📅 Fecha: {fecha_cita}<br>"
                        f"⏰ Hora: {hora_cita}<br>"
                        f"🔗 <b>Enlace Videollamada:</b> <a href='{jitsi_link}'>{jitsi_link}</a>"
                    )
                    email_adapter.send_email(psicologo.correo_electronico, subject, body_psicologo, is_html=True)
                
                except Exception as e:
                    print(f"Error enviando emails de confirmación: {e}")

            except Exception as e:
                print(f"Error generando enlace videollamada: {e}")
                # No fallamos la request si falla el calendario, pero logueamos
        
        # Si no es videollamada, igual podríamos querer notificar al calendario (opcional, pero el usuario preguntó por videocitas principalmente)
        # Dejamos la lógica actual solo para videollamada como estaba antes, o ampliamos si se requiere.
        
        
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
