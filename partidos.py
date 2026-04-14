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

@partidos_bp.route('/<int:id>/resultado', methods=['PUT', 'OPTIONS'])
def put_resultado(id):
    data = request.get_json()

    # Validación de campos obligatorios (según Swagger)
    if not data or 'local' not in data or 'visitante' not in data:
        return jsonify({
            "errors": [{
                "code": "CAMPO_REQUERIDO",
                "message": "Los campos 'local' y 'visitante' son obligatorios",
                "level": "error",
                "description": "Faltan uno o ambos campos en el body"
            }]
        }), 400

    if not isinstance(data['local'], int) or not isinstance(data['visitante'], int) or data['local'] < 0 or data['visitante'] < 0:
        return jsonify({
            "errors": [{
                "code": "VALOR_INVALIDO",
                "message": "Los goles deben ser números enteros >= 0",
                "level": "error",
                "description": "local y/o visitante contienen valores inválidos"
            }]
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que el partido existe
    cursor.execute('SELECT id_partido FROM partidos WHERE id_partido = %s', (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({
            "errors": [{
                "code": "NOT_FOUND",
                "message": "Partido no encontrado",
                "level": "error",
                "description": f"No existe un partido con id {id}"
            }]
        }), 404

    # Actualizar resultado (cargar o actualizar)
    cursor.execute('''
        UPDATE partidos
        SET goles_loc = %s, goles_vis = %s
        WHERE id_partido = %s
    ''', (data['local'], data['visitante'], id))

    conn.commit()
    cursor.close()
    conn.close()

    return '', 204

# POST partidos/id/prediccion

@partidos_bp.route('/partidos/<int:id_partido>/prediccion', methods=['POST'])
def prediccion(id_partido):
    data = request.get_json()

    if not data:
        return jsonify({'Error': 'Body Vacio'}), 400

    id_usuario = data.get('id_usuario')
    goles_loc = data.get('goles_loc')
    goles_vis = data.get('goles_vis')

    if id_usuario is None or goles_loc is None or goles_vis is None:
        return jsonify({'Error': 'Faltan datos obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT goles_loc, goles_vis FROM partidos WHERE id_partido = %s""", (id_partido,))

    partido = cursor.fetchone()

    if not partido:
        return jsonify({"Error": "Partido no encontrado"}), 404

    if partido[0] is not None and partido[1] is not None:
        return jsonify({"Error": "El partido ya fue jugado"}), 400

    cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()

    if not usuario:
        return jsonify({
            "Error": "Usuario no encontrado"
        }), 404

    cursor.execute("""
                   SELECT id_prediccion FROM predicciones 
                   WHERE id_usuario = %s AND id_partido = %s
    """, (id_usuario, id_partido))

    prediccion = cursor.fetchone()

    if prediccion:
        return jsonify({
            "Error": "El usuario ya hizo una prediccion para este partido"
        }), 400

    cursor.execute("""
                   INSERT INTO predicciones (id_usuario, id_partido, goles_loc, goles_vis) 
                   VALUES (%s, %s, %s, %s)
    """, (id_usuario, id_partido, goles_loc, goles_vis))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "MENSAJE": "Prediccion registrada correctamente",
        "id_usuario": id_usuario,
        "id_partido": id_partido,
        "goles_loc": goles_loc,
        "goles_vis": goles_vis
    }), 201


# GET /ranking

@partidos_bp.route('/ranking', methods=['GET'])
def ranking():
    data = request.get_json()
    if not data:
        return jsonify({"Error": "Body Vacio"}), 400

    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total = cursor.fetchone()[0]

    query = """
                SELECT id_usuario, nombre, puntos
                FROM usuarios 
                ORDER BY puntos DESC
                LIMIT %s OFFSET %s
        """

    cursor.execute(query, (limit, offset))
    resultados = cursor.fetchall()

    ranking = []
    for i, fila in enumerate(resultados):
        posicion = offset + i + 1

        ranking.append({
            "posicion": posicion,
            "id_usuario": fila[0],
            "nombre": fila[1],
            "puntos": fila[2]
        })

    cursor.close()
    conn.close()

    return jsonify({
        "data": ranking,
        "total": total,
        "limit": limit,
        "offset": offset
    })