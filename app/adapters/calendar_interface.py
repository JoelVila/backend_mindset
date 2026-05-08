from abc import ABC, abstractmethod

class CalendarInterface(ABC):
    @abstractmethod
    def create_event(self, summary, start_time, end_time, description=None, attendee_emails=None):
        """
        Crea un evento en el calendario externo.
        Debe retornar un diccionario con 'meetLink' (si existe) y 'id' del evento.
        """
        pass
