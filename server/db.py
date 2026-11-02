"""
Taller-ventanería — Capa de Acceso a Datos (DAL)
Responsabilidad: Consultas SQL puras y gestión de conexión.
"""

import json
import os
import sqlite3
import datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'taller.db'))
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def get_db() -> sqlite3.Connection:
    """Regresa conexión a la DB con optimizaciones para concurrencia."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db() -> None:
    """Crea tablas, índices y puebla datos iniciales."""
    conn = get_db()
    
    # 1. Crear tablas desde schema.sql
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        conn.executescript(f.read())
    
    # 2. Blindar con Índices para rendimiento
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_cortes_pieza ON cortes(pieza_codigo)",
        "CREATE INDEX IF NOT EXISTS idx_vidrios_pieza ON vidrios(pieza_codigo)",
        "CREATE INDEX IF NOT EXISTS idx_insumos_pieza ON insumos(pieza_codigo)",
        "CREATE INDEX IF NOT EXISTS idx_instalaciones_pieza ON instalaciones(pieza_codigo)",
        "CREATE INDEX IF NOT EXISTS idx_movimientos_pieza ON movimientos(pieza_codigo)"
    ]
    for idx in indices:
        conn.execute(idx)
    
    conn.commit()
    conn.close()

# --- Consultas Simples (Read) ---

def fetch_all(query: str, params: tuple = ()) -> List[Dict]:
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_one(query: str, params: tuple = ()) -> Optional[Dict]:
    conn = get_db()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return dict(row) if row else None

# --- Operaciones de Escritura (Write) ---

def execute_transaction(queries: List[tuple]) -> bool:
    """Ejecuta múltiples queries en una sola transacción atómica."""
    conn = get_db()
    try:
        for query, params in queries:
            conn.execute(query, params)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def insert_log(tipo: str, pieza_codigo: str, detalle: Dict):
    """Registra un movimiento en la bitácora."""
    conn = get_db()
    conn.execute(
        "INSERT INTO movimientos (fecha, tipo, pieza_codigo, detalle) VALUES (?,?,?,?)",
        (datetime.date.today().isoformat(), tipo, pieza_codigo, json.dumps(detalle))
    )
    conn.commit()
    conn.close()

# --- Levantamientos (Obra → Taller) ---

def crear_levantamiento(data: Dict) -> int:
    """Inserta un nuevo levantamiento capturado en obra. Regresa el ID generado."""
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO levantamientos 
           (fecha, torre, nivel, depto, lado, operador, piezas_json, notas_generales)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            datetime.datetime.now().isoformat(timespec='seconds'),
            data['torre'], data['nivel'], data['depto'], data.get('lado'),
            data['operador'], json.dumps(data.get('piezas', {})),
            data.get('notas_generales')
        )
    )
    conn.commit()
    lid = cur.lastrowid or 0
    conn.close()
    return lid

def listar_levantamientos(solo_nuevos: bool = False) -> List[Dict]:
    """Lista los levantamientos, opcionalmente solo los nuevos (no procesados)."""
    conn = get_db()
    if solo_nuevos:
        rows = conn.execute(
            "SELECT * FROM levantamientos WHERE estado = 'nuevo' ORDER BY fecha DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM levantamientos ORDER BY fecha DESC"
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        # Parseamos el JSON de piezas para que el frontend lo reciba listo
        try:
            d['piezas'] = json.loads(d.pop('piezas_json'))
        except Exception:
            d['piezas'] = {}
        result.append(d)
    return result

def marcar_levantamiento_recibido(lid: int) -> bool:
    """Cambia el estado de un levantamiento a 'recibido' (procesado por el taller)."""
    conn = get_db()
    conn.execute(
        "UPDATE levantamientos SET estado = 'recibido' WHERE id = ?", (lid,)
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0

def contar_levantamientos_nuevos() -> int:
    """Cuenta cuántos levantamientos esperan ser procesados por el taller."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM levantamientos WHERE estado = 'nuevo'"
    ).fetchone()
    conn.close()
    return row['c'] if row else 0
