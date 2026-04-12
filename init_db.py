import mysql.connector

with open('init_db.sql', 'r') as f:
    sql = f.read()

conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    password='2026'
)

cursor = conn.cursor()
for statement in sql.split(';'):
    if statement.strip():
        print(statement)
        cursor.execute(statement)
        conn.commit()
        print('Executed successfully')

cursor.close()
conn.close()