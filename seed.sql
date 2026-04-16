USE prode;

-- FASES
INSERT INTO fases (nombre) VALUES
('Grupos'),
('Dieciseisavos'),
('Octavos'),
('Cuartos'),
('Semifinal'),
('Tercer Puesto'),
('Final');

-- USUARIOS
INSERT INTO usuarios (nombre, mail) VALUES
('Facundo', 'facu@gmail.com'),
('Juan', 'juan@gmail.com'),
('Maria', 'maria@gmail.com');

-- PARTIDOS - FASE DE GRUPOS (MUNDIAL 2026)

-- GRUPO A
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Mexico', 'Sudafrica', 'MetLife Stadium', 'New York', '2026-06-11 16:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Corea del Sur', 'Republica Checa', 'BMO Field', 'Toronto', '2026-06-12 23:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO B
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Canada', 'Bosnia Herzegovina', 'SoFi Stadium', 'Los Angeles', '2026-06-12 16:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Suiza', 'Qatar', 'Hard Rock Stadium', 'Miami', '2026-06-13 16:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO C
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Brasil', 'Marruecos', 'AT&T Stadium', 'Dallas', '2026-06-13 19:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Haiti', 'Escocia', 'BC Place', 'Vancouver', '2026-06-13 22:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO D
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Estados Unidos', 'Paraguay', 'Mercedes-Benz Stadium', 'Atlanta', '2026-06-12 22:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Australia', 'Turquia', 'NRG Stadium', 'Houston', '2026-06-14 01:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO E
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Alemania', 'Curazao', 'Levis Stadium', 'San Francisco', '2026-06-14 14:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Costa de Marfil', 'Ecuador', 'Lumen Field', 'Seattle', '2026-06-14 20:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO F
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Paises Bajos', 'Japon', 'Gillette Stadium', 'Boston', '2026-06-14 17:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Suecia', 'Tunez', 'Gillette Stadium', 'Boston', '2026-06-14 23:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO G
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Belgica', 'Egipto', 'Estadio Azteca', 'Ciudad de Mexico', '2026-06-15 16:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Iran', 'Nueva Zelanda', 'BBVA Stadium', 'Monterrey', '2026-06-15 22:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- GRUPO H
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Espana', 'Cabo Verde', 'Soldier Field', 'Chicago', '2026-06-15 13:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Arabia Saudita', 'Uruguay', 'Lincoln Financial Field', 'Philadelphia', '2026-06-15 19:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

 -- GRUPO I
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Francia', 'Senegal', 'Soldier Field', 'Chicago', '2026-06-16 16:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Irak', 'Noruega', 'Lincoln Financial Field', 'Philadelphia', '2026-06-16 19:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

  -- GRUPO J
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Argentina', 'Argelia', 'Soldier Field', 'Chicago', '2026-06-16 22:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Austria', 'Jordania', 'Lincoln Financial Field', 'Philadelphia', '2026-06-17 01:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

  -- GRUPO K
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Portugal', 'RD Congo', 'Soldier Field', 'Chicago', '2026-06-17 14:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Uzbekistan', 'Colombia', 'Lincoln Financial Field', 'Philadelphia', '2026-06-17 17:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

   -- GRUPO L
INSERT INTO partidos (equipo_loc, equipo_vis, estadio, ciudad, fecha, id_fase)
VALUES
('Inglaterra', 'Croacia', 'Soldier Field', 'Chicago', '2026-06-17 17:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos')),
('Ghana', 'Panama', 'Lincoln Financial Field', 'Philadelphia', '2026-06-17 20:00:00',
 (SELECT id_fase FROM fases WHERE nombre = 'Grupos'));

-- PREDICCIONES (ejemplo)

INSERT INTO predicciones (id_partido, id_usuario, goles_loc, goles_vis)
VALUES
(1, 1, 0, 2),
(1, 2, 1, 1),
(2, 3, 0, 1),
(3, 1, 3, 0),
(4, 2, 1, 0);

-- Clasificados

INSERT INTO clasificados (grupo, pais_clasificado)
VALUES
('A', 'Mexico'),
('A', 'Sudafrica'),
('A', 'Corea del Sur'),
('A', 'Republica Checa'),
('B', 'Canada'),
('B', 'Bosnia Herzegovina'),
('B', 'Suiza'),
('B', 'Qatar'),
('C', 'Brasil'),
('C', 'Marruecos'),
('C', 'Haiti'),
('C', 'Escocia'),
('D', 'Estados Unidos'),
('D', 'Paraguay'),
('D', 'Australia'),
('D', 'Turquia'),
('E', 'Alemania'),
('E', 'Curazao'),
('E', 'Costa de Marfil'),
('E', 'Ecuador'),
('F', 'Paises Bajos'),
('F', 'Japon'),
('F', 'Suecia'),
('F', 'Tunez'),
('G', 'Belgica'),
('G', 'Egipto'),
('G', 'Iran'),
('G', 'Nueva Zelanda'),
('H', 'Espana'),
('H', 'Cabo Verde'),
('H', 'Arabia Saudita'),
('H', 'Uruguay'),
('I', 'Francia'),
('I', 'Senegal'),
('I', 'Irak'),
('I', 'Noruega'),
('J', 'Argentina'),
('J', 'Argelia'),
('J', 'Austria'),
('J', 'Jordania'),
('K', 'Portugal'),
('K', 'RD Congo'),
('K', 'Uzbekistan'),
('K', 'Colombia'),
('L', 'Inglaterra'),
('L', 'Croacia'),
('L', 'Ghana'),
('L', 'Panama');