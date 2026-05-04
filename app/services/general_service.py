from datetime import datetime
from app import db
from app.models import Informe, Paciente, Factura, Especialidad, Anamnesis
from app.errors import APIException

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
            raise APIException("Informe no encontrado", 404)
        
        can_access = False
        if user_role == 'paciente' and informe.id_paciente == user_id:
            can_access = True
        elif user_role == 'psicologo' and informe.id_psicologo == user_id:
            can_access = True
        
        if not can_access:
            raise APIException("Acceso denegado a este informe", 403)
            
        return informe

    @staticmethod
    def create_informe(psicologo_id, data):
        texto = data.get('contenido') or data.get('texto_informe')
        
        if 'id_paciente' not in data or not texto:
            raise APIException("Campos 'id_paciente' y 'texto_informe' son requeridos", 400)
        
        paciente = Paciente.query.get(data['id_paciente'])
        if not paciente:
            raise APIException("Paciente no encontrado", 404)
        
        new_informe = Informe(
            id_paciente=data['id_paciente'],
            id_psicologo=psicologo_id,
            texto_informe=texto,
            titulo_informe=data.get('titulo_informe', 'Informe General'),
            diagnostico=data.get('diagnostico'),
            tratamiento=data.get('tratamiento'),
            id_cita=data.get('id_cita')
        )
        
        db.session.add(new_informe)
        db.session.commit()
        return new_informe

class HistorialService:
    @staticmethod
    def get_historial(paciente_id):
        anamnesis = Anamnesis.query.filter_by(id_paciente=paciente_id).first()
        if anamnesis:
             anamnesis.contenido = f"Antecedentes: {anamnesis.antecedentes}\nMotivo: {anamnesis.motivo_consulta}"
             anamnesis.fecha_creacion = anamnesis.fecha_alta
        return anamnesis

    @staticmethod
    def update_historial(data):
        paciente_id = data.get('id_paciente')
        antecedentes = data.get('antecedentes') or data.get('contenido')
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
        total = data.get('total') or data.get('importe_total')
        base = data.get('base_imponible')
        iva = data.get('iva')
        
        if total is None and base is not None and iva is not None:
            try:
                total = float(base) + (float(base) * (float(iva) / 100))
            except:
                total = 0
                
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
