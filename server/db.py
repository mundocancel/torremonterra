import sqlite3
import os
from datetime import datetime
from typing import Optional


DB_PATH: str = "data/taller.db"


def get_db() -> sqlite3.Connection:
    """Return a database connection with WAL mode and foreign keys enabled."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the database from schema.sql and sync inventory snapshot."""
    conn = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()

    conn.executescript(schema)
    conn.commit()
    conn.close()

    _sync_inventory_snapshot()


def _sync_inventory_snapshot() -> None:
    """Populate inventory_snapshot from monterra.json if empty."""
    conn = get_db()

    cur = conn.execute("SELECT COUNT(*) FROM inventory_snapshot")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    import json

    monterra_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monterra.json")
    with open(monterra_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inventario = data.get("inventario", {})

    for material_id, info in inventario.items():
        conn.execute(
            """
            INSERT INTO inventory_snapshot (material_id, cantidad_disponible, cantidad_minima,
                                            unidad_medida, proveedor_principal, costo_unitario)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                material_id,
                info.get("cantidad_disponible", 0),
                info.get("cantidad_minima", 0),
                info.get("unidad_medida", ""),
                info.get("proveedor_principal", ""),
                info.get("costo_unitario", 0),
            ),
        )

    conn.commit()
    conn.close()


def get_inventory_snapshot(material_id: str):
    """Return the current snapshot for a material, or None."""
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM inventory_snapshot WHERE material_id = ?", (material_id,)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_inventory_snapshot(material_id: str, cantidad_disponible: float) -> None:
    """Update the available quantity for a material."""
    conn = get_db()
    conn.execute(
        """
        UPDATE inventory_snapshot
        SET cantidad_disponible = ?, fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE material_id = ?
        """,
        (cantidad_disponible, material_id),
    )
    conn.commit()
    conn.close()


def add_inventory_movement(
    material_id: str,
    tipo_movimiento: str,
    cantidad: float,
    motivo: Optional[str] = None,
    usuario_id: Optional[str] = None,
    ref_instalacion_id: Optional[str] = None,
) -> str:
    """Record an inventory movement and update the snapshot."""
    import uuid

    mov_id = str(uuid.uuid4())
    conn = get_db()

    conn.execute(
        """
        INSERT INTO inventory_movements (id, material_id, tipo_movimiento, cantidad,
                                        motivo, usuario_id, ref_instalacion_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (mov_id, material_id, tipo_movimiento, cantidad, motivo, usuario_id, ref_instalacion_id),
    )

    if tipo_movimiento == "entrada":
        conn.execute(
            """
            UPDATE inventory_snapshot SET cantidad_disponible = cantidad_disponible + ?
            WHERE material_id = ?
            """,
            (cantidad, material_id),
        )
    elif tipo_movimiento == "salida":
        conn.execute(
            """
            UPDATE inventory_snapshot SET cantidad_disponible = cantidad_disponible - ?
            WHERE material_id = ?
            """,
            (cantidad, material_id),
        )
    elif tipo_movimiento == "ajuste":
        conn.execute(
            """
            UPDATE inventory_snapshot SET cantidad_disponible = ?
            WHERE material_id = ?
            """,
            (cantidad, material_id),
        )

    conn.commit()
    conn.close()
    return mov_id


# ---------------------------------------------------------------------------
# FIX 1: add_piece_installation ahora acepta y persiste los 4 campos de fecha
# ---------------------------------------------------------------------------

def add_piece_installation(
    codigo_plano: str,
    pieza_catalogo_id: str,
    departamento_id: str,
    torre_codigo: str,
    nivel_nombre: str,
    estado: str = "pendiente",
    usuario_asignado: str = None,
    observaciones: str = None,
    fecha_inicio_fabricacion: str = None,
    fecha_fin_fabricacion: str = None,
    fecha_inicio_instalacion: str = None,
    fecha_fin_instalacion: str = None,
) -> str:
    """Register a piece installation/fabrication record."""
    import uuid

    piece_id = str(uuid.uuid4())
    conn = get_db()

    conn.execute(
        """
        INSERT INTO piece_installations (
            id, codigo_plano, pieza_catalogo_id, departamento_id,
            torre_codigo, nivel_nombre, estado, usuario_asignado, observaciones,
            fecha_inicio_fabricacion, fecha_fin_fabricacion,
            fecha_inicio_instalacion, fecha_fin_instalacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            piece_id,
            codigo_plano,
            pieza_catalogo_id,
            departamento_id,
            torre_codigo,
            nivel_nombre,
            estado,
            usuario_asignado,
            observaciones,
            fecha_inicio_fabricacion,
            fecha_fin_fabricacion,
            fecha_inicio_instalacion,
            fecha_fin_instalacion,
        ),
    )
    conn.commit()
    conn.close()
    return piece_id


def get_piece_installations(torre_codigo=None, nivel_nombre=None, estado=None):
    """List piece installations with optional filters."""
    conn = get_db()

    query = "SELECT * FROM piece_installations WHERE 1=1"
    params = []

    if torre_codigo:
        query += " AND torre_codigo = ?"
        params.append(torre_codigo)
    if nivel_nombre:
        query += " AND nivel_nombre = ?"
        params.append(nivel_nombre)
    if estado:
        query += " AND estado = ?"
        params.append(estado)

    query += " ORDER BY created_at DESC"

    cur = conn.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_piece_installation(piece_id: str):
    """Return a piece installation by ID, or None."""
    conn = get_db()
    cur = conn.execute("SELECT * FROM piece_installations WHERE id = ?", (piece_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# FIX 2: update_piece_installation — piece_id SIEMPRE al final de params
# ---------------------------------------------------------------------------

def update_piece_installation(
    piece_id: str,
    estado: str = None,
    usuario_asignado: str = None,
    observaciones: str = None,
    fecha_fin_fabricacion: datetime = None,
    fecha_fin_instalacion: datetime = None,
) -> bool:
    """Update a piece installation record."""
    conn = get_db()

    updates = []
    params = []

    if estado:
        updates.append("estado = ?")
        params.append(estado)
    if usuario_asignado:
        updates.append("usuario_asignado = ?")
        params.append(usuario_asignado)
    if observaciones is not None:
        updates.append("observaciones = ?")
        params.append(observaciones)
    if fecha_fin_fabricacion:
        updates.append("fecha_fin_fabricacion = ?")
        params.append(fecha_fin_fabricacion.isoformat())
    if fecha_fin_instalacion:
        updates.append("fecha_fin_instalacion = ?")
        params.append(fecha_fin_instalacion.isoformat())

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(piece_id)  # <-- SIEMPRE el último, fuera del if de campos
        conn.execute(
            f"""
            UPDATE piece_installations SET {', '.join(updates)}
            WHERE id = ?
            """,
            params,
        )
        conn.commit()

    conn.close()
    return True


# ---------------------------------------------------------------------------
# Production tasks
# ---------------------------------------------------------------------------

def add_production_task(
    tipo: str,
    titulo: str,
    descripcion: str = None,
    prioridad: int = 1,
    usuario_asignado: str = None,
    pieza_instalacion_id: str = None,
    tiempo_estimado_minutos: int = None,
) -> str:
    """Create a production task."""
    import uuid

    task_id = str(uuid.uuid4())
    conn = get_db()

    conn.execute(
        """
        INSERT INTO production_tasks (id, tipo, titulo, descripcion, prioridad,
                                      usuario_asignado, pieza_instalacion_id, tiempo_estimado_minutos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            tipo,
            titulo,
            descripcion,
            prioridad,
            usuario_asignado,
            pieza_instalacion_id,
            tiempo_estimado_minutos,
        ),
    )
    conn.commit()
    conn.close()
    return task_id


def get_production_tasks(usuario_asignado=None, estado=None):
    """List production tasks with optional filters."""
    conn = get_db()

    query = "SELECT * FROM production_tasks WHERE 1=1"
    params = []

    if usuario_asignado:
        query += " AND usuario_asignado = ?"
        params.append(usuario_asignado)
    if estado:
        query += " AND estado = ?"
        params.append(estado)

    query += " ORDER BY prioridad DESC, fecha_asignacion ASC"

    cur = conn.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_production_task(task_id: str):
    """Return a production task by ID, or None."""
    conn = get_db()
    cur = conn.execute("SELECT * FROM production_tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# FIX 3: update_production_task — task_id SIEMPRE al final de params
# ---------------------------------------------------------------------------

def update_production_task(
    task_id: str,
    estado: str = None,
    fecha_completado: datetime = None,
    tiempo_real_minutos: int = None,
) -> bool:
    """Update a production task record."""
    conn = get_db()

    updates = []
    params = []

    if estado:
        updates.append("estado = ?")
        params.append(estado)
    if fecha_completado:
        updates.append("fecha_completado = ?")
        params.append(fecha_completado.isoformat())
    if tiempo_real_minutos is not None:
        updates.append("tiempo_real_minutos = ?")
        params.append(tiempo_real_minutos)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)  # <-- SIEMPRE el último, fuera del if de campos
        conn.execute(
            f"""
            UPDATE production_tasks SET {', '.join(updates)}
            WHERE id = ?
            """,
            params,
        )
        conn.commit()

    conn.close()
    return True


def get_inventory_movements(material_id=None, limite: int = 100):
    """List inventory movements with optional material filter."""
    conn = get_db()

    query = "SELECT * FROM inventory_movements WHERE 1=1"
    params = []

    if material_id:
        query += " AND material_id = ?"
        params.append(material_id)

    query += " ORDER BY fecha DESC LIMIT ?"
    params.append(limite)

    cur = conn.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
