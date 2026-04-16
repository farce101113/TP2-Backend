from flask import jsonify, Blueprint, request
import mysql.connector
from db import get_db_connection

usuarios_bp = Blueprint('usuarios', __name__)

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
