from app import create_app, db
from app.models import Psicologo, Paciente, Resena, Especialidad
import random

app = create_app()

bios = [
    "Especialista en ansiedad y estrés con más de 10 años de trayectoria ayudando a pacientes a recuperar su equilibrio emocional.",
    "Psicóloga clínica enfocada en terapia cognitivo-conductual y bienestar personal.",
    "Experto en terapia de pareja y mediación familiar. Mi enfoque es empático y resolutivo.",
    "Psicólogo especializado en trastornos del estado de ánimo y crecimiento personal.",
    "Terapia orientada a resultados. Te ayudo a superar tus miedos y alcanzar tus objetivos.",
    "Acompañamiento emocional para jóvenes y adultos. Especialista en autoestima.",
    "Psicóloga con enfoque integrador. Trabajaremos juntos para mejorar tu calidad de vida.",
    "Especialista en psicología de la salud y manejo del estrés laboral.",
    "Terapeuta con amplia experiencia en duelo y procesos de cambio vital.",
    "Psicología positiva y coaching emocional para el desarrollo del talento.",
]

comentarios = [
    "Excelente profesional, me ha ayudado mucho en mi proceso.",
    "Muy empático y cercano. Lo recomiendo 100%.",
    "Las sesiones son muy fructíferas. He notado el cambio desde el primer mes.",
    "Me siento muy cómodo/a en las sesiones. Es muy profesional.",
    "Gran capacidad de escucha y herramientas muy útiles.",
    "Una experiencia muy positiva. Superó mis expectativas.",
    "Muy puntual y profesional. Explica todo con mucha claridad.",
    "Me ha dado las claves para gestionar mi ansiedad de forma eficaz.",
    "Un trato inmejorable. Te hace sentir escuchado en todo momento.",
    "La mejor decisión que he tomado este año para mi salud mental.",
]

with app.app_context():
    print("🚀 Iniciando enriquecimiento de datos de Psicólogos...")
    
    psicologos = Psicologo.query.all()
    pacientes = Paciente.query.all()
    
    if not psicologos:
        print("❌ No hay psicólogos en la base de datos. Ejecuta primero tmp_create_users.py.")
    else:
        for i, p in enumerate(psicologos):
            # 1. Foto de perfil (Avatar)
            gender = "men" if i % 2 == 0 else "women"
            p.foto_psicologo = f"https://randomuser.me/api/portraits/{gender}/{random.randint(1, 70)}.jpg"
            
            # 2. Bio profesional
            p.bio = random.choice(bios)
            
            # 3. Precio y Experiencia
            p.precio_online = random.randint(45, 85)
            p.anios_experiencia = random.randint(3, 15)
            
            # 4. Reseñas
            # Eliminar reseñas previas si las hubiera para este psicólogo en el script
            # Resena.query.filter_by(id_psicologo=p.id_psicologo).delete()
            
            if pacientes:
                num_resenas = random.randint(3, 6)
                for _ in range(num_resenas):
                    paciente = random.choice(pacientes)
                    # Evitar duplicados de reseña por el mismo paciente (opcional)
                    resena_existente = Resena.query.filter_by(id_paciente=paciente.id_paciente, id_psicologo=p.id_psicologo).first()
                    if not resena_existente:
                        nueva_resena = Resena(
                            id_paciente=paciente.id_paciente,
                            id_psicologo=p.id_psicologo,
                            puntuacion=random.randint(4, 5), # Queremos reseñas buenas para empezar
                            comentario=random.choice(comentarios)
                        )
                        db.session.add(nueva_resena)
            
            print(f"✅ Psicólogo {p.nombre} actualizado con Éxito.")
        
        db.session.commit()
        print("\n✨ PROCESO COMPLETADO: Datos enriquecidos con éxito.")
