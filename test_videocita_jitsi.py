
import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from app import create_app, db
from app.models import Psicologo, Paciente, Cita
from app.services.cita_service import CitaService

class TestVideocitaJitsi(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.services.cita_service.GoogleCalendarAdapter')
    def test_crear_cita_videollamada_jitsi(self, MockCalendarAdapter):
        # 1. Setup Mock for Google Calendar
        mock_adapter_instance = MockCalendarAdapter.return_value
        # Mock create_event to return a fake event ID
        mock_adapter_instance.create_event.return_value = {
            'id': 'google_event_123',
            'htmlLink': 'http://google.calendar/event',
            'meetLink': None # We are testing that the Jitsi link is used as location, not necessarily a meet link
        }

        # 2. Call service to create appointment
        # Create fixtures
        psico = Psicologo(
            nombre="Dr. Test", 
            correo_electronico="psico@test.com",
            contrasena_hash="hashed",
            precio_online=50.0
        )
        paciente = Paciente(
            nombre="Paciente Test", 
            apellido="Test",
            correo_electronico="paciente@test.com",
            contrasena_hash="hashed",
            telefono="123456789",
            dni_nif="12345678A",
            fecha_nacimiento=date(1990, 1, 1),
            edad=30
        )
        db.session.add(psico)
        db.session.add(paciente)
        db.session.commit()

        # Data for appointment
        fecha_futura = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        data = {
            'id_psicologo': psico.id_psicologo,
            'fecha': fecha_futura,
            'hora': '10:00',
            'tipo_cita': 'videollamada'
        }

        print("\n--- Iniciando prueba de creación de Videollamada ---")
        nueva_cita, error, status = CitaService.agendar_cita(paciente.id_paciente, data)

        # 3. Assertions
        if error:
            self.fail(f"Error al agendar cita: {error}")

        print(f"✅ Cita creada con ID: {nueva_cita.id_cita}")
        print(f"🔗 Enlace Meet generado: {nueva_cita.enlace_meet}")

        # Check Jitsi Link format
        self.assertIsNotNone(nueva_cita.enlace_meet)
        self.assertIn("meet.jit.si", nueva_cita.enlace_meet)
        self.assertIn("PsicoApp-", nueva_cita.enlace_meet)

        # Check interaction with Google Calendar Adapter
        print("🔍 Verificando integración con Google Calendar...")
        self.assertTrue(MockCalendarAdapter.called)
        
        # Verify arguments passed to create_event
        # We need to get the arguments passed to create_event
        args, kwargs = mock_adapter_instance.create_event.call_args
        
        print(f"📍 Location pasado a Google Calendar: {kwargs.get('location')}")
        
        self.assertEqual(kwargs.get('location'), nueva_cita.enlace_meet)
        self.assertIn(nueva_cita.enlace_meet, kwargs.get('description'))
        
        print("✅ Prueba Exitosa: Se generó enlace Jitsi y se pasó como location a Google Calendar.")

if __name__ == '__main__':
    unittest.main()
