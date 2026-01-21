
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

#### **Login de Psicólogo**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/auth/login`
*   **Body (JSON):**
    ```json
    {
      "email": "maria.gonzalez@example.com",
      "password": "password123",
      "role": "psicologo"
    }
    ```

---

### 2. 👤 Gestión de Perfiles (Requiere Token)

#### **Ver Mi Perfil (Paciente)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/perfil_paciente`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`

#### **Actualizar Mi Perfil (Paciente)**
*   **Método:** `PUT`
*   **URL:** `{{ base_url }}/main/pacientes/perfil`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`
*   **Body (JSON):**
    ```json
    {
      "nombre": "Carlos Alberto",
      "telefono": "666999888"
    }
    ```

#### **Ver Mi Perfil (Psicólogo)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/psicologos/perfil`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`

#### **Actualizar Mi Perfil (Psicólogo)**
*   **Método:** `PUT`
*   **URL:** `{{ base_url }}/main/psicologos/perfil`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`
*   **Body (JSON):**
    ```json
    {
      "bio": "Nueva biografía actualizada...",
      "precio_presencial": 55,
      "precio_online": 45
    }
    ```

---

### 3. 🧠 Psicólogos y Búsqueda

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
*   **Query Param:** `fecha=2026-02-20` (IMPORTANTE: Fecha futura)

---

### 4. 📅 Citas

#### **Agendar Cita (Paciente)**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/citas/agendar`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`
*   **Body (JSON):**
    ```json
    {
      "id_psicologo": 1,
      "fecha": "2024-05-20",
      "hora": "10:00",
      "tipo_cita": "videollamada",
      "motivo": "Ansiedad recurrente"
    }
    ```

#### **Mis Citas (Paciente)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/pacientes/citas`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`
*   **Query Param:** `estado=proximas` (opcional)

#### **Mis Citas (Psicólogo)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}Z`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`

---

### 5. 📄 Informes e Historial

#### **Ver Informes (Paciente)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/pacientes/informes`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`

#### **Ver Informes de mis Pacientes (Psicólogo)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/psicologos/informes`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`

#### **Crear Informe (Psicólogo)**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/psicologos/informes`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`
*   **Body (JSON):**
    ```json
    {
      "id_paciente": 1,
      "titulo": "Informe Inicial",
      "contenido": "El paciente presenta...",
      "diagnostico": "Trastorno de Ansiedad Generalizada",
      "tratamiento": "Terapia Cognitivo-Conductual"
    }
    ```

#### **Ver Historial Clínico (Anamnesis)**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/historial/1` (ID del Paciente)
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`

---

### 6. 🔔 Notificaciones y Facturas

#### **Ver Notificaciones**
*   **Método:** `GET`
*   **URL:** `{{ base_url }}/main/notificaciones`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}` (o psicólogo)

#### **Generar Factura**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/facturas`
*   **Headers:** `Authorization: Bearer {{ token_psicologo }}`
*   **Body (JSON):**
    ```json
    {
      "id_paciente": 1,
      "concepto": "Sesión de terapia online",
      "base_imponible": 50,
      "iva": 10.5
    }
    ```

---

### 7. 📸 Verificación y Biometría (Nuevo)

#### **Validar Documento (OCR Psicólogo)**
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/analyze-document`
*   **Body (Multipart Form):**
    *   `file`: [Seleccionar archivo Imagen (.jpg/.png)] - *Nota: PDF no soportado en esta versión*

#### **Verificación Biométrica (DNI vs Selfie)** 🚀
*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/biometric/verify-identity`
*   **Body (Multipart Form):**
    *   `dni_image`: [Seleccionar archivo foto DNI frontal]
    *   `selfie_image`: [Seleccionar archivo selfie actual]
    
    *📥 **Respuesta esperada:** Score de coincidencia y booleano `verified`.*

---

### 8. ⚙️ Habilitar CORS (Importante para Flutter)

Si tu compañero va a conectar desde una app móvil real o un emulador externo, asegúrate de iniciar el servidor escuchando en todas las interfaces:

```powershell
flask run --host=0.0.0.0
```
Y en la app de Flutter, apuntar a tu IP local (ej: `http://192.168.1.35:5000`) en lugar de `localhost`.

---

### 9. 📹 Integración Google Meet (Videoconsultas)

#### **Crear Cita con Videollamada**
Cuando se agenda una cita con `tipo_cita: "videollamada"`, el sistema genera automáticamente un evento en Google Calendar y devuelve el enlace al evento para que psicólogo y paciente puedan unirse.

*   **Método:** `POST`
*   **URL:** `{{ base_url }}/main/citas/agendar`
*   **Headers:** `Authorization: Bearer {{ token_paciente }}`
*   **Body (JSON):**
    ```json
    {
      "id_psicologo": 1,
      "fecha": "2026-05-20",
      "hora": "10:00",
      "tipo_cita": "videollamada" 
    }
    ```
    *(Nota: `tipo_cita` debe ser exactamente "videollamada")*

*   **Respuesta Exitosa (201 Created):**
    ```json
    {
        "id": 15,
        "enlace_meet": "https://www.google.com/calendar/event?eid=...",
        "google_calendar_event_id": "cgp836c1mldlhg...",
        ...
    }
    ```

#### **Verificar Integración (Manual)**
1.  **Backend:** Revisa la respuesta JSON y busca el campo `enlace_meet`.
2.  **Google Calendar:** Entra en el calendario configurado (`GOOGLE_CALENDAR_ID`) y verifica que el evento se ha creado en el día/hora indicados.
3.  **Descripción del Evento:** Verifica que la descripción del evento en Calendar contiene los datos de contacto (emails) de psicólogo y paciente.

