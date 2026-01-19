import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def verify_api():
    print("🔍 Verificando API (Endpoints actuales)...")
    
    # 1. Esperar a que el servidor responda
    print(f"   Conectando a {BASE_URL}...")
    try:
        requests.get(BASE_URL)
    except:
        pass # Es normal si la ruta raíz no devuelve nada, solo probamos conexión

    # 2. Registrar Usuario de Prueba
    register_url = f"{BASE_URL}/auth/register"
    user_email = f"test_user_{int(time.time())}@example.com" # Email único
    user_data = {
        "role": "paciente",
        "email": user_email,
        "password": "password123",
        "nombre": "Test",
        "apellido": "User",
        "edad": 30,
        "telefono": "123456789"
    }
    
    print(f"\n1. Registrando usuario en {register_url}...")
    try:
        response = requests.post(register_url, json=user_data)
        if response.status_code == 201:
            print("   ✅ SUCCESS: Usuario registrado.")
        else:
            print(f"   ❌ ERROR: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return

    # 3. Login
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "email": user_email,
        "password": "password123",
        "role": "paciente"
    }
    
    print(f"\n2. Iniciando sesión en {login_url}...")
    token = None
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print("   ✅ SUCCESS: Login correcto.")
            print(f"      Token: {token[:20]}...")
        else:
            print(f"   ❌ ERROR: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        return

    # 4. Consultar Psicólogos (Público)
    psico_url = f"{BASE_URL}/main/psicologos/search"
    print(f"\n3. Buscando psicólogos en {psico_url}...")
    try:
        response = requests.get(psico_url)
        if response.status_code == 200:
            psicologos = response.json()
            print(f"   ✅ SUCCESS: Se encontraron {len(psicologos)} psicólogos.")
        else:
            print(f"   ❌ ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")

if __name__ == "__main__":
    verify_api()
