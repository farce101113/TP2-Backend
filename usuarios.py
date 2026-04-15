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
