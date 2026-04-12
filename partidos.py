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

