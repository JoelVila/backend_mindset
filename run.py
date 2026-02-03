from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, Anamnesis, Informe, Factura, Notificacion

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Psicologo': Psicologo,
        'Paciente': Paciente,
        'Especialidad': Especialidad,
        'Cita': Cita,
        'Anamnesis': Anamnesis,
        'Informe': Informe,
        'Factura': Factura,
        'Notificacion': Notificacion
    }


if __name__ == '__main__':
    # Inicializar Scheduler para recordatorios
    from flask_apscheduler import APScheduler
    from app.services.reminder_service import ReminderService
    
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    
    # Tarea programada: Ejecutar cada día a las 09:00 AM
    @scheduler.task('cron', id='send_reminders', hour=9, minute=0)
    def scheduled_reminders():
        ReminderService.send_daily_reminders(app)
        
    print("🕒 [Scheduler] Iniciado. Recordatorios programados para las 09:00 AM.")
    app.run(debug=True)
