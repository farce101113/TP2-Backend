from flask import Flask, request, jsonify, Blueprint
from db import get_db_connection

ranking_bp = Blueprint('ranking', __name__)

# GET /ranking
@ranking_bp.route('/', methods=['GET'])
def ranking():
    try:
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)

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
        for i, fila in enumerate(resultados):
            posicion = offset + i + 1

            ranking.append({
                "posicion": posicion,
                "id_usuario": fila["id_usuario"],
                "nombre": fila["nombre"],
                "puntos": fila["puntos"]
            })

        cursor.close()
        conn.close()

        return jsonify({
            "data": ranking,
            "total": total,
            "limit": limit,
            "offset": offset
        }), 200
    
    except Exception as e:
        return jsonify({
            'code' : 'INTERNAL SERVER_ERROR',
            'message' : 'Ocurrio un error al procesar la solicitud de partidosl',
            'level' : 'error',
            'description' : str(e)
        }), 500
