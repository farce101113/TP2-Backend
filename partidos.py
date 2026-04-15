from flask import Flask, request, jsonify, Blueprint
from db import get_db_connection
from datetime import datetime

partidos_bp = Blueprint('partidos', __name__)

@partidos_bp.route('/', methods=['GET'])
def get_partidos():

    try:
        equipo = request.args.get('equipo')
        fecha = request.args.get('fecha')
        fase = request.args.get('fase')
        limit = request.args.get('_limit', default = 10, type=int)
        offset = request.args.get('_offset', default=0, type=int)

        if limit < 0 or offset < 0:
            return jsonify({
                        'code' : 'BAD REQUEST',
                        'message' : 'Los parametros _limit y _offset deben ser numeros enteros no negativos',
                        'level' : 'error',
                        'description' : 'El valor de _limit y _offset debe ser un numero entero mayor o igual a 0'
                    }), 400
        
        if fecha:
            try:
                datetime.strptime(fecha, '%Y-%m-%d')

            except ValueError:
                return jsonify({
                    'code' : 'BAD REQUEST',
                    'message' : 'El formato de fecha es invalido',
                    'level' : 'error',
                    'description' : 'El formato de fecha debe ser YYYY-MM-DD'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = 'SELECT * FROM partidos WHERE 1=1'
        params = []

        if equipo : 
            query += ' AND (equipo_loc = %s OR equipo_vis = %s)'
            params.extend([equipo,equipo])

        if fecha:
            query += ' AND fecha LIKE %s'
            params.append(f'{fecha}%')

        if fase:
            query += ' AND id_fase = %s'
            params.append(fase)

        # Contar con los mismos filtros
        count_query = query.replace('SELECT *', 'SELECT COUNT(*) AS total')
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()['total']

        query += ' LIMIT %s OFFSET %s'
        params.extend([limit,offset])

        cursor.execute(query, tuple(params))
        partidos = cursor.fetchall()

        for partido in partidos:
            if partido.get('goles_loc') is None:
                partido.pop('goles_loc', None)
            if partido.get('goles_vis') is None:
                partido.pop('goles_vis', None)
        
        base_url = request.base_url
        extra_params = ''
        if equipo:
            extra_params += f"&equipo={equipo}"
        if fecha:
            extra_params += f"&fecha={fecha}"
        if fase:
            extra_params += f"&fase={fase}"

        def build_url(new_offset):
            return f"{base_url}?_limit={limit}&_offset={new_offset}{extra_params}"

        first = build_url(0)
        prev = build_url(max(offset - limit, 0)) if offset > 0 else None
        next = build_url(offset + limit) if offset + limit < total else None
        last_offset = (total - 1) // limit
        last = build_url(last_offset)

        cursor.close()
        conn.close()

        if len(partidos) == 0:
            return 'No hay partidos que cumplan con los criterios de búsqueda', 204

        return jsonify(
            {
            'partidos': partidos,
            'links': {
                'first': first,
                'prev': prev,
                'next': next,
                'last': last
            }
            
        }), 200
    
    except Exception as e:
        return jsonify({
            'code' : 'INTERNAL SERVER_ERROR',
            'message' : 'Ocurrio un error al procesar la solicitud de partidosl',
            'level' : 'error',
            'description' : str(e)
        }), 500

@partidos_bp.route('/<int:id>', methods=['GET'])
def get_partidos_id(id):
    try:
        if id <= 0:
            return jsonify({
                        'code' : 'BAD REQUEST',
                        'message' : 'El parametro id debe ser un numero entero no negativo',
                        'level' : 'error',
                        'description' : 'El valor de id debe ser un numero entero mayor a 0'
                    }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM partidos WHERE id_partido = %s',(id,))
        partidos = cursor.fetchone()

        if partidos is None:
            return jsonify({
                'code' : 'NOT FOUND',
                'message' : f'No se encontro el partido con id {id}',
                'level' : 'error',
                'description' : f'No existe un partido con el id {id} en la base de datos'
            }), 404

        cursor.close()
        conn.close()
        
        return jsonify(partidos), 200
    
    except Exception as e:
        return jsonify({
    
            'code' : 'INTERNAL SERVER_ERROR',
            'message' : 'Ocurrio un error al procesar la solicitud de partidosl',
            'level' : 'error',
            'description' : str(e)
                
        }), 500

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

# POST /partidos/id/prediccion
@partidos_bp.route('/partidos/<int:id_partido>/prediccion', methods=['POST'])
def prediccion(id_partido):
    data = request.get_json()

    if not data:
        return jsonify({"Error": "Body Vacio"}), 400

    id_usuario = data.get('id_usuario')
    goles_loc = data.get('goles_loc')
    goles_vis = data.get('goles_vis')

    if id_usuario is None or goles_loc is None or goles_vis is None:
        return jsonify({"Error": "Faltan datos obligatorios"}), 400

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
