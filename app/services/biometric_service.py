import face_recognition
import cv2
import numpy as np
import os

class BiometricService:
    def __init__(self):
        # Umbral para considerar que es la misma persona (menor es más estricto)
        # 0.6 es el estándar de la librería, 0.5 es más seguro.
        self.tolerance = 0.5 

    def _load_image(self, image_path_or_bytes):
        """
        Carga una imagen desde una ruta de archivo o desde bytes.
        """
        try:
            if isinstance(image_path_or_bytes, str):
                if not os.path.exists(image_path_or_bytes):
                    raise FileNotFoundError(f"Imagen no encontrada: {image_path_or_bytes}")
                image = face_recognition.load_image_file(image_path_or_bytes)
            else:
                # Asumimos que son bytes (ej: vienen de request.files['...'].read())
                nparr = np.frombuffer(image_path_or_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                # Convertir de BGR (OpenCV) a RGB (face_recognition)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image
        except Exception as e:
            raise ValueError(f"Error cargando la imagen: {str(e)}")

    def verify_identity(self, dni_image_source, selfie_image_source):
        """
        Compara la foto del DNI con la selfie para verificar si son la misma persona.
        Retorna un diccionario con el resultado.
        """
        try:
            # 1. Cargar imágenes
            img_dni = self._load_image(dni_image_source)
            img_selfie = self._load_image(selfie_image_source)

            # 2. Detectar caras (Encodings)
            # face_encodings devuelve una lista de arrays (uno por cada cara encontrada)
            dni_encodings = face_recognition.face_encodings(img_dni)
            selfie_encodings = face_recognition.face_encodings(img_selfie)

            # 3. Validaciones previas
            if len(dni_encodings) == 0:
                return {
                    "verified": False, 
                    "error": "No se detectó ninguna cara en la foto del DNI."
                }
            if len(selfie_encodings) == 0:
                return {
                    "verified": False, 
                    "error": "No se detectó ninguna cara en la selfie."
                }
            
            # Tomamos la primera cara encontrada en cada foto (asumimos que son fotos individuales)
            dni_face_encoding = dni_encodings[0]
            selfie_face_encoding = selfie_encodings[0]

            # 4. Comparar caras
            # face_distance devuelve la distancia euclidiana. Menor distancia = más parecido.
            face_distances = face_recognition.face_distance([dni_face_encoding], selfie_face_encoding)
            distance = face_distances[0]
            
            # compare_faces devuelve True/False basado en la tolerancia
            results = face_recognition.compare_faces([dni_face_encoding], selfie_face_encoding, tolerance=self.tolerance)
            is_match = bool(results[0])

            # Calcular un porcentaje de confianza aproximado (inversamente proporcional a la distancia)
            # Distancia 0.0 -> 100% match. Distancia 0.6 -> Límite.
            confidence = max(0, (1.0 - distance)) * 100

            return {
                "verified": is_match,
                "distance": float(distance),
                "confidence_score": round(confidence, 2),
                "message": "Identidad verificada correctamente" if is_match else "Las caras no coinciden"
            }

        except Exception as e:
            return {
                "verified": False,
                "error": f"Error interno en verificación biométrica: {str(e)}"
            }
