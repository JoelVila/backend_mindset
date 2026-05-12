from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
try:
    from app.services.scheduler import scheduler, send_reminders, send_motivation, send_imminent_reminders
    _scheduler_available = True
except Exception as _sched_err:
    print(f"\u26a0\ufe0f [Scheduler] No se pudo cargar el scheduler: {_sched_err}")
    _scheduler_available = False
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
            
        from app.models import Especialidad
        if Especialidad.query.count() == 0:
            especialidades_default = [
                'Psicología Clínica',
                'Psicología Educativa',
                'Psicología Organizacional',
                'Neuropsicología',
                'Psicoterapia Infantil',
                'Terapia de Pareja',
                'Psicología del Deporte',
                'Psicología Forense',
                'Psicoterapia Cognitivo-Conductual',
                'Terapia Familiar'
            ]
            for esp_nombre in especialidades_default:
                db.session.add(Especialidad(nombre=esp_nombre))
            db.session.commit()
            print("Especialidades por defecto creadas.")
    
    # Secure HTTP headers
    # content_security_policy=None allows the app to work normally without strict CSP during dev
    talisman.init_app(app, content_security_policy=None)
    
    # Init Scheduler
    global _scheduler_available
    if app.config.get('SCHEDULER_API_ENABLED') and _scheduler_available:
        scheduler.init_app(app)
        scheduler.start()
        
        # Add Job (Run every day at 9:00 AM)
        if not scheduler.get_job('reminder_job'):
             scheduler.add_job(id='reminder_job', func=lambda: send_reminders(app), trigger='cron', hour=9, minute=0)
        
        # Add Motivation Job (Run every day at 10:00 AM)
        if not scheduler.get_job('motivation_job'):
             scheduler.add_job(id='motivation_job', func=lambda: send_motivation(app), trigger='cron', hour=10, minute=0)

        # Add Imminent Reminders Job (Run every 5 minutes)
        if not scheduler.get_job('imminent_job'):
             scheduler.add_job(id='imminent_job', func=lambda: send_imminent_reminders(app), trigger='interval', minutes=5)

    from app.routes import auth_bp, main_bp, tickets_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/main')
    app.register_blueprint(tickets_bp, url_prefix='/main')

    from app.routes.webhook import webhook_bp
    app.register_blueprint(webhook_bp)

    from app.routes.informe_routes import informes_bp
    app.register_blueprint(informes_bp)

    from app.routes.nota_routes import notas_bp
    app.register_blueprint(notas_bp)
    
    from app.services.socket_service import init_socketio
    init_socketio(app)
    
    swagger.init_app(app)

    from app.errors import APIException

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # @app.errorhandler(Exception)
    # def handle_generic_exception(error):
    #     return jsonify({
    #         "error": "Ha habido un error"
    #     }), 500

    return app
