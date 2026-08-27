-- Schema de base de datos para taller-ventaneria
-- SQLite

-- Tabla: piece_installations (piezas instaladas/fabricadas)
CREATE TABLE IF NOT EXISTS piece_installations (
    id TEXT PRIMARY KEY,
    codigo_plano TEXT NOT NULL,
    pieza_catalogo_id TEXT NOT NULL,
    departamento_id TEXT NOT NULL,
    torre_codigo TEXT NOT NULL,
    nivel_nombre TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    fecha_inicio_fabricacion DATETIME,
    fecha_fin_fabricacion DATETIME,
    fecha_inicio_instalacion DATETIME,
    fecha_fin_instalacion DATETIME,
    usuario_asignado TEXT,
    observaciones TEXT,
    tiempo_real_horas REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: inventory_movements (movimientos de inventario)
CREATE TABLE IF NOT EXISTS inventory_movements (
    id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('entrada', 'salida', 'ajuste')),
    cantidad REAL NOT NULL,
    motivo TEXT,
    usuario_id TEXT,
    ref_instalacion_id TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: inventory_snapshot (snapshot actualizable del inventario)
CREATE TABLE IF NOT EXISTS inventory_snapshot (
    material_id TEXT PRIMARY KEY,
    cantidad_disponible REAL NOT NULL DEFAULT 0,
    cantidad_minima REAL NOT NULL DEFAULT 0,
    unidad_medida TEXT NOT NULL,
    proveedor_principal TEXT,
    costo_unitario REAL,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: production_tasks (tareas de producción)
CREATE TABLE IF NOT EXISTS production_tasks (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL CHECK(tipo IN ('fabricacion', 'instalacion', 'revision', 'mantenimiento')),
    titulo TEXT NOT NULL,
    descripcion TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'en_progreso', 'completada', 'cancelada')),
    prioridad INTEGER NOT NULL DEFAULT 1 CHECK(prioridad BETWEEN 1 AND 5),
    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATETIME,
    fecha_completado DATETIME,
    usuario_asignado TEXT NOT NULL,
    pieza_instalacion_id TEXT,
    tiempo_estimado_minutos INTEGER,
    tiempo_real_minutos INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_pieces_torre ON piece_installations(torre_codigo, nivel_nombre);
CREATE INDEX IF NOT EXISTS idx_pieces_estado ON piece_installations(estado);
CREATE INDEX IF NOT EXISTS idx_movements_material ON inventory_movements(material_id, fecha);
CREATE INDEX IF NOT EXISTS idx_tasks_usuario ON production_tasks(usuario_asignado, estado);
CREATE INDEX IF NOT EXISTS idx_tasks_pieza ON production_tasks(pieza_instalacion_id);
