-- ============================================================
-- Esquema base de datos MONTERRA · Sistema de Taller
-- ============================================================
-- Licencia MIT © 2026 David Plascencia
-- Se ejecuta una vez al primer arranque; DB_INIT en app.py
-- Controlado por alembic/manual; ver db.py para migraciones

PRAGMA foreign_keys = ON;

-- Catálogo de sistemas de ventanas/puertas (fuente: proyecto_ventanas_normalizado.json)
CREATE TABLE IF NOT EXISTS catalogo_sistemas (
    sistema_id TEXT PRIMARY KEY,         -- ej: 'corrediza_3', 'puerta_abitable'
    nombre TEXT NOT NULL,
    descripcion TEXT,                    -- opcional
    formulas_json TEXT NOT NULL,         -- copia del JSON normalizado (para auditoría)
    activo INTEGER DEFAULT 1             -- 0 = deshabilitado, 1 = activo
);

-- Catálogo de materiales/herrajes (fuente: mismo JSON o catálogo externo)
CREATE TABLE IF NOT EXISTS catalogo_materiales (
    material_id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    unidad TEXT NOT NULL,               -- 'mm', 'pieza', 'metro_lineal', 'm2'
    precio_unitario REAL,               -- opcional, para futuras cotizaciones
    observaciones TEXT                  -- ej: 'Carretilla tandem, solo V-01'
);

-- Torres del proyecto (lectura, de monterra.json)
CREATE TABLE IF NOT EXISTS proyecto_torres (
    torre_codigo TEXT PRIMARY KEY,      -- 'T-01', 'T-02', 'T-03'
    nombre TEXT NOT NULL                -- 'Torre 1', 'Torre 2', 'Torre 3'
);

-- Niveles del proyecto (lectura, de monterra.json)
CREATE TABLE IF NOT EXISTS proyecto_niveles (
    torre_codigo TEXT NOT NULL,
    nivel_codigo TEXT NOT NULL,
    PRIMARY KEY (torre_codigo, nivel_codigo),
    FOREIGN KEY (torre_codigo) REFERENCES proyecto_torres(torre_codigo) ON DELETE CASCADE
);

-- Estado del proyecto: piezas a fabricar
CREATE TABLE IF NOT EXISTS piezas (
    codigo TEXT PRIMARY KEY,            -- 'V-01', 'P-01', ...
    nombre TEXT NOT NULL,               -- 'Sala PB', 'Comedor N1', ...
    sistema_id TEXT NOT NULL,
    torre TEXT,
    nivel TEXT,
    depto TEXT,
    recinto TEXT,
    ancho_mm REAL NOT NULL,
    alto_mm REAL NOT NULL,
    alto_total_mm REAL,                 -- NULL si no aplica (ej: corrediza donde alto = alto_total)
    estado TEXT NOT NULL DEFAULT 'pendiente',
    observaciones TEXT,
    FOREIGN KEY (sistema_id) REFERENCES catalogo_sistemas(sistema_id) ON DELETE RESTRICT,
    CHECK (estado IN ('pendiente', 'en_corte', 'armado', 'instalado'))
);

-- Cortes de perfil (calculados por calculos.py, estado gestionado en app)
CREATE TABLE IF NOT EXISTS cortes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pieza_codigo TEXT NOT NULL,
    material_id INTEGER,
    pieza_nombre TEXT NOT NULL,         -- copia al momento del cálculo
    longitud_mm REAL NOT NULL,
    cantidad REAL NOT NULL,
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (pieza_codigo) REFERENCES piezas(codigo) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES catalogo_materiales(material_id) ON DELETE SET NULL,
    CHECK (estado IN ('pendiente', 'cortado', 'error'))
);

-- Vidrios (calculados por calculos.py)
CREATE TABLE IF NOT EXISTS vidrios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pieza_codigo TEXT NOT NULL,
    posicion TEXT,                      -- 'panel_fijo', 'panel_corredizo', ...
    ancho_mm REAL NOT NULL,
    alto_mm REAL NOT NULL,
    cantidad REAL NOT NULL,
    espesor_mm INTEGER,                 -- 6, 8, 10 (para futuros)
    estado TEXT NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (pieza_codigo) REFERENCES piezas(codigo) ON DELETE CASCADE,
    CHECK (estado IN ('pendiente', 'cortado', 'instalado'))
);

-- Insumos (felpa, empaque, pijas, etc.)
CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pieza_codigo TEXT NOT NULL,
    material_id INTEGER,
    nombre TEXT NOT NULL,
    cantidad REAL NOT NULL,
    unidad TEXT NOT NULL,               -- 'mm', 'pieza', 'metro_lineal', 'm2'
    tipo TEXT NOT NULL DEFAULT 'fijo',  -- 'fijo', 'condicional'
    FOREIGN KEY (pieza_codigo) REFERENCES piezas(codigo) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES catalogo_materiales(material_id) ON DELETE SET NULL
);

-- Instalaciones (cuando se instala en obra)
CREATE TABLE IF NOT EXISTS instalaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pieza_codigo TEXT NOT NULL,
    operador TEXT NOT NULL,             -- nombre del instalador
    ubicacion_instalacion TEXT,         -- 'Torre T-01, PB, Sala'
    fecha_instalacion TEXT,            -- '2026-09-03'
    observaciones TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (pieza_codigo) REFERENCES piezas(codigo) ON DELETE CASCADE,
    CHECK (estado IN ('pendiente', 'instalado', 'incidencia'))
);

-- Movimientos (bitácora de cambios para auditoría)
CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,                -- '2026-09-03'
    tipo TEXT NOT NULL,                 -- 'corte_cortado', 'instalacion', 'estado_pieza'
    pieza_codigo TEXT,
    detalle TEXT                        -- JSON opcional del cambio
);

-- Vista materializada: resumen por pieza (útil para dashboard)
CREATE VIEW IF NOT EXISTS vista_resumen_pieza AS
SELECT
    p.codigo,
    p.nombre,
    p.torre,
    p.nivel,
    p.depto,
    p.recinto,
    p.estado AS estado_pieza,
    s.nombre AS sistema_nombre,
    p.ancho_mm,
    p.alto_mm,
    p.alto_total_mm,
    (SELECT COUNT(*) FROM cortes c WHERE c.pieza_codigo = p.codigo)          AS total_cortes,
    (SELECT COUNT(*) FROM cortes c WHERE c.pieza_codigo = p.codigo AND c.estado = 'cortado') AS cortes_cortados,
    (SELECT COUNT(*) FROM vidrios v WHERE v.pieza_codigo = p.codigo)          AS total_vidrios,
    (SELECT COUNT(*) FROM vidrios v WHERE v.pieza_codigo = p.codigo AND v.estado = 'instalado') AS vidrios_instalados,
    (SELECT COUNT(*) FROM instalaciones i WHERE i.pieza_codigo = p.codigo AND i.estado = 'instalado') AS instalaciones_ok,
    (SELECT COUNT(*) FROM instalaciones i WHERE i.pieza_codigo = p.codigo AND i.estado = 'incidencia') AS incidencias
FROM piezas p
JOIN catalogo_sistemas s ON p.sistema_id = s.sistema_id;

-- Vista: dashboard global (puente para /api/dashboard)
CREATE VIEW IF NOT EXISTS vista_dashboard AS
SELECT
    (SELECT COUNT(*) FROM piezas) AS total_piezas,
    (SELECT COUNT(*) FROM piezas WHERE estado = 'pendiente') AS pendientes,
    (SELECT COUNT(*) FROM piezas WHERE estado = 'en_corte') AS en_corte,
    (SELECT COUNT(*) FROM piezas WHERE estado = 'armado') AS armados,
    (SELECT COUNT(*) FROM piezas WHERE estado = 'instalado') AS instalados,
    (SELECT COUNT(*) FROM cortes WHERE estado = 'cortado') AS total_cortes_cortados
FROM (SELECT 1);
