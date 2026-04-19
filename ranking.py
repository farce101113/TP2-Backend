from flask import Flask, request, jsonify, Blueprint
from db import get_db_connection

ranking_bp = Blueprint('ranking', __name__)

# GET /ranking
@ranking_bp.route('/', methods=['GET'])
def ranking():
    try:
        limit = request.args.get('_limit', default=10, type=int)
        offset = request.args.get('_offset', default=0, type=int)

        if limit < 0 or offset < 0:
            return jsonify({
                'code': 'BAD REQUEST',
                'message': 'Los parametros limit y offset no son validos',
                'level': 'error',
                'description': 'El valor de limit y offset deben ser un numero entero mayor o igual a 0'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Total de usuarios
        cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
        total = cursor.fetchone()["total"]

        # Query con cálculo dinámico de puntos
        query = """
            SELECT 
                u.id_usuario,
                u.nombre,
                COALESCE(SUM(
                    CASE
                        WHEN p.goles_loc IS NULL OR p.goles_vis IS NULL THEN 0

                        WHEN pr.goles_loc = p.goles_loc 
                        AND pr.goles_vis = p.goles_vis THEN 3

                        WHEN (
                            (pr.goles_loc > pr.goles_vis AND p.goles_loc > p.goles_vis) OR
                            (pr.goles_loc < pr.goles_vis AND p.goles_loc < p.goles_vis) OR
                            (pr.goles_loc = pr.goles_vis AND p.goles_loc = p.goles_vis)
                        ) THEN 1

                        ELSE 0
                    END
                ), 0) AS puntos
            FROM usuarios u
            LEFT JOIN predicciones pr 
                ON u.id_usuario = pr.id_usuario
            LEFT JOIN partidos p 
                ON pr.id_partido = p.id_partido
            GROUP BY u.id_usuario, u.nombre
            ORDER BY puntos DESC, u.nombre ASC
            LIMIT %s OFFSET %s
        """

        cursor.execute(query, (limit, offset))
        resultados = cursor.fetchall()

        ranking = []
        for fila in resultados:
            ranking.append({
                "id_usuario": fila["id_usuario"],
                "nombre": fila["nombre"],
                "puntos": fila["puntos"]
            })

        base_url = request.base_url
        def build_url(new_offset):
            return f'{base_url}?_limit={limit}&_offset={new_offset}'

        first = build_url(0)

        prev = build_url(offset - limit) if offset > 0 else None

        next = build_url(offset + limit) if offset + limit < total else None

        last_offset = max(total - limit, 0)
        last = build_url(last_offset)

        links = {
            '_first': {'href': first},
            'prev': {'href': prev} if prev else None,
            'next': {'href': next} if next else None,
            'last': {'href': last}
        }

        cursor.close()
        conn.close()

        return jsonify({
            "data": ranking,
            "links": links
        }), 200
    
    except Exception as e:
        return jsonify({
            'code' : 'INTERNAL SERVER_ERROR',
            'message' : 'Ocurrio un error al procesar la solicitud de partidosl',
            'level' : 'error',
            'description' : str(e)
        }), 500
