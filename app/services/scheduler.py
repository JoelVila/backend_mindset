from flask_apscheduler import APScheduler

scheduler = APScheduler()

def send_reminders(app):
    """
    Wrapper function to call the ReminderService.
    """
    from app.services.reminder_service import ReminderService
    ReminderService.send_daily_reminders(app)
