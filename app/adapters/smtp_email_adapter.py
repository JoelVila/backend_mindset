import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.adapters.email_interface import EmailInterface

class SmtpEmailAdapter(EmailInterface):
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
    def send_email(self, to_email, subject, body, is_html=False):
        if not self.smtp_user or not self.smtp_password:
            print(f"[EMAIL MOCK] Credenciales SMTP no configuradas. Se simula envio a {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.smtp_user, to_email, text)
            server.quit()
            
            print(f"[EMAIL] Correo enviado exitosamente a {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Fallo al enviar correo a {to_email}: {e}")
            return False
