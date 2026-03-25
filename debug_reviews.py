from app import create_app, db
from app.models import Resena, Psicologo
from sqlalchemy import func

app = create_app()
with app.app_context():
    print("--- Estadisticas de Reseñas por Psicologo ---")
    stats = db.session.query(
        Resena.id_psicologo,
        Psicologo.nombre,
        func.count(Resena.id_resena).label('count'),
        func.avg(Resena.puntuacion).label('avg')
    ).join(Psicologo, Resena.id_psicologo == Psicologo.id_psicologo)\
     .group_by(Resena.id_psicologo, Psicologo.nombre).all()
    
    for s in stats:
        print(f"ID: {s[0]} | Nombre: {s[1]} | Conteo: {s[2]} | Media: {s[3]}")
    
    if not stats:
        print("No se encontraron reseñas en la base de datos.")
