import os
import ssl
import smtplib
import certifi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.adapters.email_interface import EmailInterface

TIMEOUT = 15  # segundos

class SmtpEmailAdapter(EmailInterface):
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
    def send_email(self, to_email, subject, body, is_html=False, attachment_bytes=None, attachment_filename=None):
        if not self.smtp_user or not self.smtp_password:
            print(f"[EMAIL MOCK] Credenciales SMTP no configuradas. Se simula envio a {to_email}: {subject}")
            return True

        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        if attachment_bytes and attachment_filename:
            attachment = MIMEApplication(attachment_bytes, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
            msg.attach(attachment)

        raw_msg = msg.as_string()
        context = ssl.create_default_context(cafile=certifi.where())

        # --- Intento 1: Puerto 587 con STARTTLS ---
        try:
            print(f"[EMAIL] Intentando STARTTLS en {self.smtp_server}:587...")
            with smtplib.SMTP(self.smtp_server, 587, timeout=TIMEOUT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, raw_msg)
            print(f"[EMAIL] Correo enviado exitosamente a {to_email} (puerto 587)")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Fallo puerto 587 para {to_email}: {e}")

        # --- Intento 2: Puerto 465 con SSL (fallback) ---
        try:
            print(f"[EMAIL] Intentando SSL en {self.smtp_server}:465...")
            with smtplib.SMTP_SSL(self.smtp_server, 465, context=context, timeout=TIMEOUT) as server:
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, raw_msg)
            print(f"[EMAIL] Correo enviado exitosamente a {to_email} (puerto 465)")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Fallo puerto 465 para {to_email}: {e}")

        print(f"[EMAIL] No se pudo enviar el correo a {to_email}. Verifica firewall y credenciales.")
        return False
