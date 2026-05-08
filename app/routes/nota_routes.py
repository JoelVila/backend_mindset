from flask import Blueprint, request, jsonify
from app.services.nota_service import NotaService

notas_bp = Blueprint('notas', __name__)

@notas_bp.route('/notas', methods=['POST'])
def crear_nota():
    """
    Crear nota de sesión
    ---
    tags:
      - Notas
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            id_cita:
              type: integer
            contenido:
              type: string
            tipo_nota:
              type: string
    responses:
      201:
        description: Nota creada
    """
    data = request.json
    nota, msg, code = NotaService.crear_nota(data)
    if nota:
        return jsonify(msg), code
    return jsonify(msg), code

@notas_bp.route('/notas/<int:id_nota>', methods=['PUT'])
def editar_nota(id_nota):
    """
    Editar nota de sesión
    ---
    tags:
      - Notas
    parameters:
      - name: id_nota
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            contenido:
              type: string
            tipo_nota:
              type: string
    responses:
      200:
        description: Nota actualizada
    """
    data = request.json
    nota, msg, code = NotaService.update_nota(id_nota, data)
    return jsonify(msg), code

@notas_bp.route('/notas/cita/<int:id_cita>', methods=['GET'])
def get_notas_cita(id_cita):
    """
    Obtener notas de una cita
    ---
    tags:
      - Notas
    parameters:
      - name: id_cita
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de notas
    """
    notas = NotaService.get_notas_cita(id_cita)
    res = []
    for n in notas:
        res.append({
            "id": n.id_nota,
            "contenido": n.contenido,
            "tipo": n.tipo_nota,
            "fecha": str(n.fecha)
        })
    return jsonify(res), 200
