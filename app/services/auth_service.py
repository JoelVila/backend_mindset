from app import db
from app.models import Psicologo, Paciente, Administrador, Especialidad
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token


class AuthService:
    @staticmethod
    def login(data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        email = data.get('email')
        password = data.get('password')
        role = data.get('role') # 'psicologo', 'paciente' or 'admin'

        if not role:
            return {"msg": "Role is required"}, 400

        user = None
        if role == 'psicologo':
            user = Psicologo.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                access_token = create_access_token(identity={'id': user.id_psicologo, 'role': 'psicologo'})
                return {"access_token": access_token, "role": "psicologo"}, 200
                
        elif role == 'paciente':
            user = Paciente.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                access_token = create_access_token(identity={'id': user.id_paciente, 'role': 'paciente'})
                return {"access_token": access_token, "role": "paciente"}, 200

        elif role == 'admin':
            user = Administrador.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                access_token = create_access_token(identity={'id': user.id_admin, 'role': 'admin'})
                return {"access_token": access_token, "role": "admin"}, 200
        
        return {"msg": "Bad username or password"}, 401

    @staticmethod
    def register(data):
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
            
        role = data.get('role')
        
        # Check for required photo
        if not data.get('foto_perfil'):
            return {"msg": "Foto de perfil is required"}, 400
        
        if role == 'psicologo':
            if Psicologo.query.filter_by(email=data.get('email')).first():
                 return {"msg": "Email already exists"}, 400
            
            # --- Verificación de Seguridad contra el COPC ---
            num_licencia = data.get('numero_licencia')
            if not num_licencia:
                 return {"msg": "Registration failed: License number is required for verification."}, 400
            
            from app.adapters.copc_adapter import CopcAdapter
            adapter = CopcAdapter()
            verification = adapter.verify(num_licencia)
            
            if not verification.get("verified"):
                return {"msg": f"Registration denied: {verification.get('msg')}"}, 403
            
            nombre_final = verification.get("nombre") or data.get('nombre')
            licencia_final = verification.get("numero_colegiado") or num_licencia
            institucion_final = verification.get("institucion") or data.get('institucion')

            new_user = Psicologo(
                nombre=nombre_final,
                email=data.get('email'),
                password_hash=generate_password_hash(data.get('password')),
                telefono=data.get('telefono'),
                foto_perfil=data.get('foto_perfil'),
                bio=data.get('bio'),
                precio_presencial=data.get('precio_presencial'),
                precio_online=data.get('precio_online'),
                precio_chat=data.get('precio_chat'),
                numero_cuenta=data.get('numero_cuenta'),
                banco=data.get('banco'),
                titular_cuenta=data.get('titular_cuenta'),
                numero_licencia=licencia_final,
                institucion=institucion_final,
                verificado=verification.get("verified", False)
            )
            
            # Handle specialties
            especialidades_input = data.get('especialidades', []) # List of IDs
            especialidad_id_legacy = data.get('especialidad_id') # Single ID or Name
            
            if isinstance(especialidad_id_legacy, str):
                esp = Especialidad.query.filter_by(nombre=especialidad_id_legacy).first()
                if esp:
                    especialidad_id_legacy = esp.id
            
            if especialidad_id_legacy:
                new_user.especialidad_id = especialidad_id_legacy
                
            if especialidades_input:
                for esp_id in especialidades_input:
                    especialidad = Especialidad.query.get(esp_id)
                    if especialidad:
                        new_user.especialidades.append(especialidad)
                        if not new_user.especialidad_id:
                            new_user.especialidad_id = esp_id
            
            db.session.add(new_user)
            
        elif role == 'paciente':
            if Paciente.query.filter_by(email=data.get('email')).first():
                 return {"msg": "Email already exists"}, 400
                 
            new_user = Paciente(
                nombre=data.get('nombre'),
                email=data.get('email'),
                password_hash=generate_password_hash(data.get('password')),
                apellido=data.get('apellido'),
                edad=data.get('edad'),
                telefono=data.get('telefono'),
                foto_perfil=data.get('foto_perfil'),
                tipo_paciente=data.get('tipo_paciente'),
                tipo_tarjeta=data.get('tipo_tarjeta')
            )
            db.session.add(new_user)
        else:
            return {"msg": "Invalid role"}, 400
            
        db.session.commit()
        return {"msg": "User created successfully"}, 201
