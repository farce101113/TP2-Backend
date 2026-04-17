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

# Funciones auxiliares para validaciones comunes
def validar_campos_obligatorios(data, campos):
    faltantes = [c for c in campos if c not in data or data[c] is None]
    if faltantes:
        return error_response(
            400,
            "BAD_REQUEST",
            "Faltan campos obligatorios",
            "Se requieren ciertos campos",
            {
                "invalid_fields": [
                    {"field": c, "reason": "Campo requerido"} for c in faltantes
                ]
            }
        )
    return None

# Funciones para validaciones específicas de lógica de negocio
def obtener_equipo(cursor, nombre):
    cursor.execute('''
        SELECT pais_clasificado, grupo
        FROM clasificados
        WHERE LOWER(pais_clasificado) = LOWER(%s)
    ''', (nombre,))
    return cursor.fetchone()

# Función para obtener fase por nombre (case insensitive)
def obtener_fase(cursor, nombre):
    cursor.execute(
        'SELECT id_fase, nombre FROM fases WHERE LOWER(nombre) = LOWER(%s)',
        (nombre,)
    )
    return cursor.fetchone()

# Validación de lógica específica para creación/actualización de partidos
def validar_logica_partido(cursor, data, partido_id=None):
    equipo_local = data['equipo_local']
    equipo_visitante = data['equipo_visitante']

    # Equipos iguales
    if equipo_local.lower() == equipo_visitante.lower():
        return error_response(
            400, "BAD_REQUEST",
            "Equipos inválidos",
            "Un equipo no puede jugar contra sí mismo"
        )

    # Buscar equipos
    local = obtener_equipo(cursor, equipo_local)
    visitante = obtener_equipo(cursor, equipo_visitante)

    if not local or not visitante:
        return error_response(
            400, "BAD_REQUEST",
            "Equipos inválidos",
            "Uno o más equipos no están clasificados"
        )

    # Buscar fase nueva
    fase = obtener_fase(cursor, data['fase'])
    if not fase:
        return error_response(
            400, "BAD_REQUEST",
            "Fase inválida",
            "La fase no existe"
        )

    id_fase = fase["id_fase"]
    nombre_fase = fase["nombre"]
    es_grupos = nombre_fase.lower() == "grupos"
    fase_actual_nombre = None

    if partido_id:
        cursor.execute('''
            SELECT f.nombre
            FROM partidos p
            JOIN fases f ON p.id_fase = f.id_fase
            WHERE p.id_partido = %s
        ''', (partido_id,))
        
        fila = cursor.fetchone()
        if fila:
            fase_actual_nombre = fila["nombre"]

    # Valida transición de fases (si viene fase actual)
    if fase_actual_nombre:
        fase_actual = fase_actual_nombre.lower()
        fase_nueva = nombre_fase.lower()

        fases_finales = ["cuartos", "semifinal", "tercer puesto", "final"]

        if fase_actual == "grupos":
            if fase_nueva not in ["grupos"] + fases_finales:
                return error_response(
                    409,
                    "CONFLICT",
                    "Transición de fase inválida",
                    "Un partido de grupos solo puede mantenerse o pasar a fases finales"
                )

    # Validar que ambos equipos sean del mismo grupo si la fase es de grupos
    if es_grupos and local["grupo"] != visitante["grupo"]:
        return error_response(
            400, "BAD_REQUEST",
            "Grupos incompatibles",
            "Equipos en distintos grupos"
        )

    # Validar que no se repitan partidos en la misma fase
    filtro_id = ""
    params_extra = ()

    if partido_id:
        filtro_id = "AND id_partido != %s"
        params_extra = (partido_id,)

    # Validar que no exista el mismo partido en la misma fase
    cursor.execute(f'''
        SELECT 1 FROM partidos
        WHERE id_fase = %s
        {filtro_id}
        AND (
            (LOWER(equipo_loc) = LOWER(%s) AND LOWER(equipo_vis) = LOWER(%s))
            OR
            (LOWER(equipo_loc) = LOWER(%s) AND LOWER(equipo_vis) = LOWER(%s))
        )
    ''', (
        id_fase,
        *params_extra,
        equipo_local, equipo_visitante,
        equipo_visitante, equipo_local
    ))

    if cursor.fetchone():
        return error_response(
            409, "CONFLICT",
            "Conflicto de datos",
            "El partido ya existe en esta fase"
        )

    # Validar que un mismo equipo no juegue más de una vez en fases de grupos
    if not es_grupos:

        # equipo local
        cursor.execute(f'''
            SELECT 1 FROM partidos
            WHERE id_fase = %s
            {filtro_id}
            AND (
                LOWER(equipo_loc) = LOWER(%s)
                OR LOWER(equipo_vis) = LOWER(%s)
            )
        ''', (id_fase, *params_extra, equipo_local, equipo_local))

        if cursor.fetchone():
            return error_response(
                409, "CONFLICT",
                "Conflicto de datos",
                "El equipo local ya tiene un partido en esta fase"
            )

        # equipo visitante
        cursor.execute(f'''
            SELECT 1 FROM partidos
            WHERE id_fase = %s
            {filtro_id}
            AND (
                LOWER(equipo_loc) = LOWER(%s)
                OR LOWER(equipo_vis) = LOWER(%s)
            )
        ''', (id_fase, *params_extra, equipo_visitante, equipo_visitante))

        if cursor.fetchone():
            return error_response(
                409, "CONFLICT",
                "Conflicto de datos",
                "El equipo visitante ya tiene un partido en esta fase"
            )

    # Validar que no se repita el mismo enfrentamiento en fases distintas (salvo grupos → finales)

    cursor.execute(f'''
        SELECT f.nombre
        FROM partidos p
        JOIN fases f ON p.id_fase = f.id_fase
        WHERE (
            (LOWER(p.equipo_loc) = LOWER(%s) AND LOWER(p.equipo_vis) = LOWER(%s))
            OR
            (LOWER(p.equipo_loc) = LOWER(%s) AND LOWER(p.equipo_vis) = LOWER(%s))
        )
        {f"AND p.id_partido != %s" if partido_id else ""}
    ''', (
        equipo_local, equipo_visitante,
        equipo_visitante, equipo_local,
        *params_extra
    ))

    partidos_existentes = cursor.fetchall()

    fases_permitidas_repetir = ["Cuartos", "Semifinal", "Tercer Puesto", "Final"]

    for (fase_existente,) in partidos_existentes:

        # Si ya se jugó en fase que no es grupos
        if fase_existente.lower() != "grupos":
            return error_response(
                409,
                "CONFLICT",
                "Conflicto de datos",
                "El partido ya fue jugado en otra fase"
            )

        # Si viene de grupos → solo fases finales
        if nombre_fase not in fases_permitidas_repetir:
            return error_response(
                409,
                "CONFLICT",
                "Repetición no permitida",
                "Un partido de grupos solo puede repetirse en fases finales"
            )

    return {
        "ok": True,
        "id_fase": id_fase,
        "nombre_fase": nombre_fase,
        "es_grupos": es_grupos
    }


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
            'message' : 'Ocurrio un error al procesar la solicitud de partidos',
            'level' : 'error',
            'description' : str(e)
                
        }), 500


@partidos_bp.route('/<int:id>', methods=['PATCH'])
def patch_partido(id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM partidos WHERE id_partido = %s', (id,))
        actual = cursor.fetchone()

        if not actual:
            cursor.close()
            conn.close()
            return error_response(
                404, "NOT_FOUND",
                "Partido no encontrado",
                f"id {id} inexistente"
            )

        # Merge estado actual + cambios
        data_completo = {
            "equipo_local": data.get("equipo_local", actual["equipo_loc"]),
            "equipo_visitante": data.get("equipo_visitante", actual["equipo_vis"]),
            "fecha": data.get("fecha", actual["fecha"]),
            "fase": data.get("fase")  # puede ser None
        }

        # Si no vino fase → reconstruir nombre
        if not data_completo["fase"]:
            cursor.execute(
                '''SELECT nombre FROM fases WHERE id_fase = %s''',
                (actual["id_fase"],)
            )
            data_completo["fase"] = cursor.fetchone()["nombre"]

        resultado = validar_logica_partido(cursor, data_completo, partido_id=id)
        if "ok" not in resultado:
            cursor.close()
            conn.close()
            return resultado

        cursor.execute('''
            UPDATE partidos
            SET equipo_loc=%s, equipo_vis=%s, fecha=%s, id_fase=%s
            WHERE id_partido=%s
        ''', (
            data_completo["equipo_local"],
            data_completo["equipo_visitante"],
            data_completo["fecha"],
            resultado["id_fase"],
            id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return '', 204

    except Exception as e:
        return error_response(500, "INTERNAL_SERVER_ERROR", "Error interno", str(e))

# DELETE partidos
@partidos_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_partido(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificamos si existe
        cursor.execute('SELECT id_partido FROM partidos WHERE id_partido = %s', (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'code': 'NOT_FOUND',
                'message': f'No se encontró el partido con id {id}',
                'level': 'error',
                'description': f'No existe un partido con el id {id} en la base de datos'
            }), 404
        
        cursor.execute('DELETE FROM partidos WHERE id_partido = %s', (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return '', 204
        
    except Exception as e:
        return jsonify({
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'Ocurrió un error al eliminar el partido',
            'level': 'error',
            'description': str(e)
        }), 500

@partidos_bp.route('/<int:id>/resultado', methods=['PUT', 'OPTIONS'])
def put_resultado(id):
    data = request.get_json()

    # Validación de campos obligatorios (según Swagger)
    if not data or 'local' not in data or 'visitante' not in data:
        return jsonify({
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'Ocurrió un error al eliminar el partido',
            'level': 'error',
            'description': str(e)
        }), 500


@partidos_bp.route('/<int:id>', methods=['PUT'])
def put_partido(id):
    try:
        data = request.get_json()

        error = validar_campos_obligatorios(
            data,
            ['equipo_local', 'equipo_visitante', 'fecha', 'fase']
        )
        if error:
            return error

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM partidos WHERE id_partido = %s', (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return error_response(
                404, "NOT_FOUND",
                "Partido no encontrado",
                f"id {id} inexistente"
            )

        resultado = validar_logica_partido(cursor, data, partido_id=id)
        if "ok" not in resultado:
            cursor.close()
            conn.close()
            return resultado

        cursor.execute('''
            UPDATE partidos
            SET equipo_loc=%s, equipo_vis=%s, fecha=%s, id_fase=%s
            WHERE id_partido=%s
        ''', (
            data['equipo_local'],
            data['equipo_visitante'],
            data['fecha'],
            resultado["id_fase"],
            id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return '', 204

    except Exception as e:
        return error_response(500, "INTERNAL_SERVER_ERROR", "Error interno", str(e))

# POST /partidos/id/prediccion
@partidos_bp.route('/<int:id_partido>/prediccion', methods=['POST'])
def prediccion(id_partido):
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'code': 'BAD_REQUEST',
                'message': 'Body requerido',
                'level': 'error',
                'description': 'El cuerpo de la solicitud debe contener un JSON con id_usuario, goles_loc y goles_vis'
            }), 400

        id_usuario = data.get('id_usuario')
        goles_loc = data.get('goles_loc')
        goles_vis = data.get('goles_vis')

        if id_usuario is None or goles_loc is None or goles_vis is None:
            return jsonify({
                'code': 'BAD_REQUEST',
                'message': 'Faltan datos obligatorios',
                'level': 'error',
                'description': 'Los campos id_usuario, goles_loc y goles_vis son requeridos'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""SELECT goles_loc, goles_vis FROM partidos WHERE id_partido = %s""", (id_partido,))

        partido = cursor.fetchone()

        if not partido:
            return jsonify({
                'code': 'NOT_FOUND',
                'message': 'Partido no encontrado',
                'level': 'error',
                'description': f'No existe un partido con id {id_partido}'
            }), 404

        if partido[0] is not None and partido[1] is not None:
            return jsonify({
                'code': 'BAD_REQUEST',
                'message': 'El partido ya fue jugado',
                'level': 'error',
                'description': f'El partido con id {id_partido} ya tiene resultados registrados'
            }), 400

        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                'code': 'NOT_FOUND',
                'message': 'Usuario no encontrado',
                'level': 'error',
                'description': f'No existe un usuario con id {id_usuario}'
            }), 404

        cursor.execute("""
                    SELECT id_prediccion FROM predicciones 
                    WHERE id_usuario = %s AND id_partido = %s
        """, (id_usuario, id_partido))

        prediccion = cursor.fetchone()

        if prediccion:
            return jsonify({
                'code': 'CONFLICT',
                'message': 'Prediccion ya registrada',
                'level': 'error',
                'description': f'El usuario con id {id_usuario} ya hizo una prediccion para el partido con id {id_partido}'
            }), 409

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
    
    except Exception as e:
        return jsonify({
            'code' : 'INTERNAL SERVER_ERROR',
            'message' : 'Ocurrio un error al procesar la solicitud de partidosl',
            'level' : 'error',
            'description' : str(e)
        }), 500

@partidos_bp.route('/', methods=['POST'])
def create_partido():
    try:
        data = request.get_json()

        error = validar_campos_obligatorios(
            data,
            ['equipo_local', 'equipo_visitante', 'fecha', 'fase']
        )
        if error:
            return error

        conn = get_db_connection()
        cursor = conn.cursor()

        resultado = validar_logica_partido(cursor, data)
        if "ok" not in resultado:
            cursor.close()
            conn.close()
            return resultado

        cursor.execute('''
            INSERT INTO partidos 
            (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data['equipo_local'],
            data['equipo_visitante'],
            data.get('estadio', 'A confirmar'),
            data.get('ciudad', 'A confirmar'),
            data['fecha'],
            resultado["id_fase"]
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Partido creado exitosamente"}), 201

    except Exception as e:
        return error_response(
            500,
            "INTERNAL_SERVER_ERROR",
            "Error interno",
            str(e)
        )
