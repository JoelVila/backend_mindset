from app import create_app, db
from app.models import Especialidad

app = create_app()

def seed_especialidades():
    with app.app_context():
        especialidades = [
            "Psicología Clínica",
            "Psicología Educativa",
            "Psicología Infantil y Juvenil",
            "Neuropsicología",
            "Psicología Forense",
            "Psicología del Deporte",
            "Psicología de la Salud",
            "Psicología Organizacional",
            "Psicología Social",
            "Psicología Familiar y de Pareja",
            "Psicología Cognitivo-Conductual",
            "Psicoanálisis",
            "Psicología Humanista",
            "Sexología",
            "Psicogerontología",
            "Psicología de las Adicciones",
            "Coaching Psicológico",
            "Terapia de Pareja",
            "Terapia Familiar",
            "Psicología Geriátrica",
            "Adicciones",
            "Trastornos de Ansiedad",
            "Trastornos del Estado de Ánimo",
            "Trastornos Alimentarios",
            "TDAH",
            "Trauma y TEPT",
            "Mindfulness y Meditación",
            "Duelo y Pérdida"
        ]

        for nombre in especialidades:
            if not Especialidad.query.filter_by(nombre=nombre).first():
                nueva = Especialidad(nombre=nombre)
                db.session.add(nueva)
                print(f"Adding: {nombre}")
        
        db.session.commit()
        print("Especialidades added successfully!")

def seed_admin():
    from app.models import Administrador
    from werkzeug.security import generate_password_hash
    with app.app_context():
        # Check if admin already exists
        if Administrador.query.filter_by(email='admin@psicologia.com').first():
            print("Admin user already exists.")
            return

        admin = Administrador(
            nombre="Administrador",
            email="admin@psicologia.com",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully! (admin@psicologia.com / admin123)")

if __name__ == '__main__':
    seed_especialidades()
    seed_admin()
