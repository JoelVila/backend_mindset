from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, Anamnesis, Informe, Factura, Notificacion

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
    print("🚀 Iniciando servidor...")
    app.run(debug=True)
