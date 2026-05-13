import os
import requests
import base64
from app.adapters.email_interface import EmailInterface

class BrevoEmailAdapter(EmailInterface):
    def __init__(self):
        self.api_key = os.getenv('BREVO_API_KEY')
        self.sender_email = os.getenv('SMTP_USER', 'noreply@mindconnect.com')
        self.sender_name = "MindConnect"
        self.api_url = "https://api.brevo.com/v3/smtp/email"

    def send_email(self, to_email, subject, body, is_html=True, attachment_bytes=None, attachment_filename=None):
        if not self.api_key:
            print("[BREVO ERROR] BREVO_API_KEY no configurada. No se puede enviar el correo.")
            return False

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }

        payload = {
            "sender": {"name": self.sender_name, "email": self.sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent" if is_html else "textContent": body
        }

        if attachment_bytes and attachment_filename:
            # Brevo requiere adjuntos en base64
            encoded_content = base64.b64encode(attachment_bytes).decode('utf-8')
            payload["attachment"] = [
                {
                    "content": encoded_content,
                    "name": attachment_filename
                }
            ]

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=15)
            if response.status_code in [201, 202, 200]:
                print(f"[BREVO] Correo enviado exitosamente a {to_email}")
                return True
            else:
                print(f"[BREVO ERROR] Error al enviar correo ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"[BREVO ERROR] Excepción al enviar correo a {to_email}: {e}")
            return False
