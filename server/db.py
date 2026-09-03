"""
Taller-ventanería — capa de base de datos SQLite
Puerto: /api/v1/*
"""

import json
import os
import sqlite3
import datetime
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'taller.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def get_db() -> sqlite3.Connection:
    """Regresa conexión a la DB. Crea directorio si falta."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db() -> None:
    """Crea tablas si no existen; ejecuta schema.sql."""
    if os.path.exists(DB_PATH):
        # Ya existe: verificar tablas clave
        conn = get_db()
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        conn.close()
        faltantes = [
            'catalogo_sistemas', 'catalogo_materiales',
            'proyecto_torres', 'proyecto_niveles',
            'piezas', 'cortes', 'vidrios', 'insumos',
            'instalaciones', 'movimientos'
        ]
        existentes = set(tables)
        para_crear = [t for t in faltantes if t not in existentes]
        if para_crear:
            _crear_tablas(para_crear)
        return

    _crear_tablas([
        'catalogo_sistemas', 'catalogo_materiales',
        'proyecto_torres', 'proyecto_niveles',
        'piezas', 'cortes', 'vidrios', 'insumos',
        'instalaciones', 'movimientos'
    ])

    _poblar_catálogo_sistemas()
    _poblar_catálogo_materiales()
    _poblar_proyecto()


def _crear_tablas(tablas: List[str]) -> None:
    conn = get_db()
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()


def _poblar_catálogo_sistemas() -> None:
    """Carga sistemas desde proyecto_ventanas_normalizado.json"""
    try:
        data_path = os.path.join(BASE_DIR, '..', '.hermes', 'desktop-attachments',
                                  'proyecto_ventanas_normalizado.json')
        if not os.path.exists(data_path):
            data_path = os.path.join(BASE_DIR, '..', 'data', 'proyecto_ventanas_normalizado.json')
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        # No hay JSON: insertar de memória mínimo viable
        sistemas = {
            'corrediza_3':     {'nombre': 'Corrediza de 3\"',         'descripcion': 'Ventana corrediza con panel fijo y corredizo'},
            'puerta_abitable': {'nombre': 'Puerta abatible',          'descripcion': 'Puerta corredora tipo abatible'},
            'ventanal_4_hojas':{'nombre': 'Ventanal 4 hojas',         'descripcion': 'Ventanal con 4 hojas configurables'},
            'celosias_fijas':  {'nombre': 'Celosías fijas',           'descripcion': 'Celosía fija de aluminio'},
            'sifon_eco':       {'nombre': 'Sifón Eco',                'descripcion': 'Marco de sifón con dos vidrios traslapados'},
            'fijo_inferior_ventana_cruz': {'nombre': 'Fijo inferior (ventana cruz)', 'descripcion': 'Panel fijo inferior con mullidoras'},
        }
        for sid, meta in sistemas.items():
            meta['formulas'] = {}
        data = {'sistemas_formulas': sistemas}

    sistemas = data.get('sistemas_formulas', {})
    for sid in sistemas:
        sistemas[sid].setdefault('formulas', {})

    conn = get_db()
    for sid, meta in sistemas.items():
        conn.execute(
            "INSERT OR IGNORE INTO catalogo_sistemas (sistema_id, nombre, descripcion, formulas_json, activo) VALUES (?,?,?,?,1)",
            (sid, meta.get('nombre', sid), meta.get('descripcion', ''), json.dumps(meta))
        )
    conn.commit()
    conn.close()


def _poblar_catálogo_materiales() -> None:
    """Carga materiales desde proyecto_ventanas_normalizado.json"""
    try:
        data_path = os.path.join(BASE_DIR, '..', '.hermes', 'desktop-attachments',
                                  'proyecto_ventanas_normalizado.json')
        if not os.path.exists(data_path):
            data_path = os.path.join(BASE_DIR, '..', 'data', 'proyecto_ventanas_normalizado.json')
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        # Catalogo mínimo
        conn = get_db()
        conn.executemany(
            "INSERT OR IGNORE INTO catalogo_materiales (material_id, nombre, unidad, precio_unitario, observaciones) VALUES (?,?,?,?,?)",
            [
                (1,  'Perfil Jamba 3"', 'mm', None,  'Perfil vertical superior'),
                (2,  'Perfil Riel 3"',  'mm', None,  'Perfil horizontal inferior'),
                (3,  'Chapa perfil ancho manija manija CHAPADURO', 'mm', None, 'Para cercos y traslapes'),
                (4,  'Chapa perfil estrecho manija manija CHAPAFINO', 'mm', None, 'Para traslapes'),
                (5,  'Zoclo doble vena',    'mm', None,  'Zoclo de hoja inferior'),
                (6,  'Cabezal de hoja',     'mm', None,  'Cabezal de hoja superior'),
                (21, 'Carretillas tandem de 3"', 'pieza', None, 'Tandem por peso (V-01)'),
                (22, 'Jaladera de embutir tipo Alfa', 'pieza', None, '1 por ventana'),
                (23, 'Contra jaladera tipo Herralum', 'pieza', None, '1 por ventana'),
                (26, 'Felpa',               'metro_lineal', None,  'Para sellado'),
                (27, 'Empaque vinil #11 peine', 'metro_lineal', None, 'Para vidrio de 6mm'),
                (30, 'Pija cabeza bola 10 x 3/4"', 'pieza', None, 'Para ensamble'),
                (31, 'Pija larga 10 x 3"', 'pieza', None, 'Para anclaje'),
                (34, 'Bisagra de libro',   'pieza', None,  '4 por puerta abatible'),
                (35, 'Chapa para perfil angosto manija manija', 'pieza', None, 'Chapa manija'),
                (36, 'Manija',             'pieza', None,  '1 por puerta abatible'),
            ]
        )
        conn.commit()
        conn.close()
        return

    insumos_materiales = {
        1:  ('Perfil Jamba 3"',         'mm',            None,  'Perfil vertical superior'),
        2:  ('Perfil Riel 3"',          'mm',            None,  'Perfil horizontal inferior'),
        3:  ('Chapa perfil ancho manija manija CHAPADURO', 'mm', None, 'Para cercos y traslapes'),
        4:  ('Chapa perfil estrecho manija manija CHAPAFINO', 'mm', None, 'Para traslapes'),
        5:  ('Zoclo doble vena',        'mm',            None,  'Zoclo de hoja inferior'),
        6:  ('Cabezal de hoja',         'mm',            None,  'Cabezal de hoja superior'),
        21: ('Carretillas tandem de 3"', 'pieza',        None,  'Tandem por peso (V-01)'),
        22: ('Jaladera de embutir tipo Alfa', 'pieza',   None,  '1 por ventana'),
        23: ('Contra jaladera tipo Herralum', 'pieza',   None,  '1 por ventana'),
        26: ('Felpa',                   'metro_lineal',  None,  'Para sellado'),
        27: ('Empaque vinil #11 peine', 'metro_lineal',  None,  'Para vidrio de 6mm'),
        30: ('Pija cabeza bola 10 x 3/4"', 'pieza',      None,  'Para ensamble'),
        31: ('Pija larga 10 x 3"',     'pieza',          None,  'Para anclaje'),
        34: ('Bisagra de libro',        'pieza',          None,  '4 por puerta abatible'),
        35: ('Chapa para perfil angosto manija manija', 'pieza', None,  'Chapa manija'),
        36: ('Manija',                  'pieza',          None,  '1 por puerta abatible'),
    }
    conn = get_db()
    for mid, (nombre, unidad, precio, obs) in insumos_materiales.items():
        conn.execute(
            "INSERT OR IGNORE INTO catalogo_materiales (material_id, nombre, unidad, precio_unitario, observaciones) VALUES (?,?,?,?,?)",
            (mid, nombre, unidad, precio, obs)
        )
    conn.commit()
    conn.close()


def _poblar_proyecto() -> None:
    """Crea las 15 piezas del proyecto MONTERRA desde PROYECTO en taller.html si existe;
    si no, usa datos mínimos."""
    import re
    html_path = os.path.join(BASE_DIR, '..', 'frontend', 'taller.html')
    piezas_data = None
    if os.path.exists(html_path):
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
        m = re.search(r'const\s+PROYECTO\s*=\s*\{[\s\S]*?\}\s*;', html)
        if m:
            try:
                bloque_js = m.group(0)
                data = js_to_json(bloque_js)
                piezas_data = data.get('piezas', [])
            except Exception:
                piezas_data = None

    if piezas_data is None:
        # Fallback mínimo
        piezas_data = [
            {'codigo':'V-01','nombre':'Sala PB','sistema':'corrediza_3','ancho':1990,'alto':2400,'torre':'T-01','nivel':'PB','depto':'DEP1','recinto':'Sala'},
            {'codigo':'V-02','nombre':'Comedor N1','sistema':'corrediza_3','ancho':1230,'alto':1600,'torre':'T-01','nivel':'N1','depto':'DEP1','recinto':'Comedor'},
            {'codigo':'V-03','nombre':'Balcón','sistema':'corrediza_3','ancho':1230,'alto':2400,'torre':'T-01','nivel':'N2','depto':'DEP1','recinto':'Balcón'},
            {'codigo':'V-04','nombre':'Lavandería','sistema':'celosias_fijas','ancho':740,'alto':400,'torre':'T-01','nivel':'PB','depto':'DEP1','recinto':'Lavandería'},
            {'codigo':'V-05','nombre':'Sala N1','sistema':'corrediza_3','ancho':1990,'alto':1600,'torre':'T-01','nivel':'N1','depto':'DEP2','recinto':'Sala'},
            {'codigo':'V-06','nombre':'Salas N2-N4','sistema':'corrediza_3','ancho':1990,'alto':1200,'alto_total':2400,'torre':'T-01','nivel':'N2','depto':'DEP2','recinto':'Sala'},
            {'codigo':'V-07','nombre':'Baño','sistema':'sifon_eco','ancho':430,'alto':330,'alto_total':330,'torre':'T-01','nivel':'PB','depto':'DEP1','recinto':'Baño'},
            {'codigo':'V-08','nombre':'Recámara 1','sistema':'corrediza_3','ancho':990,'alto':1200,'alto_total':2400,'torre':'T-01','nivel':'N3','depto':'DEP1','recinto':'Recámara 1'},
            {'codigo':'V-09','nombre':'Recámara 2','sistema':'corrediza_3','ancho':990,'alto':1200,'alto_total':2400,'torre':'T-01','nivel':'N3','depto':'DEP2','recinto':'Recámara 2'},
            {'codigo':'P-01','nombre':'Puerta Rec1 (chapa der.)','sistema':'puerta_abitable','ancho':990,'alto':2400,'torre':'T-01','nivel':'PB','depto':'DEP1','recinto':'Recámara 1'},
            {'codigo':'P-02','nombre':'Puerta Rec2 (chapa izq.)','sistema':'puerta_abitable','ancho':990,'alto':2400,'torre':'T-01','nivel':'PB','depto':'DEP2','recinto':'Recámara 2'},
            {'codigo':'V-10','nombre':'Sala PB T2','sistema':'corrediza_3','ancho':1990,'alto':2400,'torre':'T-02','nivel':'PB','depto':'DEP1','recinto':'Sala'},
            {'codigo':'V-11','nombre':'Comedor T2','sistema':'corrediza_3','ancho':1230,'alto':1600,'torre':'T-02','nivel':'N1','depto':'DEP1','recinto':'Comedor'},
            {'codigo':'V-12','nombre':'Sala PB T3','sistema':'corrediza_3','ancho':1990,'alto':2400,'torre':'T-03','nivel':'PB','depto':'DEP1','recinto':'Sala'},
            {'codigo':'V-13','nombre':'Comedor T3','sistema':'corrediza_3','ancho':1230,'alto':1600,'torre':'T-03','nivel':'N1','depto':'DEP1','recinto':'Comedor'},
        ]

    conn = get_db()
    # Torres
    for p in piezas_data:
        conn.execute(
            "INSERT OR IGNORE INTO proyecto_torres (torre_codigo, nombre) VALUES (?,?)",
            (p['torre'], f"Torre {p['torre'][2:]}"))

    # Niveles (machacamos para estar seguros)
    conn.execute("DELETE FROM proyecto_niveles")
    for p in piezas_data:
        conn.execute(
            "INSERT OR IGNORE INTO proyecto_niveles (torre_codigo, nivel_codigo) VALUES (?,?)",
            (p['torre'], p['nivel']))

    # Piezas
    for p in piezas_data:
        conn.execute(
            """INSERT OR IGNORE INTO piezas
               (codigo, nombre, sistema_id, torre, nivel, depto, recinto,
                ancho_mm, alto_mm, alto_total_mm, estado, observaciones)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p['codigo'], p.get('nombre', p['codigo']),
             p['sistema'], p.get('torre'), p.get('nivel'),
             p.get('depto'), p.get('recinto'),
             p['ancho'], p['alto'], p.get('alto_total'),
             'pendiente', '')
        )
    conn.commit()
    conn.close()


def js_to_json(js_code: str) -> dict:
    """Convierte un objeto JavaScript (con claves sin comillas, comentarios, etc.)
    a un diccionario Python parseable como JSON."""
    import re

    # Eliminar comentarios JS (// y /* */)
    js_code = re.sub(r'//.*$', '', js_code, flags=re.MULTILINE)
    js_code = re.sub(r'/\*[\s\S]*?\*/', '', js_code)

    # Extraer solo el cuerpo del objeto (sin "const PROYECTO = " y sin ";")
    m = re.search(r'({[\s\S]*})\s*;?\s*$', js_code.strip())
    if not m:
        raise ValueError("No se pudo extraer el objeto JS")
    cuerpo = m.group(1)

    # Convertir claves sin comillas a claves con comillas dobles
    # patrón: identificador seguido de : -> "identificador":
    cuerpo = re.sub(r'(?<=[{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', cuerpo)

    # Manejar casos como "nombre: "Torre 1"" que podrían haber quedado mal
    # Las cadenas ya tienen comillas dobles, los números no

    # Ahora parsear como JSON
    data = json.loads(cuerpo)
    return data
# ============================================================
# Consultas de estado
# ============================================================

def get_proyecto() -> Dict[str, Any]:
    conn = get_db()
    torres = conn.execute("SELECT * FROM proyecto_torres").fetchall()
    niveles_rows = conn.execute("SELECT * FROM proyecto_niveles").fetchall()
    piezas_rows = conn.execute("SELECT * FROM piezas").fetchall()
    conn.close()

    torres_out = [dict(t) for t in torres]
    niveles_out = {}
    for n in niveles_rows:
        t = n['torre_codigo']
        niveles_out.setdefault(t, []).append(n['nivel_codigo'])

    piezas_out = []
    for p in piezas_rows:
        d: Dict[str, Any] = dict(p)
        d['niveles_disponibles'] = niveles_out.get(p['torre'], [])
        piezas_out.append(d)

    return {
        'nombre': 'MONTERRA',
        'torres': torres_out,
        'niveles_por_torre': niveles_out,
        'piezas': piezas_out
    }


def get_dashboard() -> Dict[str, Any]:
    conn = get_db()
    total_piezas = conn.execute("SELECT COUNT(*) FROM piezas").fetchone()[0]

    por_estado = conn.execute(
        "SELECT estado, COUNT(*) FROM piezas GROUP BY estado"
    ).fetchall()
    por_estado_d = {r['estado']: r[1] for r in por_estado}

    # Por torre
    rows_torre = conn.execute("""
        SELECT torre,
               COUNT(*) as total,
               SUM(CASE WHEN estado='instalado' THEN 1 ELSE 0 END) as instalado,
               SUM(CASE WHEN estado='pendiente' THEN 1 ELSE 0 END) as pendiente,
               SUM(CASE WHEN estado='en_corte' THEN 1 ELSE 0 END) as en_corte,
               SUM(CASE WHEN estado='armado' THEN 1 ELSE 0 END) as armado
        FROM piezas
        GROUP BY torre
        ORDER BY torre
    """).fetchall()

    por_torre_d = {}
    for r in rows_torre:
        d = dict(r)
        del d['total']  # ya está en la estructura que devolvemos
        por_torre_d[r['torre']] = {
            'total': r['total'],
            'instalado': r['instalado'],
            'pendiente': r['pendiente'],
            'en_corte': r['en_corte'],
            'armado': r['armado'],
        }

    conn.close()
    return {
        'proyecto': 'MONTERRA',
        'total_piezas': total_piezas,
        'por_estado': {
            'pendiente': por_estado_d.get('pendiente', 0),
            'en_corte': por_estado_d.get('en_corte', 0),
            'armado': por_estado_d.get('armado', 0),
            'instalado': por_estado_d.get('instalado', 0),
        },
        'por_torre': por_torre_d,
    }


def get_pieza(codigo: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    p = conn.execute("SELECT * FROM piezas WHERE codigo=?", (codigo,)).fetchone()
    if p is None:
        conn.close()
        return None

    cortes_rows = conn.execute(
        "SELECT * FROM cortes WHERE pieza_codigo=? ORDER BY id", (codigo,)
    ).fetchall()
    cortes = [dict(c) for c in cortes_rows]

    vidrios_rows = conn.execute(
        "SELECT * FROM vidrios WHERE pieza_codigo=? ORDER BY id", (codigo,)
    ).fetchall()
    vidrios = [dict(v) for v in vidrios_rows]

    insumos_rows = conn.execute(
        "SELECT * FROM insumos WHERE pieza_codigo=? ORDER BY id", (codigo,)
    ).fetchall()
    insumos = [dict(i) for i in insumos_rows]

    conn.close()
    return {
        'codigo': p['codigo'],
        'nombre': p['nombre'],
        'sistema_id': p['sistema_id'],
        'torre': p['torre'],
        'nivel': p['nivel'],
        'depto': p['depto'],
        'recinto': p['recinto'],
        'ancho_mm': p['ancho_mm'],
        'alto_mm': p['alto_mm'],
        'alto_total_mm': p['alto_total_mm'],
        'estado': p['estado'],
        'observaciones': p['observaciones'],
        'cortes': cortes,
        'vidrios': vidrios,
        'insumos': insumos,
    }


def marcar_corte_cortado(pieza_codigo: str, corte_id: int) -> bool:
    conn = get_db()
    r = conn.execute(
        "UPDATE cortes SET estado='cortado' WHERE id=? AND pieza_codigo=? AND estado='pendiente'",
        (corte_id, pieza_codigo)
    )
    if r.rowcount:
        conn.execute(
            "INSERT INTO movimientos (fecha, tipo, pieza_codigo, detalle) VALUES (?,?,?,?)",
            (datetime.date.today().isoformat(),
             'corte_cortado',
             pieza_codigo,
             json.dumps({'corte_id': corte_id}))
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def registrar_instalacion(
    pieza_codigo: str,
    operador: str,
    ubicacion_instalacion: Optional[str],
    observaciones: Optional[str]
) -> int:
    conn = get_db()
    r = conn.execute(
        """INSERT INTO instalaciones
           (pieza_codigo, operador, ubicacion_instalacion, fecha_instalacion, observaciones, estado)
           VALUES (?,?,?,?,?, 'instalado')""",
        (pieza_codigo, operador, ubicacion_instalacion, datetime.date.today().isoformat(), observaciones)
    )
    iid = r.lastrowid
    conn.execute(
        "UPDATE piezas SET estado='instalado' WHERE codigo=? AND estado!='instalado'",
        (pieza_codigo,)
    )
    conn.execute(
        "INSERT INTO movimientos (fecha, tipo, pieza_codigo, detalle) VALUES (?,?,?,?)",
        (datetime.date.today().isoformat(),
         'instalacion',
         pieza_codigo,
         json.dumps({'instalacion_id': iid, 'operador': operador}))
    )
    conn.commit()
    conn.close()
    return iid


def calcular_y_guardar_pieza(pieza_codigo: str) -> Optional[Dict[str, Any]]:
    """Ejecuta el cálculo y persiste cortes/vidrios/insumos en DB"""
    import calculos
    p = get_pieza(pieza_codigo)
    if p is None:
        return None

    from calculos import calcular_sistema
    resultado = calcular_sistema(
        p['sistema_id'],
        p['ancho_mm'],
        p['alto_mm'],
        alto_total=p.get('alto_total_mm')
    )

    if 'error' in resultado:
        return None

    conn = get_db()
    # Limpiar datos anteriores
    conn.execute("DELETE FROM cortes WHERE pieza_codigo=?", (pieza_codigo,))
    conn.execute("DELETE FROM vidrios WHERE pieza_codigo=?", (pieza_codigo,))
    conn.execute("DELETE FROM insumos WHERE pieza_codigo=?", (pieza_codigo,))

    for c in resultado.get('componentes', []):
        conn.execute(
            """INSERT INTO cortes (pieza_codigo, material_id, pieza_nombre, longitud_mm, cantidad, observaciones, estado)
               VALUES (?,?,?,?,?,?, 'pendiente')""",
            (pieza_codigo, c.get('material_id'), c.get('pieza'), c.get('longitud_mm'), c.get('cantidad'), c.get('observaciones'))
        )

    for v in resultado.get('vidrios', []):
        conn.execute(
            """INSERT INTO vidrios (pieza_codigo, posicion, ancho_mm, alto_mm, cantidad, espesor_mm, estado)
               VALUES (?,?,?,?,?, NULL, 'pendiente')""",
            (pieza_codigo, v.get('posicion'), v.get('ancho_mm'), v.get('alto_mm'), v.get('cantidad'))
        )

    for ins in resultado.get('insumos', []):
        conn.execute(
            """INSERT INTO insumos (pieza_codigo, material_id, nombre, cantidad, unidad, tipo)
               VALUES (?,?,?,?,?, 'fijo')""",
            (pieza_codigo, ins.get('material_id'), ins.get('nombre'), ins.get('cantidad'), ins.get('unidad'))
        )

    conn.commit()
    conn.close()
    return get_pieza(pieza_codigo)
