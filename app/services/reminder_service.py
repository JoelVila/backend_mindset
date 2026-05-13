from datetime import date, timedelta
from app.models import Cita, Paciente, Psicologo, Notificacion
from app.adapters.brevo_email_adapter import BrevoEmailAdapter
from app.services.fcm_service import FCMService
from app import db
import random

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

            email_adapter = BrevoEmailAdapter()
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
                    
                    # --- 3. NOTIFICACIÓN APP PARA PACIENTE (INBOX) ---
                    try:
                        msg_notif = f"¡Hola {paciente.nombre}! Recuerda que tienes una cita de {cita.tipo_cita} mañana a las {cita.hora} con {psicologo.nombre}."
                        nueva_notif = Notificacion(
                            id_paciente=paciente.id_paciente,
                            id_psicologo=psicologo.id_psicologo,
                            id_cita=cita.id_cita,
                            titulo="Recordatorio de Cita",
                            mensaje=msg_notif,
                            tipo="cita",
                            leido=False
                        )
                        db.session.add(nueva_notif)
                        count_notifs += 1
                    except Exception as e_inbox:
                        print(f"⚠️ [Records] No se pudo guardar en Inbox: {e_inbox}")

                    # --- 4. PUSH NOTIFICATION AL PACIENTE ---
                    if paciente.fcm_token:
                        try:
                            msg_notif = f"¡Hola {paciente.nombre}! Recuerda que tienes una cita de {cita.tipo_cita} mañana a las {cita.hora} con {psicologo.nombre}."
                            FCMService.send_push(
                                token=paciente.fcm_token,
                                title="Recordatorio de Cita",
                                body=msg_notif
                            )
                        except: pass

                    # --- 5. PUSH NOTIFICATION AL PSICÓLOGO ---
                    if psicologo.fcm_token:
                        try:
                            msg_psico = f"¡Hola {psicologo.nombre}! Mañana tienes una sesión con {paciente.nombre} a las {cita.hora}."
                            FCMService.send_push(
                                token=psicologo.fcm_token,
                                title="Sesión Mañana",
                                body=msg_psico
                            )
                        except: pass
                    
                    print(f"✅ [Records] Recordatorios procesados para cita {cita.id_cita}")
                    
                except Exception as e:
                    print(f"❌ [Records] Error al procesar cita {cita.id_cita}: {e}")
            
            db.session.commit()
            print(f"🏁 [Records] Finalizado. {count_emails} emails enviados y {count_notifs} notificaciones creadas.")

    @staticmethod
    def send_daily_motivation(app):
        """Envía una frase motivacional a todos los usuarios con Token FCM de forma única"""
        with app.app_context():
            from app.models import Notificacion
            print("✨ [Motivation] Enviando frase del día...")
            frases = [
                "Tu salud mental es una prioridad. Tu felicidad es esencial. Tu existencia es valiosa.",
                "No tienes que controlar tus pensamientos; solo tienes que dejar que dejen de controlarte.",
                "Está bien no estar bien, siempre y cuando busques tu bienestar.",
                "Cada paso, por pequeño que sea, te acerca a tu mejor versión.",
                "La autocompasión es el primer paso para la sanación profunda.",
                "Recuerda que hoy es un buen día para empezar de nuevo."
            ]
            frase = random.choice(frases)
            
            # Recopilar usuarios únicos
            usuarios_fcm = {} # token -> {'id': int, 'role': str}
            
            # Pacientes
            pacientes = Paciente.query.filter(Paciente.fcm_token != None).all()
            for p in pacientes:
                if p.fcm_token not in usuarios_fcm:
                    usuarios_fcm[p.fcm_token] = {'id_paciente': p.id_paciente, 'role': 'paciente'}
            
            # Psicólogos
            psicologos = Psicologo.query.filter(Psicologo.fcm_token != None).all()
            for ps in psicologos:
                if ps.fcm_token not in usuarios_fcm:
                    usuarios_fcm[ps.fcm_token] = {'id_psicologo': ps.id_psicologo, 'role': 'psicologo'}

            print(f"📱 [Motivation] Enviando a {len(usuarios_fcm)} dispositivos únicos.")
            
            for token, info in usuarios_fcm.items():
                try:
                    # 1. Enviar Push
                    FCMService.send_push(token, "Ánimo del día", frase)
                    
                    # 2. Guardar en Inbox (DB)
                    nueva_notif = Notificacion(
                        mensaje=frase,
                        titulo="Ánimo del día ✨",
                        tipo="motivacion",
                        id_paciente=info.get('id_paciente'),
                        id_psicologo=info.get('id_psicologo')
                    )
                    db.session.add(nueva_notif)
                except Exception as e_mot:
                    print(f"⚠️ [Motivation] Error enviando/guardando: {e_mot}")
            
            try:
                db.session.commit()
            except Exception as e_commit:
                db.session.rollback()
                print(f"❌ [Motivation] Error commit final: {e_commit}")
            print(f"🏁 [Motivation] Proceso finalizado.")

    @staticmethod
    def send_imminent_reminders(app):
        """Busca citas que empiecen en 15 minutos y envía push inmediato"""
        from datetime import datetime, timedelta
        with app.app_context():
            now = datetime.now()
            # Margen de búsqueda: citas que empiecen entre dentro de 13 y 18 minutos
            target_start = now + timedelta(minutes=13)
            target_end = now + timedelta(minutes=18)
            
            print(f"⏰ [Imminent] Buscando citas entre {target_start.time()} y {target_end.time()}...")
            
            citas = Cita.query.filter(
                Cita.fecha == now.date(),
                Cita.hora >= target_start.time(),
                Cita.hora <= target_end.time(),
                Cita.estado.in_(['confirmada', 'programada', 'pendiente'])
            ).all()
            
            for cita in citas:
                paciente = Paciente.query.get(cita.id_paciente)
                psicologo = Psicologo.query.get(cita.id_psicologo)
                
                if paciente and paciente.fcm_token:
                    FCMService.send_push(
                        token=paciente.fcm_token,
                        title="Tu sesion empieza pronto",
                        body=f"Tu cita con {psicologo.nombre} comienza en 15 minutos. ¡Prepárate!",
                        data={"type": "appointment_reminder", "id_cita": str(cita.id_cita)}
                    )
                
                if psicologo and psicologo.fcm_token:
                    FCMService.send_push(
                        token=psicologo.fcm_token,
                        title="Sesion en 15 minutos",
                        body=f"Tu sesión con {paciente.nombre} empieza en breve.",
                        data={"type": "appointment_reminder", "id_cita": str(cita.id_cita)}
                    )
            
            if citas:
                print(f"✅ [Imminent] Enviados {len(citas)} recordatorios de última hora.")
