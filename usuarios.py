from flask import jsonify, Blueprint
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