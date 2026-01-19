# API Psicología - Backend

API REST desarrollada con Flask para gestión de un sistema de psicología.

## 📋 Requisitos Previos

- Python 3.9 o superior
- Docker y Docker Compose (recomendado)
- MySQL 8.0 (si no usas Docker)
- Git

## 🚀 Instalación y Configuración

### Opción 1: Con Docker (Recomendado)

1. **Clonar el repositorio**
```bash
git clone <URL_DEL_REPOSITORIO>
cd psicologia_api
```

2. **Levantar los servicios con Docker Compose**
```bash
docker-compose up --build
```

Esto levantará automáticamente:
- Base de datos MySQL en el puerto 3306
- API Flask en el puerto 5000

3. **Verificar que la API está funcionando**

Abre tu navegador o Postman y accede a:
```
http://localhost:5000/
```

### Opción 2: Sin Docker (Desarrollo Local)

1. **Clonar el repositorio**
```bash
git clone <URL_DEL_REPOSITORIO>
cd psicologia_api
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
```

3. **Activar entorno virtual**
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/Mac:
```bash
source .venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Configurar variables de entorno**

Asegúrate de tener MySQL instalado y ejecutándose. Luego edita el archivo `.env`:

```env
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=mysql+pymysql://root:TU_PASSWORD@localhost/psicologia
JWT_SECRET_KEY=834475f360a72e4d7d46368da2770021a92619dd8e
```

6. **Crear la base de datos**

Accede a MySQL y crea la base de datos:
```sql
CREATE DATABASE psicologia;
```

7. **Ejecutar migraciones**
```bash
flask db upgrade
```

8. **Ejecutar la aplicación**
```bash
python run.py
```

La API estará disponible en `http://localhost:5000`

## 🔧 Poblar la Base de Datos (Opcional)

Para agregar datos de prueba, ejecuta:
```bash
python seed.py
```

## 📡 Endpoints Principales

### Autenticación (Públicos - No requieren JWT)

#### Registro de Paciente
```http
POST /register_paciente
Content-Type: application/json

{
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "password": "password123",
  "edad": 30,
  "telefono": "123456789",
  "tipo_paciente": "particular",
  "tipo_tarjeta": "visa"
}
```

#### Login de Paciente
```http
POST /login_paciente
Content-Type: application/json

{
  "email": "juan@example.com",
  "password": "password123"
}
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "role": "paciente"
}
```

### Endpoints Protegidos (Requieren JWT)

Para usar estos endpoints, debes incluir el token JWT en el header:
```http
Authorization: Bearer <tu_token_aqui>
```

#### Obtener Perfil de Paciente
```http
GET /perfil_paciente
Authorization: Bearer <token>
```

#### Listar Psicólogos
```http
GET /psicologos
Authorization: Bearer <token>
```

#### Crear Cita
```http
POST /citas
Authorization: Bearer <token>
Content-Type: application/json

{
  "fecha": "2024-12-20",
  "hora": "10:30",
  "id_psicologo": 1,
  "id_paciente": 1,
  "tipo_cita": "consulta",
  "precio_cita": 50.00
}
```

#### Listar Citas
```http
GET /citas
Authorization: Bearer <token>
```

#### Obtener Historial Clínico
```http
GET /historial/<id_paciente>
Authorization: Bearer <token>
```

#### Obtener Notificaciones
```http
GET /notificaciones
Authorization: Bearer <token>
```

## 📱 Integración con Flutter

### Ejemplo de Login desde Flutter

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<String?> login(String email, String password) async {
  final url = Uri.parse('http://localhost:5000/login_paciente');
  
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['access_token'];
  }
  return null;
}
```

### Ejemplo de Request con JWT

```dart
Future<Map<String, dynamic>?> getPerfil(String token) async {
  final url = Uri.parse('http://localhost:5000/perfil_paciente');
  
  final response = await http.get(
    url,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  }
  return null;
}
```

## 🛠️ Verificar Docker

Para verificar que Docker está funcionando correctamente, ejecuta:
```bash
python verify_docker.py
```

## 📝 Notas Importantes

- **URL Base**: Cuando uses la API desde Flutter en un emulador Android, usa `http://10.0.2.2:5000` en lugar de `localhost:5000`
- **URL Base**: Para dispositivos iOS, asegúrate de usar la IP local de tu máquina (ej: `http://192.168.1.X:5000`)
- **JWT Token**: Guarda el token después del login para usarlo en requests subsecuentes
- **CORS**: Si tienes problemas de CORS desde Flutter web, se puede configurar en el backend

## 🔒 Seguridad

- Cambia `JWT_SECRET_KEY` en producción
- No subas el archivo `.env` al repositorio (ya está en `.gitignore`)
- Usa HTTPS en producción

## 🐛 Troubleshooting

### Error de conexión a MySQL
- Verifica que MySQL esté ejecutándose
- Verifica las credenciales en `.env` o `docker-compose.yml`

### Error "Address already in use"
- El puerto 5000 o 3306 ya está en uso
- Cierra otros servicios o cambia el puerto en `docker-compose.yml`

### No se pueden crear las tablas
- Ejecuta las migraciones: `flask db upgrade`
- O levanta con Docker que lo hace automáticamente
