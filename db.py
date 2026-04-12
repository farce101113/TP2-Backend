import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='2026',
        database='prode'
    )