# Documentación de Seguridad y Endpoints de la API

Este documento detalla la implementación de seguridad en la API del proyecto de Psicología, explicando cómo funciona la autenticación y listando los endpoints disponibles.

## Mecanismo de Seguridad: JWT (JSON Web Token)

La API utiliza **JWT (JSON Web Tokens)** para asegurar la comunicación. El sistema es "Stateless" (sin estado), lo que significa que el servidor no guarda sesiones.

### ¿Cómo funciona?

1.  **Login**: El usuario (Paciente o Psicólogo) envía sus credenciales (email y contraseña) al endpoint de Login.
2.  **Token**: Si las credenciales son correctas, el servidor genera un **Token** encriptado y lo devuelve al usuario.
3.  **Acceso**: Para acceder a cualquier dato privado (como crear una cita o ver perfiles), el usuario debe enviar este Token en cada petición.

El Token debe ir en la cabecera HTTP (**Header**) de la siguiente manera:
`Authorization: Bearer <TU_TOKEN_AQUI>`

---

## Clasificación de Endpoints

### 1. Endpoints de IA y Herramientas (NUEVO)
Endpoints auxiliares que ayudan al usuario antes del registro o durante el uso de la app.

*   **`POST /main/analyze-document`** (OCR)
    *   **Función**: Extrae automáticamente datos de una foto de acreditación.
    *   **Acceso**: Público (No requiere token, para usarse en el registro).
    *   **Input**: Archivo de imagen (multipart/form-data, key=`documento`).
    *   **Respuesta**: JSON con `{ "numero_licencia": "...", "institucion": "..." }`.

### 2. Endpoints Públicos (Auth)
Sirven para entrar al sistema.

*   **`POST /auth/login`**
    *   **Función**: Iniciar sesión.
    *   **Body**: `{ "email": "...", "password": "...", "role": "paciente" }`
    *   **Respuesta**: Devuelve el `access_token`.

*   **`POST /auth/register`**
    *   **Función**: Crear una cuenta nueva.
    *   **Body (Psicólogo - ACTUALIZADO)**:
        ```json
        {
          "role": "psicologo",
          "email": "psi@test.com",
          "password": "secret",
          "numero_licencia": "123456",
          "institucion": "Universidad Complutense",
          "documento_acreditacion": "URL_DEL_DOCUMENTO",
          "foto_psicologo": "URL_FOTO_PERFIL"
        }
        ```
    *   **Body (Paciente - ACTUALIZADO)**:
        ```json
        {
          "role": "paciente",
          "email": "juan@test.com",
          "password": "secret",
          "nombre": "Juan",
          "apellido": "Perez",
          "foto_paciente": "URL_FOTO_PERFIL"
        }
        ```

### 3. Endpoints Privados (Requieren Token)
**Si no envías el token, recibirás un error 401.**

#### Usuarios y Perfiles
*   **`GET /main/perfil_paciente`**: Devuelve los datos del paciente logueado.
*   **`GET /main/psicologos`**: Lista todos los psicólogos disponibles.

#### Gestión de Citas
*   **`POST /main/citas`**: Agendar una nueva cita.
*   **`GET /main/citas`**: Ver la lista de citas existentes.

#### Historial y Documentos
*   **`GET /main/historial/<id>`**: Ver el historial clínico.
*   **`POST /main/historial`**: Actualizar historial.
*   **`POST /main/informes`**: Crear informes.
*   **`POST /main/facturas`**: Generar facturas.

#### Sistema
*   **`GET /main/notificaciones`**: Ver notificaciones.

---

## Repositorio

🔗 **GitHub**: [https://github.com/JoelVila/backendPsicologia.git](https://github.com/JoelVila/backendPsicologia.git)
