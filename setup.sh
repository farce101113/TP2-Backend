#!/bin/bash

echo "🚀 Iniciando setup del proyecto Prode..."

# -------------------------

# 1. Crear entorno virtual

# -------------------------

if [ ! -d ".venv" ]; then
echo "📦 Creando entorno virtual..."
python3 -m venv .venv
fi

# Activar entorno virtual

echo "⚙️ Activando entorno virtual..."
source .venv/bin/activate

# -------------------------

# 2. Instalar dependencias

# -------------------------

echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install flask flask-cors mysql-connector-python

# -------------------------

# 3. Verificar MySQL

# -------------------------

echo "🐬 Verificando MySQL..."
if ! systemctl is-active --quiet mysql; then
echo "⚠️ MySQL no está corriendo. Intentando iniciarlo..."
sudo systemctl start mysql
fi

# -------------------------
# 4. Resetear DB
# -------------------------
echo "🧹 Reseteando base de datos..."
mysql -u root -p'2026' -e "DROP DATABASE IF EXISTS prode; CREATE DATABASE prode;"

# -------------------------
# 5. Inicializar DB
# -------------------------
echo "🗄️ Creando estructura..."
python init_db.py

# -------------------------
# 6. Cargar seed
# -------------------------
echo "🌱 Cargando datos..."
mysql -u root -p'2026' prode < seed.sql

if [ $? -ne 0 ]; then
echo "❌ Error cargando seed.sql"
exit 1
fi

echo "✅ Base de datos lista"

# -------------------------

# 6. Levantar backend

# -------------------------

echo "🚀 Levantando servidor Flask..."

python app.py
