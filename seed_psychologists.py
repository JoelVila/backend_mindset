"""
Script to populate database with sample psychologist data
Run this after applying migrations to test the new endpoint
"""
from app import create_app, db
from app.models import Psicologo, Especialidad, Paciente
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("🌱 Seeding database...")
    
    # 1. Crear Especialidades
    specialties_data = [
        "Ansiedad", "Depresión", "Terapia Cognitivo-Conductual",
        "Trauma", "PTSD", "Terapia EMDR", "Psicología Clínica", "Terapia de Pareja"
    ]
    
    specialty_objects = {}
    for name in specialties_data:
        sp = Especialidad.query.filter_by(nombre=name).first()
        if not sp:
            sp = Especialidad(nombre=name)
            db.session.add(sp)
        specialty_objects[name] = sp
    
    db.session.commit()
    
    # 2. Crear Psicólogos
    # Psicologo 1: Matches the user's search (Barcelona, Ansiedad, Price < 50)
    p1 = Psicologo.query.filter_by(correo_electronico='maria.gonzalez@example.com').first()
    if not p1:
        p1 = Psicologo(
            nombre='María',
            apellido='González',
            correo_electronico='maria.gonzalez@example.com',
            contrasena_hash=generate_password_hash('password123'),
            # No 'telefono' in current model, omitting
            dni_nif='12345678A',
            direccion_fiscal='Av. Diagonal 123, Barcelona', # Matches "Barcelona"
            numero_colegiado='28900',
            telefono='666112233',
            foto_psicologo='https://i.pravatar.cc/150?img=1',
            bio='Especialista en terapia cognitivo-conductual. Experta en ansiedad y estrés.', # Matches "ansiedad"
            anios_experiencia=8,
            precio_presencial=45.0, # Matches < 50
            precio_online=40.0,
            precio_telefono=30.0,
            cuenta_bancaria='ES9121000000000000001234',
            banco='CaixaBank',
            titular_cuenta='María González'
        )
        p1.especialidades.append(specialty_objects['Ansiedad'])
        p1.especialidades.append(specialty_objects['Terapia Cognitivo-Conductual'])
        p1.especialidades.append(specialty_objects['Psicología Clínica']) # Matches "Psicología Clínica"
        db.session.add(p1)

    # Psicologo 2: Madrid (Should not appear in Barcelona search)
    p2 = Psicologo.query.filter_by(correo_electronico='carlos.ramirez@example.com').first()
    if not p2:
        p2 = Psicologo(
            nombre='Carlos',
            apellido='Ramírez',
            correo_electronico='carlos.ramirez@example.com',
            contrasena_hash=generate_password_hash('password123'),
            dni_nif='87654321B',
            direccion_fiscal='Calle Gran Vía 45, Madrid',
            numero_colegiado='28901',
            telefono='666445566',
            foto_psicologo='https://i.pravatar.cc/150?img=12',
            bio='Especializado en trauma y PTSD. Terapia EMDR.',
            anios_experiencia=12,
            precio_presencial=60.0,
            precio_online=90.0
        )
        p2.especialidades.append(specialty_objects['Trauma'])
        p2.especialidades.append(specialty_objects['PTSD'])
        db.session.add(p2)

    # Psicologo 3: Barcelona but Expensive (Should not appear in < 50 search)
    p3 = Psicologo.query.filter_by(correo_electronico='laura.martinez@example.com').first()
    if not p3:
        p3 = Psicologo(
            nombre='Laura',
            apellido='Martínez',
            correo_electronico='laura.martinez@example.com',
            contrasena_hash=generate_password_hash('password123'),
            dni_nif='11223344C',
            direccion_fiscal='Passeig de Gracia 50, Barcelona',
            numero_colegiado='28902',
            telefono='666778899',
            foto_psicologo='https://i.pravatar.cc/150?img=5',
            bio='Terapia de pareja y relaciones.',
            anios_experiencia=10,
            precio_presencial=80.0,
            precio_online=75.0
        )
        p3.especialidades.append(specialty_objects['Terapia de Pareja'])
        db.session.add(p3)

    db.session.commit()
    print("✅ Seed completed! Database populated with test psychologists.")
    print(f"Total Psicólogos: {Psicologo.query.count()}")

