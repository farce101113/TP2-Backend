# 🏆 Prode Mundial 2026 - Backend

Backend desarrollado en Flask para la gestión de un sistema de predicciones (prode) basado en el fixture del Mundial 2026.

---

## 📦 Requisitos

Antes de comenzar, asegurarse de tener instalado:

* Python 3
* MySQL
* pip

---

## 🚀 Instalación rápida (recomendada)

El proyecto incluye un script que automatiza todo el proceso:

```bash
./setup.sh
```

Este script realiza:

* Creación del entorno virtual (`.venv`)
* Instalación de dependencias
* Inicialización de la base de datos
* Carga de datos (`seed.sql`)
* Levanta el servidor Flask

---

## ⚙️ Instalación manual

### 1. Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 2. Instalar dependencias

```bash
pip install flask flask-cors mysql-connector-python
```

---

### 3. Configurar MySQL

Asegurarse de que MySQL esté corriendo:

```bash
sudo systemctl start mysql
```

---

### 4. Inicializar base de datos

```bash
python init_db.py
```

---

### 5. Cargar datos iniciales

```bash
mysql -u root -p prode < seed.sql
```

---

### 6. Ejecutar backend

```bash
python app.py
```

Servidor disponible en:

```text
http://localhost:5000
```

---

## 📡 Endpoints

### 🔹 Obtener partidos

```http
GET /partidos/
```

Ejemplo:

```bash
curl http://localhost:5000/partidos/
```

---

## 📁 Estructura del proyecto

```
TP2-Backend/
│
├── app.py              # Punto de entrada Flask
├── db.py               # Conexión a la base de datos
├── init_db.py          # Script para crear estructura
├── init_db.sql         # Definición de tablas
├── seed.sql            # Datos iniciales
├── partidos.py         # Rutas de partidos
├── usuarios.py         # Rutas de usuarios
├── setup.sh            # Script de automatización
└── README.md
```

---

## 🗄️ Base de datos

Nombre de la base:

```
prode
```

Tablas principales:

* `fases`
* `partidos`
* `usuarios`
* `predicciones`
* `clasificados`

---

## ⚠️ Notas importantes

* El proyecto utiliza el usuario `root` de MySQL
* La contraseña configurada es:

```
2026
```

* El script `setup.sh` **resetea la base de datos** en cada ejecución

---

## 🧪 Testing rápido

Una vez levantado el servidor:

```bash
curl http://localhost:5000/partidos/
```

---

## 💡 Recomendaciones

* Usar entorno virtual (`.venv`)
* No modificar directamente `seed.sql` sin reiniciar la DB
* Ejecutar siempre `setup.sh` para evitar inconsistencias

---
