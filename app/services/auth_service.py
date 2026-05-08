from app import db
from app.models import Psicologo, Paciente, Administrador, Especialidad
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
import re
from email_validator import validate_email, EmailNotValidError

from app.errors import APIException
import json


class AuthService:
    @staticmethod
    def login(data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if not role:
            raise APIException("El rol es obligatorio", 400)

        email = email.strip().lower() if email else None

        if not email or not password:
             raise APIException("El correo y la contraseña son obligatorios", 400)
             
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise APIException("Formato de correo inválido", 400)
        if role == 'psicologo':
            user = Psicologo.query.filter_by(correo_electronico=email).first()
            if user and check_password_hash(user.contrasena_hash, password):
                identity = json.dumps({'id': user.id_psicologo, 'role': 'psicologo'})
                access_token = create_access_token(identity=identity)
                return {"access_token": access_token, "role": "psicologo"}, 200
                
        elif role == 'paciente':
            user = Paciente.query.filter_by(correo_electronico=email).first()
            if user and check_password_hash(user.contrasena_hash, password):
                identity = json.dumps({'id': user.id_paciente, 'role': 'paciente'})
                access_token = create_access_token(identity=identity)
                return {"access_token": access_token, "role": "paciente"}, 200

        elif role == 'admin':
            user = Administrador.query.filter_by(email=email).first()
            if user and check_password_hash(user.contrasena_hash, password):
                identity = json.dumps({'id': user.id_admin, 'role': 'admin'})
                access_token = create_access_token(identity=identity)
                return {"access_token": access_token, "role": "admin"}, 200
        
        raise APIException("Usuario o contraseña incorrectos", 401)

    @staticmethod
    def register(data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        role = data.get('role')
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if not email or not password:
            raise APIException("El correo y la contraseña son obligatorios", 400)

        try:
            validate_email(email)
        except EmailNotValidError:
            raise APIException("Formato de correo inválido", 400)

        if len(password) < 8:
            raise APIException("La contraseña debe tener al menos 8 caracteres", 400)
        
        if not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
            raise APIException("La contraseña debe contener al menos una mayúscula y un número", 400)
            if Psicologo.query.filter_by(correo_electronico=data.get('email')).first():
                 raise APIException("El correo ya está registrado", 400)
            
            num_cole = data.get('numero_licencia') or data.get('numero_colegiado')
            if not num_cole:
                 raise APIException("Registro fallido: El número de colegiado es obligatorio para la verificación.", 400)
            
            from app.adapters.copc_adapter import CopcAdapter
            adapter = CopcAdapter()
            verification = adapter.verify(num_cole)
            
            if not verification.get("verified"):
                raise APIException(f"Registro denegado: {verification.get('msg')}", 403)
            
            nombre_final = verification.get("nombre") or data.get('nombre')
            num_cole_final = verification.get("numero_colegiado") or num_cole
            
            new_user = Psicologo(
                nombre=nombre_final,
                correo_electronico=data.get('email'),
                contrasena_hash=generate_password_hash(data.get('password')),
                telefono=data.get('telefono'),
                apellido=data.get('apellido'),
                dni_nif=data.get('dni_nif'),
                direccion_fiscal=data.get('direccion_fiscal'),
                numero_colegiado=num_cole_final,
                cuenta_bancaria=data.get('numero_cuenta'),
                foto_psicologo=data.get('foto_perfil'),
                
                bio=data.get('bio'),
                anios_experiencia=data.get('anios_experiencia'),
                precio_online=data.get('precio_online'),
                banco=data.get('banco'),
                titular_cuenta=data.get('titular_cuenta')
            )
            
            especialidades_input = data.get('especialidades', [])
            especialidad_id_legacy = data.get('especialidad_id')
            
            if especialidad_id_legacy:
                if isinstance(especialidad_id_legacy, str):
                    esp = Especialidad.query.filter_by(nombre=especialidad_id_legacy).first()
                    if esp:
                        new_user.especialidades.append(esp)
                else:
                    esp = Especialidad.query.get(especialidad_id_legacy)
                    if esp:
                        new_user.especialidades.append(esp)

            if especialidades_input:
                for esp_input in especialidades_input:
                    especialidad = None
                    
                    if isinstance(esp_input, int) or (isinstance(esp_input, str) and esp_input.isdigit()):
                        especialidad = Especialidad.query.get(int(esp_input))
                    
                    if not especialidad and isinstance(esp_input, str):
                        especialidad = Especialidad.query.filter_by(nombre=esp_input).first()

                    if especialidad:
                         if especialidad not in new_user.especialidades:
                            new_user.especialidades.append(especialidad)
            
            db.session.add(new_user)
            
        elif role == 'paciente':
            if Paciente.query.filter_by(correo_electronico=data.get('email')).first():
                 raise APIException("El correo ya está registrado", 400)
                 
            new_user = Paciente(
                nombre=data.get('nombre'),
                correo_electronico=data.get('email'),
                contrasena_hash=generate_password_hash(data.get('password')),
                apellido=data.get('apellido'),
                telefono=data.get('telefono'),
                dni_nif=data.get('dni_nif'),
                direccion_fiscal=data.get('direccion_fiscal'),
                foto_paciente=data.get('foto_perfil'),
                token_pago=data.get('token_pago'),
                
                edad=data.get('edad'),
                fecha_nacimiento=data.get('fecha_nacimiento')
            )
            
            if new_user.fecha_nacimiento:
                if isinstance(new_user.fecha_nacimiento, str):
                    from datetime import datetime
                    try:
                        new_user.fecha_nacimiento = datetime.strptime(new_user.fecha_nacimiento, '%Y-%m-%d').date()
                    except:
                        new_user.fecha_nacimiento = None
                
                if not new_user.edad and new_user.fecha_nacimiento:
                     from datetime import datetime
                     today = datetime.now().date()
                     new_user.edad = today.year - new_user.fecha_nacimiento.year - (
                        (today.month, today.day) < (new_user.fecha_nacimiento.month, new_user.fecha_nacimiento.day)
                     )

            db.session.add(new_user)
        else:
            raise APIException("Rol inválido", 400)
            
        db.session.commit()
        return {"msg": "User created successfully"}, 201
