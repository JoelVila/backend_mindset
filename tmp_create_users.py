from app import create_app, db
from app.models import Psicologo, Paciente
from werkzeug.security import generate_password_hash
from datetime import date

app = create_app()

with app.app_context():
    # 1. Crear Psicólogo
    if not Psicologo.query.filter_by(correo_electronico='psicologo@test.com').first():
        psicologo = Psicologo(
            nombre='Psicologo',
            apellido='Prueba',
            correo_electronico='psicologo@test.com',
            contrasena_hash=generate_password_hash('Password123'),
            telefono='600000000',
            dni_nif='12345678Z',
            numero_colegiado='12345',
            onboarding_completado=True
        )
        db.session.add(psicologo)
        print("Psicólogo de prueba creado: psicologo@test.com / Password123")

    # 2. Crear Paciente
    if not Paciente.query.filter_by(correo_electronico='paciente@test.com').first():
        paciente = Paciente(
            nombre='Paciente',
            apellido='Prueba',
            correo_electronico='paciente@test.com',
            contrasena_hash=generate_password_hash('Password123'),
            telefono='700000000',
            dni_nif='87654321X',
            fecha_nacimiento=date(1995, 1, 1),
            edad=29
        )
        db.session.add(paciente)
        print("Paciente de prueba creado: paciente@test.com / Password123")

    db.session.commit()
    print("Base de datos actualizada con usuarios de prueba.")
