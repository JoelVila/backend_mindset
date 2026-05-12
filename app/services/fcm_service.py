import firebase_admin
from firebase_admin import credentials, messaging
import os
from flask import current_app

class FCMService:
    _initialized = False

    @classmethod
    def _initialize(cls):
        if not cls._initialized:
            try:
                # Buscar el archivo de credenciales en la raíz o en una ruta definida en env
                cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
                if not cred_path:
                    # Por defecto buscamos en la raíz del proyecto
                    cred_path = os.path.join(os.getcwd(), 'firebase-credentials.json')
                
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    cls._initialized = True
                    print("✅ [FCM] Firebase Admin inicializado correctamente.")
                else:
                    print(f"⚠️ [FCM] No se encontró el archivo de credenciales en {cred_path}")
            except Exception as e:
                print(f"❌ [FCM] Error inicializando Firebase Admin: {e}")

    @classmethod
    def send_push(cls, token, title, body, data=None):
        cls._initialize()
        if not cls._initialized:
            print("⚠️ [FCM] No se pudo enviar notificación: Firebase no inicializado.")
            return False
        
        if not token:
            print("⚠️ [FCM] No se pudo enviar notificación: Token vacío.")
            return False

        try:
            # Construir el mensaje
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},
                token=token,
            )

            # Enviar
            token_preview = token[:20] + '...' if len(token) > 20 else token
            print(f"[FCM] Intentando enviar a token: {token_preview}")
            response = messaging.send(message)
            print(f"[FCM] Notificaci\u00f3n enviada con \u00e9xito. Message ID: {response}")
            return True
        except Exception as e:
            print(f"[FCM] Error enviando notificaci\u00f3n push a token {token[:20]}...: {type(e).__name__}: {e}")
            return False

    @classmethod
    def send_to_topic(cls, topic, title, body, data=None):
        """Útil para anuncios generales o frases del día"""
        cls._initialize()
        if not cls._initialized: return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )
            response = messaging.send(message)
            print(f"✅ [FCM] Notificación a tópico '{topic}' enviada: {response}")
            return True
        except Exception as e:
            print(f"❌ [FCM] Error enviando notificación a tópico: {e}")
            return False
