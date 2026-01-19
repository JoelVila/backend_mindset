import requests
from bs4 import BeautifulSoup
import re
from app.adapters.verification_interface import VerificationAdapter

class CopcAdapter(VerificationAdapter):
    """
    Adapter for the COPC (Col·legi Oficial de Psicologia de Catalunya) website.
    It adapts the scraping logic into a clean verify() interface.
    """
    
    BASE_URL = "https://copc-staging.indaws.cloud/es/colegiat?tec_num_colegiat={}"
    
    def verify(self, numero_colegiado: str) -> dict:
        if not numero_colegiado:
            return {"verified": False, "msg": "Número de colegiado no proporcionado"}

        # Limpiar el número (quitar espacios, letras si las hay)
        numero_limpio = re.sub(r'\D', '', str(numero_colegiado))
        
        url = self.BASE_URL.format(numero_limpio)
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Verificar si aparece el mensaje de "no encontrado"
            not_found_msg = soup.find(string=re.compile("No se han encontrado colegiados", re.I))
            if not_found_msg:
                return {"verified": False, "msg": "No se encontró ningún psicólogo con ese número en el COPC"}
            
            # 2. Intentar extraer los datos de la tabla de resultados
            results_table = soup.find('table')
            if not results_table:
                return {"verified": False, "msg": "Error al analizar la estructura de la web (tabla no encontrada)"}
                
            rows = results_table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # El número suele estar en la primera columna
                    num_encontrado = cols[0].get_text(strip=True)
                    # El nombre suele estar en la segunda columna dentro de un span/a
                    nombre_encontrado = cols[1].get_text(strip=True)
                    
                    if num_encontrado == numero_limpio:
                        return {
                            "verified": True,
                            "nombre": nombre_encontrado,
                            "numero_colegiado": num_encontrado,
                            "msg": "Psicólogo verificado correctamente en el COPC",
                            "institucion": "COPC (Catalunya)"
                        }
            
            return {"verified": False, "msg": "El número no coincide exactamente con los registros activos"}

        except Exception as e:
            return {"verified": False, "msg": f"Error de conexión con la web del COPC: {str(e)}"}
