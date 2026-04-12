CREATE DATABASE IF NOT EXISTS prode;
USE prode;

CREATE TABLE IF NOT EXISTS fases (
    id_fase INT AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (id_fase)
);

CREATE TABLE IF NOT EXISTS partidos (
    id_partido INT NOT NULL AUTO_INCREMENT,
    equipo_loc VARCHAR(50) NOT NULL,
    equipo_vis VARCHAR(50) NOT NULL,
    estadio VARCHAR(50) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    fecha DATETIME NOT NULL,
    id_fase INT NOT NULL,
    goles_loc INT UNSIGNED,
    goles_vis INT UNSIGNED,
    PRIMARY KEY (id_partido),
    FOREIGN KEY (id_fase) REFERENCES fases(id_fase)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    mail VARCHAR(50) NOT NULL UNIQUE,
    puntos INT DEFAULT 0,
    PRIMARY KEY (id_usuario)
);

CREATE TABLE IF NOT EXISTS predicciones (
    id_prediccion INT NOT NULL AUTO_INCREMENT,
    id_partido INT NOT NULL,
    id_usuario INT NOT NULL,
    goles_loc INT UNSIGNED,
    goles_vis INT UNSIGNED,
    PRIMARY KEY (id_prediccion),
    FOREIGN KEY (id_partido) REFERENCES partidos(id_partido) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    UNIQUE (id_partido, id_usuario)
);

CREATE TABLE IF NOT EXISTS clasificados (
    id_clasificado INT NOT NULL AUTO_INCREMENT,
    grupo VARCHAR(1) NOT NULL,
    pais_clasificado VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_clasificado)
);