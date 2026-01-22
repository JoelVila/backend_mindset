import os
import datetime
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.adapters.calendar_interface import CalendarInterface

class GoogleCalendarAdapter(CalendarInterface):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'credentials.json'

    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        if os.path.exists(self.SERVICE_ACCOUNT_FILE):
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
                )
                self.service = build('calendar', 'v3', credentials=self.creds)
            except Exception as e:
                print(f"Error autenticando con Google: {e}")
        else:
            print(f"Archivo de credenciales {self.SERVICE_ACCOUNT_FILE} no encontrado.")

    def create_event(self, summary, start_time, end_time, description=None, attendee_emails=None, location=None):
        if not self.service:
            print("Servicio de Google Calendar no inicializado.")
            return None

        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            # 'conferenceData': {
            #     'createRequest': {
            #         'requestId': f"meet-{int(datetime.datetime.now().timestamp())}",
            #         'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            #     }
            # },
            'attendees': [{'email': email} for email in attendee_emails] if attendee_emails else [],
        }

        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

        try:
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            return {
                'id': event.get('id'),
                'htmlLink': event.get('htmlLink'),
                'meetLink': event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
            }
        except Exception as e:
            print(f"Error creando evento en Google Calendar: {e}")
            return None
