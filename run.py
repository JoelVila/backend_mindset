from gevent import monkey
monkey.patch_all()

from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, Anamnesis, Informe, Factura, Notificacion
from app.services.socket_service import socketio
from werkzeug.security import generate_password_hash

app = create_app()

# ========================================================
# TAREA DE INICIO (Fuera de main para que Gunicorn la vea)
# ========================================================
try:
    with app.app_context():
        print("Sincronizando psicólogos con Aiven...")
        psicologos = Psicologo.query.all()
        nombres_reales = ["Dra. Elena García", "Dr. Carlos Ruiz", "Dra. Ana Martínez", "Dr. Luis Fernández", "Dra. Sofía López"]
        
        for i, p in enumerate(psicologos):
            if p.nombre and ("Joel" in p.nombre or "Dr." not in p.nombre):
                p.nombre = nombres_reales[i % len(nombres_reales)]
                p.apellido = "Especialista"
        
        test_email = "test_verificado@mindconnect.com"
        psicologo1_email = "psicologo1@test.com"
        
        # Crear test_verificado
        test_p = Psicologo.query.filter_by(correo_electronico=test_email).first()
        if not test_p:
            test_p = Psicologo(
                nombre="Dr. Test", apellido="Verificado", correo_electronico=test_email,
                contrasena_hash=generate_password_hash("Test1234"),
                verificado=True, ocr_verificado=True, biometrico_verificado=True,
                onboarding_completado=True, precio_online=50.00, anios_experiencia=15,
                numero_colegiado="99999-V", bio="Perfil verificado para pruebas del sistema."
            )
            db.session.add(test_p)
        else:
            test_p.verificado = True
            test_p.ocr_verificado = True
            test_p.biometrico_verificado = True

        # Crear psicologo1@test.com
        p1 = Psicologo.query.filter_by(correo_electronico=psicologo1_email).first()
        if not p1:
            p1 = Psicologo(
                nombre="Psicologo", apellido="Prueba", correo_electronico=psicologo1_email,
                contrasena_hash=generate_password_hash("123456"),
                verificado=True, ocr_verificado=True, biometrico_verificado=True,
                onboarding_completado=True, precio_online=60.00, anios_experiencia=5,
                numero_colegiado="11111-P", bio="Psicólogo de prueba verificado."
            )
            db.session.add(p1)
        else:
            p1.contrasena_hash = generate_password_hash("123456")
            p1.verificado = True
            p1.ocr_verificado = True
            p1.biometrico_verificado = True
            p1.onboarding_completado = True
            
        db.session.commit()
        print("Sincronización con Aiven y creación de usuarios completada.")
except Exception as e:
    print(f"Aviso de inicio: {e}")

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 'Psicologo': Psicologo, 'Paciente': Paciente,
        'Especialidad': Especialidad, 'Cita': Cita, 'Anamnesis': Anamnesis,
        'Informe': Informe, 'Factura': Factura, 'Notificacion': Notificacion
    }

if __name__ == '__main__':
    # Esto solo se ejecuta en local
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
