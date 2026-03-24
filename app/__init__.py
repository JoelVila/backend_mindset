from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from app.services.scheduler import scheduler, send_reminders
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
import atexit

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
swagger = Swagger()
limiter = Limiter(
    key_func=get_remote_address, 
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
talisman = Talisman()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    # Configuración de CORS explícito (Sugerencia académica)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Crear administrador por defecto si no existe (Sugerencia académica)
    with app.app_context():
        from app.models import Administrador
        from werkzeug.security import generate_password_hash
        if not Administrador.query.first():
            admin = Administrador(
                email='admin@mindconnect.com',
                contrasena_hash=generate_password_hash('Admin123'),
                nombre='SuperAdmin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin por defecto creado: admin@mindconnect.com / Admin123")
    
    # Secure HTTP headers
    # content_security_policy=None allows the app to work normally without strict CSP during dev
    talisman.init_app(app, content_security_policy=None)
    
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
