from flask import Blueprint, request, jsonify
from app.services.informe_service import InformeService

informes_bp = Blueprint('informes', __name__)

@informes_bp.route('/informes', methods=['POST'])
def crear_informe():
    """
    Crear nuevo informe (Psicólogos)
    ---
    tags:
      - Informes
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            id_paciente:
              type: integer
            id_psicologo:
              type: integer
            titulo:
              type: string
            texto:
              type: string
            diagnostico:
              type: string
            tratamiento:
              type: string
    responses:
      201:
        description: Informe creado
      400:
        description: Datos inválidos
    """
    data = request.json
    informe, msg, code = InformeService.crear_informe(data)
    if informe:
        return jsonify(msg), code
    return jsonify(msg), code

@informes_bp.route('/informes/<int:id_informe>', methods=['PUT'])
def editar_informe(id_informe):
    """
    Editar informe existente
    ---
    tags:
      - Informes
    parameters:
      - name: id_informe
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            titulo:
              type: string
            texto:
              type: string
            diagnostico:
              type: string
            tratamiento:
              type: string
    responses:
      200:
        description: Informe actualizado
      404:
        description: No encontrado
    """
    data = request.json
    informe, msg, code = InformeService.update_informe(id_informe, data)
    return jsonify(msg), code

@informes_bp.route('/informes/<int:id_informe>', methods=['GET'])
def get_informe(id_informe):
    """
    Obtener detalles de un informe
    ---
    tags:
      - Informes
    parameters:
      - name: id_informe
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalles del informe
      404:
        description: No encontrado
    """
    informe = InformeService.get_informe_id(id_informe)
    if not informe:
        return jsonify({"msg": "Informe no encontrado"}), 404
    
    return jsonify({
        "id": informe.id_informe,
        "titulo": informe.titulo_informe,
        "diagnostico": informe.diagnostico,
        "tratamiento": informe.tratamiento,
        "texto": informe.texto_informe,
        "fecha": str(informe.fecha_creacion),
        "id_paciente": informe.id_paciente
    }), 200

@informes_bp.route('/informes/paciente/<int:id_paciente>', methods=['GET'])
def get_informes_paciente(id_paciente):
    informes = InformeService.get_informes_paciente(id_paciente)
    res = []
    for inf in informes:
        res.append({
            "id": inf.id_informe,
            "titulo": inf.titulo_informe,
            "fecha": str(inf.fecha_creacion),
            "diagnostico": inf.diagnostico
        })
    return jsonify(res), 200

from app.utils.pdf_generator import generate_pdf_report
from flask import send_file
from app.models import Informe, Paciente, Psicologo

@informes_bp.route('/informes/<int:id_informe>/pdf', methods=['GET'])
def descargar_informe_pdf(id_informe):
    informe = InformeService.get_informe_id(id_informe)
    if not informe:
        return jsonify({"msg": "Informe no encontrado"}), 404
    
    paciente = Paciente.query.get(informe.id_paciente)
    psicologo = Psicologo.query.get(informe.id_psicologo)
    
    # Generar PDF con FPDF2
    try:
        pdf_buffer = generate_pdf_report(paciente, psicologo, informe)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"Informe_{paciente.nombre}_{informe.fecha_creacion.date()}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return jsonify({"msg": "Error generando archivo PDF"}), 500
