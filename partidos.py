from flask import Flask, request, jsonify, Blueprint
from db import get_db_connection

partidos_bp = Blueprint('partidos', __name__)

@partidos_bp.route('/', methods=['GET'])
def get_partidos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM partidos')
    partidos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(partidos)

@partidos_bp.route('/<int:id>', methods=['PUT'])
def put_partido(id):
    data = request.get_json()

    campos_requeridos = ['equipo_local', 'equipo_visitante', 'fecha', 'fase']
    for campo in campos_requeridos:
        if campo not in data or data[campo] is None:
            return jsonify({"errors": [{"code": "CAMPO_REQUERIDO", "message": f"El campo '{campo}' es obligatorio", "level": "error", "description": f"Falta el campo '{campo}' en el body"}]}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que el partido existe
    cursor.execute('SELECT * FROM partidos WHERE id_partido = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"errors": [{"code": "NOT_FOUND", "message": "Partido no encontrado", "level": "error", "description": f"No existe un partido con id {id}"}]}), 404

    # Buscar id_fase por nombre
    cursor.execute('SELECT id_fase FROM fases WHERE nombre = %s', (data['fase'],))
    fase = cursor.fetchone()
    if not fase:
        cursor.close()
        conn.close()
        return jsonify({"errors": [{"code": "FASE_INVALIDA", "message": "La fase no es válida", "level": "error", "description": "La fase enviada no existe en la base de datos"}]}), 400

    cursor.execute('''
        UPDATE partidos
        SET equipo_loc = %s, equipo_vis = %s, fecha = %s, id_fase = %s
        WHERE id_partido = %s
    ''', (data['equipo_local'], data['equipo_visitante'], data['fecha'], fase['id_fase'], id))

    conn.commit()
    cursor.close()
    conn.close()
    return '', 204


@partidos_bp.route('/<int:id>', methods=['PATCH'])
def patch_partido(id):
    data = request.get_json()

    campos_permitidos = ['equipo_local', 'equipo_visitante', 'fecha', 'fase']
    campos_presentes = {k: v for k, v in data.items() if k in campos_permitidos}

    if not campos_presentes:
        return jsonify({"errors": [{"code": "SIN_CAMPOS", "message": "Debe enviar al menos un campo para actualizar", "level": "error", "description": "El body no contiene campos válidos"}]}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que el partido existe
    cursor.execute('SELECT * FROM partidos WHERE id_partido = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"errors": [{"code": "NOT_FOUND", "message": "Partido no encontrado", "level": "error", "description": f"No existe un partido con id {id}"}]}), 404

    # Si viene fase, resolver el id
    if 'fase' in campos_presentes:
        cursor.execute('SELECT id_fase FROM fases WHERE nombre = %s', (campos_presentes['fase'],))
        fase = cursor.fetchone()
        if not fase:
            cursor.close()
            conn.close()
            return jsonify({"errors": [{"code": "FASE_INVALIDA", "message": "La fase no es válida", "level": "error", "description": "La fase enviada no existe en la base de datos"}]}), 400
        campos_presentes['fase'] = fase['id_fase']

    mapeo = {
        'equipo_local': 'equipo_loc',
        'equipo_visitante': 'equipo_vis',
        'fecha': 'fecha',
        'fase': 'id_fase'
    }

    sets = ', '.join([f"{mapeo[k]} = %s" for k in campos_presentes])
    valores = list(campos_presentes.values()) + [id]

    cursor.execute(f'UPDATE partidos SET {sets} WHERE id_partido = %s', valores)
    conn.commit()
    cursor.close()
    conn.close()
    return '', 204