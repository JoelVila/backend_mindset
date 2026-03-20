from app import db
from app.models import Psicologo, Paciente, Administrador, Especialidad
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
import re
from email_validator import validate_email, EmailNotValidError

import json


class AuthService:
    @staticmethod
    def login(data):
        print(f"DEBUG LOGIN - Raw data received: {data}")
        print(f"DEBUG LOGIN - Data type: {type(data)}")
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        email = data.get('email') # Front-end likely still sends 'email' key
        password = data.get('password')
        role = data.get('role') # 'psicologo', 'paciente' or 'admin'

        if not role:
            return {"msg": "Role is required"}, 400

        # Basic Sanitization
        email = email.strip().lower() if email else None

        if not email or not password:
             return {"msg": "Email and password are required"}, 400
             
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return {"msg": "Invalid email format"}, 400
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
            # Admin still uses 'email' field in DB according to new model, but check hash field name
            user = Administrador.query.filter_by(email=email).first()
            # Admin model uses contrasena_hash now too
            if user and check_password_hash(user.contrasena_hash, password):
                identity = json.dumps({'id': user.id_admin, 'role': 'admin'})
                access_token = create_access_token(identity=identity)
                return {"access_token": access_token, "role": "admin"}, 200
        
        return {"msg": "Bad username or password"}, 401

    @staticmethod
    def register(data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        role = data.get('role')
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if not email or not password:
            return {"msg": "Email and password are required"}, 400

        try:
            validate_email(email)
        except EmailNotValidError:
            return {"msg": "Invalid email format"}, 400

        if len(password) < 8:
            return {"msg": "Password must be at least 8 characters long"}, 400
        
        if not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
            return {"msg": "Password must contain at least one uppercase letter and one number"}, 400
            if Psicologo.query.filter_by(correo_electronico=data.get('email')).first():
                 return {"msg": "Email already exists"}, 400
            
            # --- Verificación de Seguridad contra el COPC ---
            # Mapping 'numero_licencia' from input to 'numero_colegiado' in DB
            num_cole = data.get('numero_licencia') or data.get('numero_colegiado')
            if not num_cole:
                 return {"msg": "Registration failed: License number is required for verification."}, 400
            
            from app.adapters.copc_adapter import CopcAdapter
            adapter = CopcAdapter()
            verification = adapter.verify(num_cole)
            
            if not verification.get("verified"):
                return {"msg": f"Registration denied: {verification.get('msg')}"}, 403
            
            nombre_final = verification.get("nombre") or data.get('nombre')
            # Using verified number if available, else input
            num_cole_final = verification.get("numero_colegiado") or num_cole
            
            new_user = Psicologo(
                nombre=nombre_final,
                correo_electronico=data.get('email'),
                contrasena_hash=generate_password_hash(data.get('password')),
                telefono=data.get('telefono'), # Changed from 'telefono' string to matching model if needed, model has telefono
                apellido=data.get('apellido'),
                dni_nif=data.get('dni_nif'),
                direccion_fiscal=data.get('direccion_fiscal'),
                numero_colegiado=num_cole_final,
                cuenta_bancaria=data.get('numero_cuenta'), # Mapping frontend 'numero_cuenta' to DB 'cuenta_bancaria'
                foto_psicologo=data.get('foto_perfil'), # Mapping frontend 'foto_perfil' to DB 'foto_psicologo'
                
                # Campos adicionales recuperados
                bio=data.get('bio'),
                anios_experiencia=data.get('anios_experiencia'),
                precio_online=data.get('precio_online'),
                banco=data.get('banco'),
                titular_cuenta=data.get('titular_cuenta')
            )
            
            # Handle specialties
            especialidades_input = data.get('especialidades', []) # List of IDs
            print(f"DEBUG REGISTER - Especialidades recibidas: {especialidades_input} (Type: {type(especialidades_input)})")
            
            especialidad_id_legacy = data.get('especialidad_id') # Single ID or Name
            
            # Legacy support if frontend sends single ID
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
                    
                    # 1. Intentar buscar por ID (si es int o string numérico)
                    if isinstance(esp_input, int) or (isinstance(esp_input, str) and esp_input.isdigit()):
                        especialidad = Especialidad.query.get(int(esp_input))
                    
                    # 2. Si no se encontró, intentar buscar por Nombre exacto
                    if not especialidad and isinstance(esp_input, str):
                        especialidad = Especialidad.query.filter_by(nombre=esp_input).first()

                    if especialidad:
                         # Check if not already added
                         if especialidad not in new_user.especialidades:
                            new_user.especialidades.append(especialidad)
            
            db.session.add(new_user)
            
        elif role == 'paciente':
            if Paciente.query.filter_by(correo_electronico=data.get('email')).first():
                 return {"msg": "Email already exists"}, 400
                 
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
                
                # Campos adicionales recuperados
                edad=data.get('edad'),
                fecha_nacimiento=data.get('fecha_nacimiento')
            )
            
            # Handle date string conversion and auto-calculate age
            if new_user.fecha_nacimiento:
                if isinstance(new_user.fecha_nacimiento, str):
                    from datetime import datetime
                    try:
                        new_user.fecha_nacimiento = datetime.strptime(new_user.fecha_nacimiento, '%Y-%m-%d').date()
                    except:
                        new_user.fecha_nacimiento = None
                
                # Auto-calculate age if not provided
                if not new_user.edad and new_user.fecha_nacimiento:
                     from datetime import datetime
                     today = datetime.now().date()
                     new_user.edad = today.year - new_user.fecha_nacimiento.year - (
                        (today.month, today.day) < (new_user.fecha_nacimiento.month, new_user.fecha_nacimiento.day)
                     )

            db.session.add(new_user)
        else:
            return {"msg": "Invalid role"}, 400
            
        db.session.commit()
        return {"msg": "User created successfully"}, 201
