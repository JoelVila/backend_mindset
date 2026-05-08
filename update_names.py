from app import create_app, db
from app.models import Psicologo
from werkzeug.security import generate_password_hash

app = create_app()

def update_data():
    with app.app_context():
        print("Actualizando nombres de psicólogos...")
        
        # 1. Renombrar psicólogos existentes que tengan nombres genéricos
        psicologos = Psicologo.query.all()
        nombres_reales = ["Dra. Elena García", "Dr. Carlos Ruiz", "Dra. Ana Martínez", "Dr. Luis Fernández"]
        
        for i, p in enumerate(psicologos):
            if "Joel" in p.nombre:
                nuevo_nombre = nombres_reales[i % len(nombres_reales)]
                p.nombre = nuevo_nombre
                p.apellido = "Especialista"
        
        # 2. Crear psicólogo de prueba 100% verificado
        test_email = "test_verificado@mindconnect.com"
        exists = Psicologo.query.filter_by(correo_electronico=test_email).first()
        
        if not exists:
            new_p = Psicologo(
                nombre="Dr. Test",
                apellido="Verificado",
                correo_electronico=test_email,
                contrasena_hash=generate_password_hash("Test1234"),
                verificado=True,
                ocr_verificado=True,
                biometrico_verificado=True,
                numero_colegiado="12345-V",
                bio="Psicólogo de prueba con todas las certificaciones validadas.",
                precio_online=50.00,
                anios_experiencia=10,
                onboarding_completado=True
            )
            db.session.add(new_p)
            print(f"Psicólogo de prueba creado: {test_email}")
        else:
            exists.verificado = True
            exists.ocr_verificado = True
            exists.biometrico_verificado = True
            print("Psicólogo de prueba ya existía, se han actualizado sus verificaciones.")
            
        db.session.commit()
        print("¡Base de datos actualizada con éxito!")

if __name__ == "__main__":
    update_data()
