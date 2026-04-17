# TP2-Backend - API Fixture + ProDe Mundial 2026

Backend desarrollado en **Flask** + **MySQL** para gestionar el fixture del Mundial 2026 y el sistema de pronósticos (ProDe).

El proyecto cumple **exactamente** con el contrato definido en `swagger.yaml`.

---

## 📦 Requisitos

- Python 3.8+
- MySQL (servidor corriendo)
- pip

---

## 🚀 Instalación y ejecución (recomendado)

```bash
./setup.sh
Este script:

Crea/actualiza el entorno virtual .venv
Instala todas las dependencias
Reinicia y carga la base de datos
Levanta el servidor en http://localhost:5000


⚙️ Instalación manual
Bashpython3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors mysql-connector-python
python init_db.py
mysql -u root -p prode < seed.sql
python app.py

📡 Ejemplos de uso (Postman)
PARTIDOS
GET /partidos

Método: GET
Url: /partidos
Body: Sin body (query params opcionales: equipo, fecha, fase, _limit, _offset)

POST /partidos

Método: POST
Url: /partidos
Body:JSON{
  "equipo_local": "Argentina",
  "equipo_visitante": "Brasil",
  "fecha": "2026-06-15",
  "fase": "grupos"
}

GET /partidos/{id}

Método: GET
Url: /partidos/1
Body: Sin body

PUT /partidos/{id}

Método: PUT
Url: /partidos/1
Body:JSON{
  "equipo_local": "Argentina",
  "equipo_visitante": "Brasil",
  "fecha": "2026-06-15",
  "fase": "grupos"
}

PATCH /partidos/{id}

Método: PATCH
Url: /partidos/1
Body: (al menos un campo)JSON{
  "fecha": "2026-06-20"
}

DELETE /partidos/{id}

Método: DELETE
Url: /partidos/1
Body: Sin body

PUT /partidos/{id}/resultado

Método: PUT
Url: /partidos/1/resultado
Body:JSON{
  "local": 2,
  "visitante": 1
}

POST /partidos/{id}/prediccion

Método: POST
Url: /partidos/1/prediccion
Body:JSON{
  "id_usuario": 1,
  "local": 2,
  "visitante": 1
}

USUARIOS
POST /usuarios

Método: POST
Url: /usuarios
Body:JSON{
  "nombre": "Juan Pérez",
  "email": "juan@test.com"
}

GET /usuarios

Método: GET
Url: /usuarios
Body: Sin body (query params: _limit, _offset)

GET /usuarios/{id}

Método: GET
Url: /usuarios/1
Body: Sin body

PUT /usuarios/{id}

Método: PUT
Url: /usuarios/1
Body:JSON{
  "nombre": "Juan Pérez",
  "email": "juan@test.com"
}

DELETE /usuarios/{id}

Método: DELETE
Url: /usuarios/1
Body: Sin body

RANKING
GET /ranking

Método: GET
Url: /ranking
Body: Sin body (query params: _limit, _offset)


🗄️ Base de datos

Nombre: prode
Usuario: root
Contraseña: 2026


📋 Supuestos / Hipótesis

No se implementó autenticación (según enunciado).
estadio y ciudad están en la BD pero no se usan en el contrato Swagger.
Solo se permite una predicción por usuario por partido.
Los puntos del ranking se calculan automáticamente (3/1/0).
Paginación HATEOAS implementada en todos los listados.


🛠️ Tecnologías

Framework: Flask
Base de datos: MySQL
Contrato: OpenAPI 3.0 (swagger.yaml)