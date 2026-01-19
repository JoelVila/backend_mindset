from app import db
from app.models import Psicologo, Especialidad

class PsicologoService:
    @staticmethod
    def get_all_basic():
        return Psicologo.query.all()

    @staticmethod
    def search_psicologos(params):
        query = Psicologo.query
        
        # Search by name or bio
        search_query = params.get('q', '').strip()
        if search_query:
            query = query.filter(
                db.or_(
                    Psicologo.nombre.ilike(f'%{search_query}%'),
                    Psicologo.bio.ilike(f'%{search_query}%')
                )
            )
        
        # Filter by specialty
        especialidad_param = params.get('especialidad', '').strip()
        if especialidad_param:
            query = query.join(Psicologo.especialidades).filter(
                Especialidad.nombre.ilike(f'%{especialidad_param}%')
            )
        
        # Filter by maximum price
        precio_max = params.get('precio_max')
        if precio_max:
            try:
                precio_max = float(precio_max)
                query = query.filter(
                    db.or_(
                        Psicologo.precio_presencial <= precio_max,
                        Psicologo.precio_online <= precio_max
                    )
                )
            except ValueError:
                pass
        
        return query.all()

    @staticmethod
    def get_profile(id_psicologo):
        return Psicologo.query.get(id_psicologo)

    @staticmethod
    def update_profile(id_psicologo, data):
        psicologo = Psicologo.query.get(id_psicologo)
        if not psicologo:
            return None, {"msg": "Psicólogo no encontrado"}, 404
        
        # Determine updates
        if 'precio_presencial' in data: psicologo.precio_presencial = data['precio_presencial']
        if 'precio_online' in data: psicologo.precio_online = data['precio_online']
        if 'precio_chat' in data: psicologo.precio_chat = data['precio_chat']
        
        if 'numero_cuenta' in data: psicologo.numero_cuenta = data.get('numero_cuenta')
        if 'banco' in data: psicologo.banco = data.get('banco')
        if 'titular_cuenta' in data: psicologo.titular_cuenta = data.get('titular_cuenta')
        
        if 'bio' in data: psicologo.bio = data['bio']
        if 'foto_perfil' in data: psicologo.foto_perfil = data['foto_perfil']
        if 'anios_experiencia' in data: psicologo.anios_experiencia = data['anios_experiencia']
        if 'telefono' in data: psicologo.telefono = data['telefono']
        
        if 'especialidades' in data:
            psicologo.especialidades.clear()
            especialidad_ids = data['especialidades']
            for esp_id in especialidad_ids:
                especialidad = Especialidad.query.get(esp_id)
                if especialidad:
                    psicologo.especialidades.append(especialidad)
        
        db.session.commit()
        return psicologo, None, 200
