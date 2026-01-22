
import os
import sys
from datetime import datetime, timedelta
from app.adapters.google_calendar_adapter import GoogleCalendarAdapter
import uuid

def test_real_calendar_event():
    print("🚀 Iniciando prueba REAL de creación de evento en Google Calendar...")

    # 1. Initialize Adapter
    try:
        adapter = GoogleCalendarAdapter()
        if not adapter.service:
            print("❌ Error: No se pudo inicializar el servicio de Google Calendar. Verifica credentials.json.")
            return
    except Exception as e:
        print(f"❌ Error al inicializar adaptador: {e}")
        return

    # 2. Define Event Data
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)
    
    # Generate unique Jitsi link
    jitsi_link = f"https://meet.jit.si/PsicoApp-TEST-{uuid.uuid4().hex[:8]}"

    summary = "📅 Cita de Prueba - PsicoApp (Videollamada)"
    description = (
        f"Esta es una prueba de integración real.\n\n"
        f"🔗 **ENLACE A LA VIDEOLLAMADA:** {jitsi_link}\n\n"
        f"Si ves este evento en tu calendario con el enlace de ubicación, ¡funciona!"
    )
    
    # Use a dummy email list or empty if you don't want to spam anyone, 
    # but the authorized user (owner of credentials) should see it on their primary calendar.
    # We will try to add the owner's email if possible, or just create it on the primary calendar.
    attendee_emails = [] 

    print(f"📝 Creando evento para: {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"📍 Location (Jitsi): {jitsi_link}")

    # 3. Create Event
    try:
        result = adapter.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendee_emails=attendee_emails,
            location=jitsi_link
        )

        if result:
            print("\n✅ ¡Evento creado exitosamente!")
            print(f"🆔 ID del evento: {result.get('id')}")
            print(f"🔗 Link al evento: {result.get('htmlLink')}")
            print(f"📹 Ubicación guardada: {jitsi_link}")
            print("👉 Por favor revisa tu Google Calendar para confirmar.")
        else:
            print("\n❌ El evento no devolvió resultados. Algo pudo fallar silenciosamente.")

    except Exception as e:
        print(f"\n❌ Excepción al crear evento: {e}")

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    test_real_calendar_event()
