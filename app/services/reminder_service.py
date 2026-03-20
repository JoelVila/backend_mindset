from datetime import date, timedelta
from app.models import Cita, Paciente, Psicologo, Notificacion
from app.adapters.smtp_email_adapter import SmtpEmailAdapter
from app import db

class ReminderService:
    @staticmethod
    def send_daily_reminders(app):
        """
        Busca las citas de 'mañana' y envía recordatorios.
        Requiere pasar la instancia de 'app' para tener el contexto de BD.
        """
        with app.app_context():
            print("⏰ [Records] Iniciando envío de recordatorios diarios...")
            
            tomorrow = date.today() + timedelta(days=1)
            
            # Buscar citas confirmadas o pendientes para mañana
            citas_manana = Cita.query.filter(
                Cita.fecha == tomorrow,
                Cita.estado.in_(['pendiente', 'confirmada', 'programada'])
            ).all()
            
            if not citas_manana:
                print("ℹ️ [Records] No hay citas para mañana.")
                return

            email_adapter = SmtpEmailAdapter()
            count_emails = 0
            count_notifs = 0
            
            for cita in citas_manana:
                try:
                    paciente = Paciente.query.get(cita.id_paciente)
                    psicologo = Psicologo.query.get(cita.id_psicologo)
                    
                    if not paciente or not psicologo:
                        continue
                    
                # --- 1. EMAIL AL PACIENTE ---
                    subject_paciente = f"Recordatorio: Tu cita es mañana - {cita.hora}"
                    body_paciente = (
                        f"Hola {paciente.nombre},<br><br>"
                        f"Te recordamos que tienes una cita programada para el d&iacute;a de ma&ntilde;ana.<br><br>"
                        f"<b>Fecha:</b> {cita.fecha}<br>"
                        f"<b>Hora:</b> {cita.hora}<br>"
                        f"<b>Profesional:</b> {psicologo.nombre} {psicologo.apellido}<br>"
                        f"<b>Tipo:</b> {cita.tipo_cita}<br><br>"
                        f"Por favor, aseg&uacute;rate de conectarte o asistir a tiempo."
                    )
                    email_adapter.send_email(paciente.correo_electronico, subject_paciente, body_paciente, is_html=True)
                    
                    # --- 2. EMAIL AL PSICÓLOGO ---
                    subject_psicologo = f"Recordatorio de Cita: Tienes una sesión mañana - {cita.hora}"
                    body_psicologo = (
                        f"Hola {psicologo.nombre},<br><br>"
                        f"Te recordamos que tienes una cita programada con un paciente para el d&iacute;a de ma&ntilde;ana.<br><br>"
                        f"<b>Fecha:</b> {cita.fecha}<br>"
                        f"<b>Hora:</b> {cita.hora}<br>"
                        f"<b>Paciente:</b> {paciente.nombre} {paciente.apellido}<br>"
                        f"<b>Tipo:</b> {cita.tipo_cita}<br><br>"
                        f"Buen trabajo."
                    )
                    email_adapter.send_email(psicologo.correo_electronico, subject_psicologo, body_psicologo, is_html=True)
                    
                    count_emails += 2
                    
                    # --- 3. NOTIFICACIÓN APP PARA PACIENTE ---
                    msg_notif = f"¡Hola {paciente.nombre}! Recuerda que tienes una cita de {cita.tipo_cita} mañana a las {cita.hora} con {psicologo.nombre}."
                    nueva_notif = Notificacion(
                        id_paciente=paciente.id_paciente,
                        id_psicologo=psicologo.id_psicologo,
                        id_cita=cita.id_cita,
                        mensaje=msg_notif,
                        leido=False
                    )
                    db.session.add(nueva_notif)
                    count_notifs += 1
                    
                    print(f"✅ [Records] Recordatorios procesados para cita {cita.id_cita}")
                    
                except Exception as e:
                    print(f"❌ [Records] Error al procesar cita {cita.id_cita}: {e}")
            
            db.session.commit()
            print(f"🏁 [Records] Finalizado. {count_emails} emails enviados y {count_notifs} notificaciones creadas.")
