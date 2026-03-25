from app import create_app, db
from app.models import Cita
import json

app = create_app()
with app.app_context():
    # Buscamos la cita por ID
    cita = Cita.query.filter_by(id=148).first()
    if cita:
        data = {
            "id": cita.id,
            "estado": cita.estado,
            "id_paciente": cita.id_paciente,
            "id_psicologo": cita.id_psicologo,
            "precio": float(cita.precio_cita) if cita.precio_cita else 0.0
        }
        print(f"DEBUG_RESULT: {json.dumps(data)}")
    else:
        print("DEBUG_RESULT: NOT_FOUND")
