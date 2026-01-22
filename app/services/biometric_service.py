from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import numpy as np
from PIL import Image
import io

class BiometricService:
    def __init__(self):
        # Inicializar MTCNN (detector de caras) y InceptionResnetV1 (reconocimiento)
        # keep_all=True para detectar todas las caras (aunque solo usaremos 1)
        self.mtcnn = MTCNN(keep_all=False, select_largest=True, post_process=True)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
        
        # Umbral de distancia (Distance Threshold)
        # Menor a 0.7 - 0.6 suele ser la misma persona.
        # Ajustaremos a 0.75 para ser tolerantes pero seguros.
        self.threshold = 0.8

    def _load_image(self, image_source):
        """
        Carga imagen PIL desde bytes o path
        """
        try:
            if isinstance(image_source, bytes):
                return Image.open(io.BytesIO(image_source)).convert('RGB')
            elif isinstance(image_source, str):
                return Image.open(image_source).convert('RGB')
            else:
                # Asumimos que ya es PIL Image
                return image_source.convert('RGB')
        except Exception as e:
            raise ValueError(f"Error cargando imagen: {e}")

    def verify_identity(self, dni_image_bytes, selfie_image_bytes):
        """
        Compara DNI y Selfie usando Facenet (PyTorch).
        Devuelve dict con resultado.
        """
        try:
            img_dni = self._load_image(dni_image_bytes)
            img_selfie = self._load_image(selfie_image_bytes)

            # 1. Detectar y Recortar Caras (MTCNN)
            # Devuelve tensor de (1, 3, 160, 160) normalizado si encuentra cara, o None
            dni_cropped = self.mtcnn(img_dni)
            selfie_cropped = self.mtcnn(img_selfie)

            if dni_cropped is None:
                return {"verified": False, "error": "No se detectó ninguna cara en el DNI"}
            
            if selfie_cropped is None:
                return {"verified": False, "error": "No se detectó ninguna cara en el Selfie"}

            # 2. Calcular Embeddings (Vectores característicos)
            # Añadir dimensión de batch: (3, 160, 160) -> (1, 3, 160, 160) si es necesario
            # MTCNN ya devuelve el batch dimension si keep_all=False? No, devuelve 3D tensor?
            # Check: MTCNN with keep_all=False returns a tensor of shape (3, image_size, image_size) if a face is detected
            # We need to add batch dimension (1, 3, 160, 160)
            
            dni_input = dni_cropped.unsqueeze(0) 
            selfie_input = selfie_cropped.unsqueeze(0)

            with torch.no_grad():
                dni_embedding = self.resnet(dni_input)
                selfie_embedding = self.resnet(selfie_input)

            # 3. Calcular Distancia Euclidiana (L2 norm)
            distance = (dni_embedding - selfie_embedding).norm().item()

            # 4. Verificar
            is_match = distance < self.threshold
            
            # Calcular confianza aproximada (0 a 100)
            # Si threshold es 0.8:
            # Dist 0.0 -> Conf 100%
            # Dist 0.8 -> Conf 50% (límite)
            # Dist 1.6 -> Conf 0%
            confidence = max(0, (1 - (distance / (self.threshold * 2)))) * 100
            
            # Ajuste visual
            if is_match:
                 # Escalar confianza para que en caso de match sea > 70%
                 confidence = 70 + (30 * (1 - (distance / self.threshold)))

            return {
                "verified": is_match,
                "distance": round(distance, 4),
                "threshold_used": self.threshold,
                "confidence_score": round(confidence, 2),
                "message": "Identidad verificada" if is_match else "Las caras no coinciden"
            }

        except Exception as e:
            print(f"Biometric Error: {e}")
            return {"verified": False, "error": f"Error interno: {str(e)}"}
