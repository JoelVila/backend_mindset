from flask_apscheduler import APScheduler

scheduler = APScheduler()

def send_reminders(app):
    """
    Wrapper function to call the ReminderService.
    """
    from app.services.reminder_service import ReminderService
    ReminderService.send_daily_reminders(app)

def send_motivation(app):
    """
    Wrapper function to call the ReminderService for motivation.
    """
    from app.services.reminder_service import ReminderService
    ReminderService.send_daily_motivation(app)

def send_imminent_reminders(app):
    """
    Check for appointments starting in 15 minutes.
    """
    from app.services.reminder_service import ReminderService
    ReminderService.send_imminent_reminders(app)
