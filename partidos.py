from flask import Flask, request, jsonify, Blueprint
from db import get_db_connection
from datetime import datetime

partidos_bp = Blueprint('partidos', __name__)

# Funcion para generar respuestas de error consistentes
def error_response(status_code, code, message, description, details=None):
    error = {
        "code": code,
        "message": message,
        "level": "error",
        "description": description
    }

    if details:
        error["details"] = details

    return jsonify({"errors": [error]}), status_code

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

# DELETE partidos
@partidos_bp.route('/partidos/<int:id>', methods=['DELETE'])
def eliminar_partido(id):
    try:
        PartidoService.eliminar(id)
        return '', 204
    except PartidoNoEncontradoError:
        return jsonify({'error': 'Partido no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def eliminar(id):
        partido = PartidoRepository.obtener_por_id(id)
        if not partido:
            raise PartidoNoEncontradoError()
        PartidoRepository.eliminar(partido)

 def obtener_por_id(id):
        return Partido.query.get(id)

def eliminar(partido):
        db.session.delete(partido)
        db.session.commit()

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
@partidos_bp.route('/<int:id_partido>/prediccion', methods=['POST'])
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


@partidos_bp.route('/', methods=['POST'])
def create_partido():
    try:
        data = request.get_json()

        # Validar campos obligatorios
        campos = ['equipo_local', 'equipo_visitante', 'fecha', 'fase']
        faltantes = [c for c in campos if c not in data]

        if faltantes:
            return error_response(
                400,
                "BAD_REQUEST",
                "Faltan campos obligatorios",
                "Se requieren ciertos campos para crear el partido",
                {
                    "invalid_fields": [
                        {
                            "field": c,
                            "reason": "Campo requerido"
                        } for c in faltantes
                    ]
                }
            )

        equipo_local = data['equipo_local']
        equipo_visitante = data['equipo_visitante']

        # Validar equipos distintos
        if equipo_local.lower() == equipo_visitante.lower():
            return error_response(
                400,
                "BAD_REQUEST",
                "Equipos inválidos",
                "Un equipo no puede jugar contra sí mismo",
                {
                    "invalid_fields": [
                        {
                            "field": "equipo",
                            "value": equipo_local,
                            "reason": "Equipos iguales"
                        }
                    ]
                }
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # Buscar equipos
        cursor.execute('''
            SELECT pais_clasificado, grupo
            FROM clasificados
            WHERE LOWER(pais_clasificado) = LOWER(%s)
        ''', (equipo_local,))
        local = cursor.fetchone()

        cursor.execute('''
            SELECT pais_clasificado, grupo
            FROM clasificados
            WHERE LOWER(pais_clasificado) = LOWER(%s)
        ''', (equipo_visitante,))
        visitante = cursor.fetchone()

        errores = []

        # Validación equipo local
        if not local:
            error_local = {
                "field": "equipo_local",
                "value": equipo_local,
                "reason": "No está clasificado",
                "suggestions": {}
            }

            if visitante:
                cursor.execute('''
                    SELECT pais_clasificado
                    FROM clasificados
                    WHERE grupo = %s
                ''', (visitante[1],))
                sugerencias = [row[0] for row in cursor.fetchall()]
                error_local["suggestions"]["same_group"] = sugerencias

            errores.append(error_local)

        # Validación equipo visitante
        if not visitante:
            error_visitante = {
                "field": "equipo_visitante",
                "value": equipo_visitante,
                "reason": "No está clasificado",
                "suggestions": {}
            }

            if local:
                cursor.execute('''
                    SELECT pais_clasificado
                    FROM clasificados
                    WHERE grupo = %s
                ''', (local[1],))
                sugerencias = [row[0] for row in cursor.fetchall()]
                error_visitante["suggestions"]["same_group"] = sugerencias

            errores.append(error_visitante)

        if errores:
            cursor.close()
            conn.close()
            return error_response(
                400,
                "BAD_REQUEST",
                "Equipos inválidos",
                "Uno o más equipos no son válidos",
                {"invalid_fields": errores}
            )

        # Validar fase
        fase_input = data.get('fase')

        # Validar tipo
        if not isinstance(fase_input, str):
            cursor.close()
            conn.close()
            return error_response(
                400,
                "BAD_REQUEST",
                "Fase inválida",
                "El campo fase debe ser un string",
                {
                    "invalid_fields": [
                        {
                            "field": "fase",
                            "value": fase_input,
                            "reason": "Tipo inválido"
                        }
                    ]
                }
            )

        fase_input = fase_input.strip()

        # Buscar fase (case insensitive)
        cursor.execute(
            'SELECT id_fase, nombre FROM fases WHERE LOWER(nombre) = LOWER(%s)',
            (fase_input,)
        )
        fase = cursor.fetchone()

        if not fase:
            # Traer todas las fases válidas
            cursor.execute('SELECT nombre FROM fases')
            fases_validas = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return error_response(
                400,
                "BAD_REQUEST",
                "Fase inexistente",
                "La fase especificada no coincide con ninguna válida",
                {
                    "invalid_fields": [
                        {
                            "field": "fase",
                            "value": fase_input,
                            "reason": "No válida",
                            "valid_values": fases_validas
                        }
                    ]
                }
            )

        id_fase = fase[0]
        nombre_fase = fase[1]
        es_grupos = nombre_fase.lower() == "grupos"

        # Validar mismo grupo
        if es_grupos and local[1] != visitante[1]:
            cursor.close()
            conn.close()
            return error_response(
                400,
                "BAD_REQUEST",
                "Grupos incompatibles",
                "Los equipos deben pertenecer al mismo grupo en fase de grupos",
                {
                    "invalid_fields": [
                        {
                            "field": "grupo",
                            "reason": "Equipos en distintos grupos",
                            "details": {
                                "grupo_local": local[1],
                                "grupo_visitante": visitante[1]
                            }
                        }
                    ]
                }
            )
        
        # Validar que el equipo no juegue más de un partido en la fase (excepto grupos)
        if not es_grupos:

            cursor.execute('''
                SELECT equipo_loc, equipo_vis
                FROM partidos
                WHERE id_fase = %s
                AND (
                    LOWER(equipo_loc) = LOWER(%s)
                    OR LOWER(equipo_vis) = LOWER(%s)
                )
            ''', (id_fase, equipo_local, equipo_local))

            if cursor.fetchone():
                cursor.close()
                conn.close()
                return error_response(
                    409,
                    "CONFLICT",
                    "Conflicto de datos",
                    "El equipo local ya tiene un partido en esta fase",
                    {
                        "invalid_fields": [
                            {
                                "field": "equipo_local",
                                "value": equipo_local,
                                "reason": "Ya tiene un partido en esta fase",
                                "details": {
                                    "fase": nombre_fase
                                }
                            }
                        ]
                    }
                )

            cursor.execute('''
                SELECT equipo_loc, equipo_vis
                FROM partidos
                WHERE id_fase = %s
                AND (
                    LOWER(equipo_loc) = LOWER(%s)
                    OR LOWER(equipo_vis) = LOWER(%s)
                )
            ''', (id_fase, equipo_visitante, equipo_visitante))

            if cursor.fetchone():
                cursor.close()
                conn.close()
                return error_response(
                    409,
                    "CONFLICT",
                    "Conflicto de datos",
                    "El equipo visitante ya tiene un partido en esta fase",
                    {
                        "invalid_fields": [
                            {
                                "field": "equipo_visitante",
                                "value": equipo_visitante,
                                "reason": "Ya tiene un partido en esta fase",
                                "details": {
                                    "fase": nombre_fase
                                }
                            }
                        ]
                    }
                )


        # Evitar duplicado en misma fase
        cursor.execute('''
            SELECT 1
            FROM partidos
            WHERE id_fase = %s
            AND (
                (LOWER(equipo_loc) = LOWER(%s) AND LOWER(equipo_vis) = LOWER(%s))
                OR
                (LOWER(equipo_loc) = LOWER(%s) AND LOWER(equipo_vis) = LOWER(%s))
            )
        ''', (
            id_fase,
            equipo_local, equipo_visitante,
            equipo_visitante, equipo_local
        ))

        if cursor.fetchone():
            cursor.close()
            conn.close()
            return error_response(
                409,
                "CONFLICT",
                "Conflicto de datos",
                "El partido ya existe en esta fase",
                {
                    "conflict": {
                        "fase": nombre_fase,
                        "equipo_local": equipo_local,
                        "equipo_visitante": equipo_visitante
                    }
                }
            )

        # Validar duplicados en otras fases
        cursor.execute('''
            SELECT f.nombre
            FROM partidos p
            JOIN fases f ON p.id_fase = f.id_fase
            WHERE (
                (LOWER(p.equipo_loc) = LOWER(%s) AND LOWER(p.equipo_vis) = LOWER(%s))
                OR
                (LOWER(p.equipo_loc) = LOWER(%s) AND LOWER(p.equipo_vis) = LOWER(%s))
            )
        ''', (
            equipo_local, equipo_visitante,
            equipo_visitante, equipo_local
        ))

        partidos_existentes = cursor.fetchall()

        fases_permitidas_repetir = ["Cuartos", "Semifinal", "Tercer Puesto", "Final"]

        for (fase_existente,) in partidos_existentes:

            if fase_existente.lower() != "grupos":
                cursor.close()
                conn.close()
                return error_response(
                    409,
                    "CONFLICT",
                    "Conflicto de datos",
                    "El partido ya fue jugado en otra fase",
                    {
                        "conflict": {
                            "fase_existente": fase_existente
                        }
                    }
                )

            if nombre_fase not in fases_permitidas_repetir:
                cursor.close()
                conn.close()
                return error_response(
                    409,
                    "CONFLICT",
                    "Repetición no permitida",
                    "Un partido de grupos solo puede repetirse en fases finales",
                    {
                        "invalid_transition": {
                            "fase_origen": "Grupos",
                            "fase_destino": nombre_fase
                        }
                    }
                )

        # Insertar partido
        cursor.execute('''
            INSERT INTO partidos 
            (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            equipo_local,
            equipo_visitante,
            data.get('estadio', 'A confirmar'),
            data.get('ciudad', 'A confirmar'),
            data['fecha'],
            id_fase
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Partido creado exitosamente"
        }), 201

    except Exception as e:
        return error_response(
            500,
            "INTERNAL_SERVER_ERROR",
            "Error interno del servidor",
            "Ocurrió un error inesperado",
            {"detail": str(e)}
        )
