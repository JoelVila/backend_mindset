from abc import ABC, abstractmethod

class VerificationAdapter(ABC):
    @abstractmethod
    def verify(self, identifier: str) -> dict:
        """
        Abstract method to verify a professional.
        Must return a dict with format:
        {
            "verified": bool,
            "msg": str,
            "nombre": str (optional),
            "numero_colegiado": str (optional),
            ...
        }
        """
        pass
