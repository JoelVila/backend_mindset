from abc import ABC, abstractmethod

class EmailInterface(ABC):
    @abstractmethod
    def send_email(self, to_email, subject, body, is_html=False):
        """
        Envía un correo electrónico.
        :param to_email: Destinatario
        :param subject: Asunto
        :param body: Cuerpo del mensaje
        :param is_html: Booleano indicando si el cuerpo es HTML
        :return: True si se envió correctamente, False en caso contrario
        """
        pass
