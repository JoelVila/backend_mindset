from gevent import monkey
monkey.patch_all()

from app import create_app, db
from app.models import Psicologo, Paciente, Especialidad, Cita, Anamnesis, Informe, Factura, Notificacion
from app.services.socket_service import socketio

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
    print("Iniciando servidor con WebSockets...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
