from flask import jsonify, Blueprint, request
import mysql.connector
from db import get_db_connection

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/', methods=['GET'])
def get_usuarios():
    try:
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validaciones
        if limit <= 0:
            return jsonify({
                'code': 'BAD_REQUEST',
                'message': 'El parámetro limit debe ser mayor a 0',
                'level': 'error',
                'description': f'limit={limit} no es válido'
            }), 400
        
        if offset < 0:
            return jsonify({
                'code': 'BAD_REQUEST',
                'message': 'El parámetro offset debe ser mayor o igual a 0',
                'level': 'error',
                'description': f'offset={offset} no es válido'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT COUNT(*) AS total FROM usuarios')
        total = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT id_usuario, nombre, email 
            FROM usuarios 
            LIMIT %s OFFSET %s
        ''', (limit, offset))
        usuarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        base_url = request.base_url
        
        def build_url(new_offset):
            return f"{base_url}?limit={limit}&offset={new_offset}"
        
        first = build_url(0)
        prev = build_url(max(offset - limit, 0)) if offset > 0 else None
        next = build_url(offset + limit) if offset + limit < total else None
        last_offset = ((total - 1) // limit) if total > 0 else 0
        last = build_url(last_offset)
        
        response = {
            'data': usuarios,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total,
                'links': {
                    'first': first,
                    'prev': prev,
                    'next': next,
                    'last': last
                }
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'Error al obtener usuarios',
            'level': 'error',
            'description': str(e)
        }), 500

@usuarios_bp.route('/<int:id>', methods=['GET'])
def get_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT id, nombre, email FROM usuarios WHERE id = %s', (id,))
    usuario = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if usuario:
        return jsonify(usuario), 200
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
@usuarios_bp.route('/', methods=['POST'])
def crear_usuario():
    data = request.get_json()

    if not data:
        return jsonify({
            "errors": [{"message": "Body requerido"}]
        }), 400

    nombre = data.get("nombre")
    email = data.get("email")

    if not nombre or not email:
        return jsonify({
            "errors": [{"message": "nombre y email son obligatorios"}]
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre, email) VALUES (%s, %s)",
            (nombre, email)
        )
        conn.commit()

        return "", 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "errors": [{"message": "email ya existe"}
            ]
        }), 409

    except Exception:
        return jsonify({
            "errors": [{"message": "error interno"}]
        }), 500

    finally:
        cursor.close()
        conn.close()
@usuarios_bp.route('/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM usuarios WHERE id = %s', (id,))
    usuario = cursor.fetchone()

    if usuario:
        cursor.execute('DELETE FROM usuarios WHERE id = %s', (id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"mensaje": "Usuario eliminado"}), 200
    else:
        cursor.close()
        conn.close()

        return jsonify({"error": "Usuario no encontrado"}), 404

@usuarios_bp.route('/<int:id>', methods=['PUT'])
def modificar_usuario(id):
    data = request.get_json()

    if not data:
        return jsonify({"errors": [{"message": "Body requerido"}]}), 400

    nombre = data.get("nombre")
    email = data.get("email")

    if not nombre or not email:
        return jsonify({"errors": [{"message": "nombre y email son obligatorios"}]}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s",
            (nombre, email, id)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"errors": [{"message": "Usuario no encontrado"}]}), 404

        return jsonify({"id": id, "nombre": nombre, "email": email}), 200

    except mysql.connector.IntegrityError:
        return jsonify({"errors": [{"message": "email ya está en uso por otro usuario"}]}), 409
    except Exception:
        return jsonify({"errors": [{"message": "error interno"}]}), 500
    finally:
        cursor.close()
        conn.close()
