from datetime import date, timedelta
from app.models import Cita, Paciente, Psicologo
from app.adapters.smtp_email_adapter import SmtpEmailAdapter

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
            count = 0
            
            for cita in citas_manana:
                try:
                    paciente = Paciente.query.get(cita.id_paciente)
                    psicologo = Psicologo.query.get(cita.id_psicologo)
                    
                    if not paciente or not psicologo:
                        continue
                        
                    subject = f"🔔 Recordatorio: Tu cita es mañana - {cita.hora}"
                    
                    body = (
                        f"Hola {paciente.nombre},<br><br>"
                        f"Te recordamos que tienes una cita programada para <b>mañana</b>.<br><br>"
                        f"📅 <b>Fecha:</b> {cita.fecha}<br>"
                        f"⏰ <b>Hora:</b> {cita.hora}<br>"
                        f"👨‍⚕️ <b>Profesional:</b> {psicologo.nombre} {psicologo.apellido}<br>"
                        f"📞 <b>Tipo:</b> {cita.tipo_cita}<br><br>"
                        f"Por favor, asegúrate de conectarte o asistir a tiempo."
                    )
                    
                    # Enviar email
                    email_adapter.send_email(paciente.correo_electronico, subject, body, is_html=True)
                    print(f"✅ [Records] Recordatorio enviado a {paciente.correo_electronico}")
                    count += 1
                    
                except Exception as e:
                    print(f"❌ [Records] Error al procesar cita {cita.id_cita}: {e}")
            
            print(f"🏁 [Records] Finalizado. {count} recordatorios enviados.")
