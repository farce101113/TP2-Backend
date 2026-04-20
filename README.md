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
```

Este script:

- Crea/actualiza el entorno virtual .venv
- Instala todas las dependencias
- Reinicia y carga la base de datos
- Levanta el servidor en http://localhost:5000

## ⚙️ Instalación manual

```Bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors mysql-connector-python
python init_db.py
mysql -u root -p prode < seed.sql
python app.py
```

## 📡 Ejemplos de uso

PARTIDOS

GET /partidos

- Método: GET
- Url: http://127.0.0.1:5000/partidos
- Body: Sin body (query params opcionales: equipo, fecha, fase, _limit, _offset)


POST /partidos

- Método: POST
- Url: http://127.0.0.1:5000/partidos
- Body:
```JSON
{
  "equipo_local": "Argentina",
  "equipo_visitante": "Brasil",
  "fecha": "2026-06-15",
  "fase": "grupos"
}
```


GET /partidos/{id}

- Método: GET
- Url: http://127.0.0.1:5000/partidos/1
- Body: Sin body


PUT /partidos/{id}

- Método: PUT
- Url: http://127.0.0.1:5000/partidos/1
- Body:
```JSON
{
  "equipo_local": "Argentina",
  "equipo_visitante": "Brasil",
  "fecha": "2026-06-15",
  "fase": "grupos"
}
```


PATCH /partidos/{id}

- Método: PATCH
- Url: http://127.0.0.1:5000/partidos/1
- Body: (al menos un campo)
```JSON
{
  "fecha": "2026-06-20"
}
```


DELETE /partidos/{id}

- Método: DELETE
- Url: http://127.0.0.1:5000/partidos/1
- Body: Sin body


PUT /partidos/{id}/resultado

- Método: PUT
- Url: http://127.0.0.1:5000/partidos/1/resultado
- Body:
```JSON
{
  "local": 2,
  "visitante": 1
}
```


POST /partidos/{id}/prediccion

- Método: POST
- Url: http://127.0.0.1:5000/partidos/1/prediccion
- Body:
```JSON
{
  "id_usuario": 1,
  "local": 2,
  "visitante": 1
}
```

USUARIOS

POST /usuarios

- Método: POST
- Url: http://127.0.0.1:5000/usuarios
- Body:
```JSON
{
  "nombre": "Juan Pérez",
  "email": "juan@test.com"
}
```


GET /usuarios

- Método: GET
- Url: http://127.0.0.1:5000/usuarios
- Body: Sin body (query params: _limit, _offset)


GET /usuarios/{id}

- Método: GET
- Url: http://127.0.0.1:5000/usuarios/1
- Body: Sin body


PUT /usuarios/{id}

- Método: PUT
- Url: http://127.0.0.1:5000/usuarios/1
- Body:
```JSON
{
  "nombre": "Juan Pérez",
  "email": "juan@test.com"
}
```


DELETE /usuarios/{id}

- Método: DELETE
- Url: http://127.0.0.1:5000/usuarios/1
- Body: Sin body

RANKING

GET /ranking

- Método: GET
- Url: http://127.0.0.1:5000/ranking
- Body: Sin body (query params: _limit, _offset)

## 🗄️ Base de datos

- Nombre: prode
- Usuario: root
- Contraseña: 2026

## 📋 Supuestos / Hipótesis

- No se implementó autenticación (según enunciado).
- estadio y ciudad están en la BD pero no se usan en el contrato Swagger.
- Solo se permite una predicción por usuario por partido.
  - Las predicciones están asociadas a:
    - un usuario (id_usuario)
    - un partido (id_partido)
- Los puntos del ranking se calculan en la ejecucion del endpoint ranking
- Paginación HATEOAS implementada en todos los listados.
- La base de datos está compuesta por las siguientes tablas:
  - Fases: contiene las fases del torneo (grupos, dieciseisavos, octavos, etc.). Se carga automáticamente al inicializar la base y se utiliza para validar que los partidos pertenezcan a una fase válida.
  - Partidos: almacena los encuentros del fixture.
  - Usuarios: almacena los usuarios del sistema.
  - Predicciones: registra las predicciones realizadas por los usuarios, vinculadas a un partido y un usuario.
  - Clasificados: contiene los equipos clasificados al Mundial 2026 junto con su grupo. Se utiliza para validar la creación de partidos.
 - La base de datos se inicializa vacía, excepto por las tablas Fases y Clasificados, que se precargan automáticamente.

## 🏆 Reglas de negocio para PARTIDOS
- Solo se pueden crear partidos cuyos equipos estén presentes en la tabla Clasificados.
- En fase de grupos:
  - Ambos equipos deben pertenecer al mismo grupo.
- En fases eliminatorias:
  - Equipos que compartieron grupo no pueden enfrentarse en dieciseisavos ni octavos de final.
  - Sí pueden enfrentarse en:
    - Cuartos de final
    - Semifinal
    - Tercer puesto
    - Final
- Estas validaciones aplican tanto para:
  - POST /partidos
  - PUT /partidos/{id}
  - PATCH /partidos/{id}

## 🛠️ Tecnologías

- Framework: Flask
- Base de datos: MySQL
- Contrato: OpenAPI 3.0 (swagger.yaml)