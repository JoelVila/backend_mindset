
# 🧪 Insomnia & Postman Testing Guide - Psicología API

Este documento contiene la información necesaria para configurar Insomnia (o Postman) y probar todos los endpoints disponibles en la API de Psicología, incluyendo las nuevas funcionalidades de biometría y roles.

## 🌍 Configuración del Entorno (Environment)

Crea un **Environment** en Insomnia con las siguientes variables para no tener que escribirlas todo el tiempo:

```json
{
  "base_url": "http://127.0.0.1:5000",
  "token_paciente": "",
  "token_psicologo": ""
}
```
*Nota: Los tokens se rellenarán automáticamente tras hacer Auth/Login si configuras chaining, o cópialos y pégalos manualmene.*

---

## 📂 Colección de Endpoints

### 1. 🔐 Autenticación (Auth)

#### **Registro de Paciente**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/register_paciente`
*   **Body (JSON):**
    ```json
    {
      "nombre": "Carlos",
      "apellido": "Gómez",
      "email": "carlos@test.com",
      "password": "password123",
      "telefono": "666112233",
      "dni_nif": "12345678A",
      "fecha_nacimiento": "1990-05-15",
      "foto_perfil": "url_o_base64_opcional"
    }
    ```

#### **Login de Paciente**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/login_paciente`
*   **Body (JSON):**
    ```json
    {
      "email": "carlos@test.com",
      "password": "password123"
    }
    ```
    *📥 **Respuesta:** Copia el `access_token` recibido.*

#### **Login de Psicólogo (Web - Admin Panel)**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/auth/login`
*   **Body (JSON):**
    ```json
    {
      "email": "admin@psicologia.com",
      "password": "admin123"
    }
    ```

---

### 2. 🧠 Psicólogos y Búsqueda

#### **Obtener Especialidades (Público)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/especialidades`

#### **Buscar Psicólogos (Filtros Avanzados)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/psicologos/search`
*   **Query Params (Opcionales):**
    *   `q`: "ansiedad" (texto libre)
    *   `especialidad`: "Psicología Clínica"
    *   `precio_min`: 0
    *   `precio_max`: 50
    *   `ubicacion`: "Barcelona"

#### **Ver Disponibilidad de un Psicólogo**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/psicologos/1/disponibilidad`
*   **Query Param:** `fecha=2024-02-20`

---

### 3. 📅 Citas (Requiere Token Paciente)

> **Header (Headers):**  
> `Authorization`: `Bearer {{ token_paciente }}`

#### **Agendar Cita**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/citas/agendar`
*   **Body (JSON):**
    ```json
    {
      "id_psicologo": 1,
      "fecha": "2024-02-20",
      "hora": "10:00",
      "tipo_cita": "online",
      "motivo": "Tengo mucha ansiedad últimamente"
    }
    ```

#### **Mis Citas (Como Paciente)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/pacientes/citas`
*   **Query Param:** `estado=proximas` (opcional)

---

### 4. 📸 Verificación y Biometría (Nuevo)

#### **Validar Documento (OCR Psicólogo)**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/analyze-document`
*   **Body (Multipart Form):**
    *   `file`: [Seleccionar archivo PDF o Imagen del título]

#### **Verificación Biométrica (DNI vs Selfie)** 🚀
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/biometric/verify-identity`
*   **Body (Multipart Form):**
    *   `dni_image`: [Seleccionar archivo foto DNI frontal]
    *   `selfie_image`: [Seleccionar archivo selfie actual]
    
    *📥 **Respuesta esperada:** Score de coincidencia y booleano `verified`.*

---

### 5. ⚙️ Habilitar CORS (Importante para Flutter)

Si tu compañero va a conectar desde una app móvil real o un emulador externo, asegúrate de iniciar el servidor escuchando en todas las interfaces:

```powershell
flask run --host=0.0.0.0
```
Y en la app de Flutter, apuntar a tu IP local (ej: `http://192.168.1.35:5000`) en lugar de `localhost`.
