"""
Script to populate database with sample psychologist data
Run this after applying migrations to test the new endpoint
"""
from app import create_app, db
from app.models import Psicologo, Especialidad, Resena, Paciente, psicologo_especialidad
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Get or create specialties
    ansiedad = Especialidad.query.filter_by(nombre='Ansiedad').first()
    depresion = Especialidad.query.filter_by(nombre='Depresión').first()
    terapia_cognitiva = Especialidad.query.filter_by(nombre='Terapia Cognitivo-Conductual').first()
    trauma = Especialidad.query.filter_by(nombre='Trauma').first()
    ptsd = Especialidad.query.filter_by(nombre='PTSD').first()
    emdr = Especialidad.query.filter_by(nombre='Terapia EMDR').first()
    
    if not ansiedad:
        ansiedad = Especialidad(nombre='Ansiedad')
        db.session.add(ansiedad)
    
    if not depresion:
        depresion = Especialidad(nombre='Depresión')
        db.session.add(depresion)
    
    if not terapia_cognitiva:
        terapia_cognitiva = Especialidad(nombre='Terapia Cognitivo-Conductual')
        db.session.add(terapia_cognitiva)
    
    if not trauma:
        trauma = Especialidad(nombre='Trauma')
        db.session.add(trauma)
    
    if not ptsd:
        ptsd = Especialidad(nombre='PTSD')
        db.session.add(ptsd)
    
    if not emdr:
        emdr = Especialidad(nombre='Terapia EMDR')
        db.session.add(emdr)
    
    db.session.commit()
    
    # Create sample psychologists
    psicologo1 = Psicologo(
        nombre='Dra. María González',
        email='maria.gonzalez@example.com',
        password_hash=generate_password_hash('password123'),
        telefono='1234567890',
        foto_perfil='https://i.pravatar.cc/150?img=1',
        bio='Especialista en terapia cognitivo-conductual con más de 8 años de experiencia ayudando a personas con ansiedad y depresión.',
        verificado=True,
        anios_experiencia=8,
        precio_presencial=50.0,
        precio_online=80.0
    )
    psicologo1.especialidades.extend([ansiedad, depresion, terapia_cognitiva])
    
    psicologo2 = Psicologo(
        nombre='Dr. Carlos Ramírez',
        email='carlos.ramirez@example.com',
        password_hash=generate_password_hash('password123'),
        telefono='0987654321',
        foto_perfil='https://i.pravatar.cc/150?img=12',
        bio='Especializado en trauma y PTSD. Certificado en EMDR y terapia centrada en el trauma con experiencia de 12 años.',
        verificado=True,
        anios_experiencia=12,
        precio_presencial=60.0,
        precio_online=90.0
    )
    psicologo2.especialidades.extend([trauma, ptsd, emdr])
    
    psicologo3 = Psicologo(
        nombre='Dra. Laura Martínez',
        email='laura.martinez@example.com',
        password_hash=generate_password_hash('password123'),
        telefono='5551234567',
        foto_perfil='https://i.pravatar.cc/150?img=5',
        bio='Especialista en terapia de pareja y relaciones interpersonales. Enfoque en comunicación efectiva y resolución de conflictos.',
        verificado=True,
        anios_experiencia=10,
        precio_presencial=55.0,
        precio_online=75.0
    )
    # Laura doesn't have specialties in the screenshot, but let's add some
    
    db.session.add_all([psicologo1, psicologo2, psicologo3])
    db.session.commit()
    
    # Create a sample patient for reviews
    paciente_test = Paciente.query.first()
    if not paciente_test:
        paciente_test = Paciente(
            nombre='Test',
            apellido='Patient',
            email='test@patient.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(paciente_test)
        db.session.commit()
    
    # Add sample reviews
    review1 = Resena(
        id_psicologo=psicologo1.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=5,
        comentario='Excelente profesional, muy recomendable'
    )
    
    review2 = Resena(
        id_psicologo=psicologo1.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=5,
        comentario='Me ayudó mucho con mi ansiedad'
    )
    
    review3 = Resena(
        id_psicologo=psicologo1.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=4,
        comentario='Muy buena experiencia'
    )
    
    # Reviews for psicologo2
    review4 = Resena(
        id_psicologo=psicologo2.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=5,
        comentario='Increíble profesional'
    )
    
    review5 = Resena(
        id_psicologo=psicologo2.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=5,
        comentario='El mejor psicólogo que he tenido'
    )
    
    # Reviews for psicologo3
    review6 = Resena(
        id_psicologo=psicologo3.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=5,
        comentario='Salvó mi matrimonio'
    )
    
    review7 = Resena(
        id_psicologo=psicologo3.id_psicologo,
        id_paciente=paciente_test.id_paciente,
        puntuacion=4,
        comentario='Muy profesional'
    )
    
    db.session.add_all([review1, review2, review3, review4, review5, review6, review7])
    db.session.commit()
    
    print("✅ Sample data created successfully!")
    print(f"Created {Psicologo.query.count()} psychologists")
    print(f"Created {Resena.query.count()} reviews")
