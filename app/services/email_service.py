import smtplib
import ssl
import certifi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app
import random

class EmailService:
    def __init__(self, mail=None):
        # Keep mail param for compatibility, but we'll use smtplib directly
        self.mail = mail
    
    def _send_email_direct(self, recipient, subject, html_content, attachment_bytes=None, attachment_filename=None):
        """Helper method to send email using smtplib directly.
        
        Tries port 587 (STARTTLS) first, then falls back to port 465 (SSL)
        if the connection is blocked or times out.
        """
        smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_user = current_app.config.get('MAIL_USERNAME')
        smtp_pass = current_app.config.get('MAIL_PASSWORD')

        if not smtp_user or not smtp_pass:
            print("Error: SMTP credentials not found in config")
            return False

        # Build the message once
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = recipient

        part = MIMEText(html_content, "html")
        msg.attach(part)

        if attachment_bytes and attachment_filename:
            attachment = MIMEApplication(attachment_bytes, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
            msg.attach(attachment)

        raw_msg = msg.as_string()
        context = ssl.create_default_context(cafile=certifi.where())
        TIMEOUT = 15  # seconds

        # --- Attempt 1: Port 587 with STARTTLS ---
        try:
            print(f"[EMAIL] Intentando conexión STARTTLS a {smtp_server}:587...")
            with smtplib.SMTP(smtp_server, 587, timeout=TIMEOUT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipient, raw_msg)
            print(f"[EMAIL] Correo enviado exitosamente a {recipient} (puerto 587)")
            return True
        except Exception as e:
            print(f"Error in _send_email_direct: {e}")

        # --- Attempt 2: Port 465 with SSL (fallback) ---
        try:
            print(f"[EMAIL] Intentando conexión SSL a {smtp_server}:465...")
            with smtplib.SMTP_SSL(smtp_server, 465, context=context, timeout=TIMEOUT) as server:
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipient, raw_msg)
            print(f"[EMAIL] Correo enviado exitosamente a {recipient} (puerto 465)")
            return True
        except Exception as e:
            print(f"Error in _send_email_direct: {e}")

        print(f"[EMAIL] No se pudo enviar el correo a {recipient}. Verifica el firewall y las credenciales SMTP.")
        return False

    def generate_reset_token(self):
        """Generate a 6-digit numeric code for password reset"""
        return str(random.randint(100000, 999999))
    
    def send_password_reset_email(self, email, token, user_type):
        """
        Send password reset email with token
        """
        try:
            user_type_label = 'Paciente' if user_type == 'paciente' else 'Psicólogo'
            subject = 'Restablece tu contraseña - MindConnect'
            
            # Email body
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: #1E5EFF;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                    }}
                    .content {{
                        background-color: #f5f7fa;
                        padding: 30px;
                        border-radius: 0 0 8px 8px;
                    }}
                    .token-box {{
                        background-color: white;
                        border: 2px solid #1E5EFF;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 20px 0;
                        text-align: center;
                        font-size: 36px;
                        font-weight: bold;
                        letter-spacing: 8px;
                        color: #1E5EFF;
                    }}
                    .warning {{
                        color: #dc3545;
                        font-size: 14px;
                        margin-top: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Restablecimiento de Contraseña</h1>
                    </div>
                    <div class="content">
                        <p>Hola,</p>
                        <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta de <strong>{user_type_label}</strong> en MindConnect.</p>
                        
                        <p>Usa el siguiente código para restablecer tu contraseña:</p>
                        
                        <div class="token-box">
                            {token}
                        </div>
                        
                        <p style="text-align: center; color: #666; font-size: 13px;">Introduce este código de 6 dígitos en la app.</p>
                        
                        <p><strong>Este código expirará en 1 hora.</strong></p>
                        
                        <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
                        
                        <div class="warning">
                            ⚠️ Por seguridad, nunca compartas este código con nadie.
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2026 MindConnect - Plataforma de Salud Mental</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email_direct(email, subject, html_content)
            
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False

    def send_appointment_confirmation(self, email, appointment_details):
        """
        Send appointment confirmation email
        """
        try:
            subject = '📅 Cita Confirmada - MindConnect'
            
            video_link_section = ""
            if appointment_details.get('tipo_cita') == 'Videollamada' and appointment_details.get('enlace_meet'):
                video_link_section = f"""
                <div style="background-color: #EBF4FF; border-left: 4px solid #1E5EFF; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; color: #1E5EFF;">Enlace de la Videollamada:</p>
                    <p style="margin: 10px 0;"><a href="{appointment_details['enlace_meet']}" style="color: #1E5EFF; text-decoration: underline; font-family: monospace;">{appointment_details['enlace_meet']}</a></p>
                    <p style="margin: 0; font-size: 12px; color: #666;">Haz clic en el enlace a la hora de tu cita para entrar en la sala.</p>
                </div>
                """
            
            phone_number_section = ""
            if 'Llamada' in appointment_details.get('tipo_cita', '') and appointment_details.get('psicologo_telefono'):
                phone_number_section = f"""
                <div style="background-color: #F0FDF4; border-left: 4px solid #10B981; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; color: #10B981;">Número de Teléfono:</p>
                    <p style="margin: 10px 0; font-size: 20px; color: #1e293b; font-weight: bold;">{appointment_details['psicologo_telefono']}</p>
                    <p style="margin: 0; font-size: 12px; color: #666;">Tu psicólogo te llamará a este número o puedes contactarle a la hora acordada.</p>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f5f7fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .details-box {{ background-color: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e1e4e8; }}
                    .detail-row {{ margin-bottom: 10px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px; }}
                    .detail-label {{ font-weight: bold; color: #666; font-size: 14px; }}
                    .detail-value {{ font-size: 16px; color: #1e293b; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📅 Tu Cita ha sido Confirmada</h1>
                    </div>
                    <div class="content">
                        <p>Hola,</p>
                        <p>¡Buenas noticias! Tu pago ha sido procesado correctamente y tu cita ha sido programada con éxito.</p>
                        
                        <div class="details-box">
                            <div class="detail-row">
                                <div class="detail-label">Psicólogo/a</div>
                                <div class="detail-value">{appointment_details['psicologo_nombre']}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Fecha</div>
                                <div class="detail-value">{appointment_details['fecha']}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Hora</div>
                                <div class="detail-value">{appointment_details['hora']}</div>
                            </div>
                            <div class="detail-row">
                                <div class="detail-label">Tipo de Sesión</div>
                                <div class="detail-value" style="text-transform: capitalize;">{appointment_details['tipo_cita']}</div>
                            </div>
                        </div>

                        {video_link_section}
                        {phone_number_section}

                        <p>Recuerda que puedes ver todos los detalles de tu cita y gestionar tus sesiones desde la aplicación MindConnect.</p>
                        
                        <p>Si tienes alguna duda o necesitas cancelar, por favor contacta con nosotros lo antes posible.</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 MindConnect - Plataforma de Salud Mental</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email_direct(email, subject, html_content)
            
        except Exception as e:
            print(f"Error sending appointment confirmation email: {e}")
            return False

    def send_invoice_email(self, email, invoice_details, pdf_bytes, pdf_filename):
        """
        Send invoice email with PDF attachment
        """
        try:
            subject = f"Factura de tu sesión - {invoice_details['numero_factura']} - MindConnect"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1E5EFF; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f5f7fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .details-box {{ background-color: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e1e4e8; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📄 Tu Factura MindConnect</h1>
                    </div>
                    <div class="content">
                        <p>Hola,</p>
                        <p>Te adjuntamos la factura correspondiente a tu reciente sesión de psicología.</p>
                        
                        <div class="details-box">
                            <p><strong>Nº Factura:</strong> {invoice_details['numero_factura']}</p>
                            <p><strong>Concepto:</strong> {invoice_details['concepto']}</p>
                            <p><strong>Importe Total:</strong> {invoice_details['total']} €</p>
                        </div>

                        <p>Puedes encontrar el detalle completo en el documento PDF adjunto a este correo.</p>
                        <p>Gracias por confiar en MindConnect.</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 MindConnect - Plataforma de Salud Mental</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email_direct(email, subject, html_content, pdf_bytes, pdf_filename)
            
        except Exception as e:
            print(f"Error sending invoice email: {e}")
            return False
    def send_cancellation_email(self, email, appointment_details, refund_details):
        """
        Send appointment cancellation email with refund details
        """
        try:
            subject = '❌ Cita Cancelada - MindConnect'
            
            refund_text = "Se ha procesado un reembolso del 100%."
            if refund_details.get('penalty_applied'):
                refund_text = f"Se ha procesado un reembolso parcial (70%). Se ha aplicado una penalización del 30% ({refund_details['penalty_amount']} €) por cancelar con menos de 24 horas de antelación."

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #EF4444; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f5f7fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .details-box {{ background-color: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e1e4e8; }}
                    .penalty {{ color: #EF4444; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>❌ Tu Cita ha sido Cancelada</h1>
                    </div>
                    <div class="content">
                        <p>Hola,</p>
                        <p>Te confirmamos que tu cita ha sido cancelada correctamente.</p>
                        
                        <div class="details-box">
                            <p><strong>Psicólogo/a:</strong> {appointment_details['psicologo_nombre']}</p>
                            <p><strong>Fecha:</strong> {appointment_details['fecha']}</p>
                            <p><strong>Hora:</strong> {appointment_details['hora']}</p>
                        </div>

                        <p><strong>Detalles del reembolso:</strong></p>
                        <p>{refund_text}</p>
                        
                        <p>El dinero volverá a tu cuenta en un plazo de 5 a 10 días hábiles según tu entidad bancaria.</p>
                        <p>Si tienes alguna duda, por favor contacta con nosotros.</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 MindConnect - Plataforma de Salud Mental</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email_direct(email, subject, html_content)
            
        except Exception as e:
            print(f"Error sending cancellation email: {e}")
            return False
