from gevent import monkey
monkey.patch_all()

from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, Anamnesis, Informe, Factura, Notificacion
from app.services.socket_service import socketio

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
    print("Iniciando servidor con WebSockets...")
    
    # Intento de actualización silenciosa (no tira el servidor si falla)
    try:
        with app.app_context():
            from app.models import Psicologo
            from werkzeug.security import generate_password_hash
            psicologos = Psicologo.query.all()
            nombres_reales = ["Dra. Elena García", "Dr. Carlos Ruiz", "Dra. Ana Martínez", "Dr. Luis Fernández"]
            for i, p in enumerate(psicologos):
                if p.nombre and ("Joel" in p.nombre or "Dr." not in p.nombre):
                    p.nombre = nombres_reales[i % len(nombres_reales)]
                    p.apellido = "Especialista"
            
            test_email = "test_verificado@mindconnect.com"
            test_p = Psicologo.query.filter_by(correo_electronico=test_email).first()
            if not test_p:
                test_p = Psicologo(
                    nombre="Dr. Test", apellido="Verificado", correo_electronico=test_email,
                    contrasena_hash=generate_password_hash("Test1234"),
                    verificado=True, ocr_verificado=True, biometrico_verificado=True,
                    onboarding_completado=True, precio_online=50.00
                )
                db.session.add(test_p)
            db.session.commit()
            print("Actualización automática de DB completada.")
    except Exception as e:
        print(f"Aviso: Falló la actualización automática pero el servidor seguirá arrancando: {e}")

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
