from app import db
from app.models import Psicologo, Especialidad

class PsicologoService:
    @staticmethod
    def get_all_basic():
        from sqlalchemy.orm import joinedload
        return Psicologo.query.options(joinedload(Psicologo.especialidades)).all()

    @staticmethod
    def search_psicologos(params):
        from sqlalchemy.orm import joinedload
        query = Psicologo.query.options(joinedload(Psicologo.especialidades))
        
        # 1. Search (Query Libre) - Nombre, Bio, O Especialidades
        search_query = params.get('q', '').strip()
        if search_query:
            query = query.filter(
                db.or_(
                    Psicologo.nombre.ilike(f'%{search_query}%'),
                    Psicologo.bio.ilike(f'%{search_query}%'),
                    Psicologo.especialidades.any(Especialidad.nombre.ilike(f'%{search_query}%'))
                )
            )
        
        # 2. Filtro Especialidad (Específico)
        especialidad_param = params.get('especialidad', '').strip()
        if especialidad_param:
            query = query.filter(
                Psicologo.especialidades.any(Especialidad.nombre.ilike(f'%{especialidad_param}%'))
            )
        
        # 3. Ubicación (filtro por dirección fiscal)
        ubicacion = params.get('ubicacion', '').strip()
        if ubicacion:
            query = query.filter(
                Psicologo.direccion_fiscal.ilike(f'%{ubicacion}%')
            )

        # 4. Rango de Precios
        precio_min = params.get('precio_min')
        precio_max = params.get('precio_max')
        
        if precio_min:
            try:
                p_min = float(precio_min)
                query = query.filter(Psicologo.precio_online >= p_min)
            except ValueError:
                pass
                
        if precio_max:
            try:
                p_max = float(precio_max)
                query = query.filter(Psicologo.precio_online <= p_max)
            except ValueError:
                pass

        # 5. Filtrar por Valoración Mínima (Rating)
        from app.models import Resena
        from sqlalchemy import func
        
        rating_min = params.get('rating_min')
        if rating_min:
            try:
                r_min = float(rating_min)
                # Subconsulta para obtener promedios por psicólogo
                subquery = db.session.query(
                    Resena.id_psicologo, 
                    func.avg(Resena.puntuacion).label('avg_rating')
                ).group_by(Resena.id_psicologo).subquery()
                
                query = query.join(subquery, Psicologo.id_psicologo == subquery.c.id_psicologo)\
                             .filter(subquery.c.avg_rating >= r_min)
            except ValueError:
                pass
        
        return query.distinct().all()

    @staticmethod
    def get_profile(id_psicologo):
        return Psicologo.query.get(id_psicologo)

    @staticmethod
    def update_profile(id_psicologo, data):
        psicologo = Psicologo.query.get(id_psicologo)
        if not psicologo:
            return None, {"msg": "Psicólogo no encontrado"}, 404
        
        # Determine updates
        if 'nombre' in data: psicologo.nombre = data['nombre']
        if 'apellido' in data: psicologo.apellido = data['apellido']
        if 'precio_online' in data: psicologo.precio_online = data['precio_online']
        
        if 'numero_cuenta' in data: psicologo.cuenta_bancaria = data.get('numero_cuenta')
        if 'banco' in data: psicologo.banco = data.get('banco')
        if 'titular_cuenta' in data: psicologo.titular_cuenta = data.get('titular_cuenta')
        
        if 'bio' in data: psicologo.bio = data['bio']
        if 'foto_perfil' in data: psicologo.foto_psicologo = data['foto_perfil']
        if 'anios_experiencia' in data: psicologo.anios_experiencia = data['anios_experiencia']
        if 'telefono' in data: psicologo.telefono = data['telefono']
        if 'direccion_fiscal' in data: psicologo.direccion_fiscal = data['direccion_fiscal']
        if 'video_presentacion_url' in data: psicologo.video_presentacion_url = data['video_presentacion_url']
        
        # Ofertas de Introducción
        if 'ofrece_sesion_intro' in data: psicologo.ofrece_sesion_intro = data['ofrece_sesion_intro']
        if 'precio_sesion_intro' in data: psicologo.precio_sesion_intro = data['precio_sesion_intro']
        
        if 'especialidades' in data:
            psicologo.especialidades.clear()
            especialidad_ids = data['especialidades']
            for esp_id in especialidad_ids:
                especialidad = Especialidad.query.get(esp_id)
                if especialidad:
                     # Check if not already added to avoid duplicates if behavior changes
                     if especialidad not in psicologo.especialidades:
                        psicologo.especialidades.append(especialidad)
        
        db.session.commit()
        return psicologo, None, 200
