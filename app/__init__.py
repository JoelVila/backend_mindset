from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from app.services.scheduler import scheduler, send_reminders
from flasgger import Swagger
import atexit

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
swagger = Swagger()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Init Scheduler
    if app.config.get('SCHEDULER_API_ENABLED'):
        scheduler.init_app(app)
        scheduler.start()
        
        # Add Job (Run every day at 9:00 AM)
        # Note: For testing we might want to run it more often or manually trigger
        # We use 'interval' or 'cron'. Let's use cron for daily run.
        if not scheduler.get_job('reminder_job'):
             scheduler.add_job(id='reminder_job', func=lambda: send_reminders(app), trigger='cron', hour=9, minute=0)
        
        # Ensure scheduler shuts down (optional but good practice)
        # atexit.register(lambda: scheduler.shutdown())

    from app.routes import auth_bp, main_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/main')

    from app.routes.webhook import webhook_bp
    app.register_blueprint(webhook_bp)

    from app.routes.informe_routes import informes_bp
    app.register_blueprint(informes_bp)
    
    from app.routes.nota_routes import notas_bp
    app.register_blueprint(notas_bp)
    
    swagger.init_app(app)

    return app
