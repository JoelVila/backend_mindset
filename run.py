from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, HistorialClinico, Informe, Factura, ResumenIngresos, Notificacion, Resena

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Psicologo': Psicologo,
        'Paciente': Paciente,
        'Especialidad': Especialidad,
        'Cita': Cita,
        'HistorialClinico': HistorialClinico,
        'Informe': Informe,
        'Factura': Factura,
        'ResumenIngresos': ResumenIngresos,
        'Notificacion': Notificacion,
        'Resena': Resena
    }


if __name__ == '__main__':
    app.run(debug=True)
