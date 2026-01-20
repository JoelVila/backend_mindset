from datetime import datetime
from app import db
from app.models import Informe, Paciente, Factura, Especialidad, Anamnesis

class InformeService:
    @staticmethod
    def get_informes_paciente(paciente_id):
        return Informe.query.filter_by(id_paciente=paciente_id).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informes_psicologo(psicologo_id):
        return Informe.query.filter_by(id_psicologo=psicologo_id).order_by(Informe.fecha_creacion.desc()).all()

    @staticmethod
    def get_informe_detalle(id_informe, user_id, user_role):
        informe = Informe.query.get(id_informe)
        if not informe:
            return None, {"msg": "Informe no encontrado"}, 404
        
        can_access = False
        if user_role == 'paciente' and informe.id_paciente == user_id:
            can_access = True
        elif user_role == 'psicologo' and informe.id_psicologo == user_id:
            can_access = True
        
        if not can_access:
            return None, {"msg": "Acceso denegado a este informe"}, 403
            
        return informe, None, 200

    @staticmethod
    def create_informe(psicologo_id, data):
        # 'contenido' or 'texto_informe' can be accepted from frontend
        texto = data.get('contenido') or data.get('texto_informe')
        
        if 'id_paciente' not in data or not texto:
            return None, {"msg": "Campos 'id_paciente' y 'texto_informe' (o contenido) son requeridos"}, 400
        
        paciente = Paciente.query.get(data['id_paciente'])
        if not paciente:
            return None, {"msg": "Paciente no encontrado"}, 404
        
        new_informe = Informe(
            id_paciente=data['id_paciente'],
            id_psicologo=psicologo_id,
            texto_informe=texto,
            titulo_informe=data.get('titulo_informe', 'Informe General'),
            diagnostico=data.get('diagnostico'),
            tratamiento=data.get('tratamiento'),
            id_cita=data.get('id_cita') # Optional linking
        )
        
        db.session.add(new_informe)
        db.session.commit()
        return new_informe, None, 201

class HistorialService:
    # Now using Anamnesis model (1:1 with Patient)
    @staticmethod
    def get_historial(paciente_id):
        # Return Anamnesis object. Frontend expects 'contenido', maybe we map 'antecedentes'?
        anamnesis = Anamnesis.query.filter_by(id_paciente=paciente_id).first()
        # Create a dummy object or let the controller handle formatting if needed.
        # But controller expects .contenido. Ideally we fix controller too.
        # For now let's return the object and properties will vary.
        # Check main.py usages: .contenido, .fecha_creacion
        # Anamnesis has 'antecedentes', 'motivo_consulta', 'fecha_alta'.
        # We'll map dynamic property if possible or just let it be.
        if anamnesis:
             # Monkey patch for compatibility if needed or just alias
             anamnesis.contenido = f"Antecedentes: {anamnesis.antecedentes}\nMotivo: {anamnesis.motivo_consulta}"
             anamnesis.fecha_creacion = anamnesis.fecha_alta # Approx
        return anamnesis

    @staticmethod
    def update_historial(data):
        paciente_id = data.get('id_paciente')
        antecedentes = data.get('antecedentes') or data.get('contenido') # Fallback if frontend sends 'contenido'
        motivo = data.get('motivo_consulta')
        alergias = data.get('alergias')
        
        anamnesis = Anamnesis.query.filter_by(id_paciente=paciente_id).first()
        if anamnesis:
            if antecedentes: anamnesis.antecedentes = antecedentes
            if motivo: anamnesis.motivo_consulta = motivo
            if alergias: anamnesis.alergias = alergias
        else:
            anamnesis = Anamnesis(
                id_paciente=paciente_id,
                antecedentes=antecedentes,
                motivo_consulta=motivo,
                alergias=alergias
            )
            db.session.add(anamnesis)
        
        db.session.commit()
        return anamnesis

class FacturaService:
    @staticmethod
    def create_factura(data):
        # Auto-calculate total
        total = data.get('total') or data.get('importe_total')
        base = data.get('base_imponible')
        iva = data.get('iva')
        
        if total is None and base is not None and iva is not None:
            try:
                total = float(base) + (float(base) * (float(iva) / 100))
            except:
                total = 0
                
        # Auto-generate invoice number if missing
        num_factura = data.get('numero_factura')
        if not num_factura:
            import time
            num_factura = f"INV-{int(time.time())}"

        new_factura = Factura(
            id_paciente=data.get('id_paciente'),
            id_psicologo=data.get('id_psicologo'),
            numero_factura=num_factura,
            importe_total=total,
            base_imponible=base,
            iva=iva,
            concepto=data.get('concepto')
        )
        db.session.add(new_factura)
        db.session.commit()
        return new_factura

class EspecialidadService:
    @staticmethod
    def get_all():
        return Especialidad.query.all()
