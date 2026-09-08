"""
Taller-ventanería — Capa de Servicios (Business Logic)
Responsabilidad: Orquestar la lógica de negocio y validar reglas.
"""

import json
from typing import Any, Dict, List, Optional
from .db import (
    fetch_all, fetch_one, execute_transaction, insert_log, init_db,
    crear_levantamiento, listar_levantamientos, marcar_levantamiento_recibido,
    contar_levantamientos_nuevos
)

def initialize_system():
    """Inicia la DB y asegura que los datos básicos estén presentes."""
    init_db()

def get_full_project() -> Dict[str, Any]:
    """Recupera la estructura completa del proyecto."""
    torres = fetch_all("SELECT * FROM proyecto_torres")
    niveles_rows = fetch_all("SELECT * FROM proyecto_niveles")
    piezas = fetch_all("SELECT * FROM piezas")
    
    niveles_out = {}
    for n in niveles_rows:
        t = n['torre_codigo']
        niveles_out.setdefault(t, []).append(n['nivel_codigo'])
        
    return {
        'nombre': 'MONTERRA',
        'torres': torres,
        'niveles_por_torre': niveles_out,
        'piezas': piezas
    }

def get_pieza_detail(codigo: str) -> Optional[Dict[str, Any]]:
    """Obtiene el estado completo de una pieza including cortes, vidrios e insumos."""
    p = fetch_one("SELECT * FROM piezas WHERE codigo=?", (codigo,))
    if not p: return None
    
    return {
        **p,
        'cortes': fetch_all("SELECT * FROM cortes WHERE pieza_codigo=? ORDER BY id", (codigo,)),
        'vidrios': fetch_all("SELECT * FROM vidrios WHERE pieza_codigo=? ORDER BY id", (codigo,)),
        'insumos': fetch_all("SELECT * FROM insumos WHERE pieza_codigo=? ORDER BY id", (codigo,)),
    }

def calculate_catalogo_sistema(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula un despiece sin persistirlo; usado por la pantalla de taller."""
    sistema_id = data.get('sistema_id')
    if not sistema_id:
        return {'error': 'Falta campo requerido: sistema_id'}

    try:
        ancho = float(data['ancho'])
        alto = float(data['alto'])
        alto_total = data.get('alto_total')
        if alto_total is not None:
            alto_total = float(alto_total)
    except (KeyError, TypeError, ValueError):
        return {'error': 'ancho y alto deben ser números válidos'}

    if ancho <= 0 or alto <= 0 or (alto_total is not None and alto_total <= 0):
        return {'error': 'Las medidas deben ser mayores a cero'}

    import calculos
    return calculos.calcular_sistema(sistema_id, ancho, alto, alto_total=alto_total)

def mark_corte_como_cortado(pieza_codigo: str, corte_id: int) -> bool:
    """Marca un corte como hecho y registra el movimiento en la bitácora."""
    # Transacción atómica: Actualiza estado + Log de movimiento
    queries = [
        ("UPDATE cortes SET estado='cortado' WHERE id=? AND pieza_codigo=? AND estado='pendiente'", (corte_id, pieza_codigo)),
        ("INSERT INTO movimientos (fecha, tipo, pieza_codigo, detalle) VALUES (date('now'), 'corte_cortado', ?, ?)", 
         (pieza_codigo, json.dumps({'corte_id': corte_id})))
    ]
    return execute_transaction(queries)

def calculate_and_persist_pieza(pieza_codigo: str) -> Optional[Dict[str, Any]]:
    """Calcula el despiece y lo guarda en la base de datos."""
    import calculos
    p = get_pieza_detail(pieza_codigo)
    if not p:
        return None

    resultado = calculos.calcular_sistema(
        p['sistema_id'], p['ancho_mm'], p['alto_mm'], alto_total=p.get('alto_total_mm')
    )
    if 'error' in resultado:
        return None

    # Transacción para limpiar y re‑insertar despiece
    queries = [
        ("DELETE FROM cortes WHERE pieza_codigo=?", (pieza_codigo,)),
        ("DELETE FROM vidrios WHERE pieza_codigo=?", (pieza_codigo,)),
        ("DELETE FROM insumos WHERE pieza_codigo=?", (pieza_codigo,))
    ]

    for c in resultado.get('componentes', []):
        queries.append(("INSERT INTO cortes (pieza_codigo, material_id, pieza_nombre, longitud_mm, cantidad, observaciones, estado) VALUES (?,?,?,?,?,?, 'pendiente')",
                        (pieza_codigo, c.get('material_id'), c.get('pieza'), c.get('longitud_mm'), c.get('cantidad'), c.get('observaciones'))))

    for v in resultado.get('vidrios', []):
        queries.append(("INSERT INTO vidrios (pieza_codigo, posicion, ancho_mm, alto_mm, cantidad, estado) VALUES (?,?,?,?,?, 'pendiente')",
                        (pieza_codigo, v.get('posicion'), v.get('ancho_mm'), v.get('alto_mm'), v.get('cantidad'))))

    for ins in resultado.get('insumos', []):
        queries.append(("INSERT INTO insumos (pieza_codigo, material_id, nombre, cantidad, unidad, tipo) VALUES (?,?,?,?,?, 'fijo')",
                        (pieza_codigo, ins.get('material_id'), ins.get('nombre'), ins.get('cantidad'), ins.get('unidad'))))

    if execute_transaction(queries):
        return get_pieza_detail(pieza_codigo)
    return None


def guardar_estado_pieza(codigo: str, cortes: List[Dict[str, Any]]) -> bool:
    """Actualiza el estado de los cortes marcados para una pieza.
    Cada elemento de *cortes* debe contener:
        {"id": "V‑01‑c0", "hecho": true/false}
    """
    # Construir consultas UPDATE para cada corte
    queries = []
    for c in cortes:
        corte_id = c.get('id')
        hecho = bool(c.get('hecho'))
        if not corte_id:
            continue
        nuevo_estado = 'cortado' if hecho else 'pendiente'
        queries.append(("UPDATE cortes SET estado=? WHERE id=? AND pieza_codigo=?", (nuevo_estado, corte_id, codigo)))
    if not queries:
        return False
    return execute_transaction(queries)

def get_global_dashboard() -> Dict[str, Any]:
    """Resumen de avance general."""
    total = fetch_one("SELECT COUNT(*) as total FROM piezas")['total']
    por_estado = fetch_all("SELECT estado, COUNT(*) as cant FROM piezas GROUP BY estado")
    
    estado_map = {r['estado']: r['cant'] for r in por_estado}
    
    return {
        'proyecto': 'MONTERRA',
        'total_piezas': total,
        'por_estado': {
            'pendiente': estado_map.get('pendiente', 0),
            'en_corte': estado_map.get('en_corte', 0),
            'armado': estado_map.get('armado', 0),
            'instalado': estado_map.get('instalado', 0),
        },
        'levantamientos_nuevos': contar_levantamientos_nuevos()
    }

# --- Servicios de Levantamiento (Obra → Taller) ---

def crear_levantamiento_desde_obra(data: Dict) -> Dict[str, Any]:
    """
    Crea un levantamiento desde la app de campo.
    Valida campos mínimos y registra en la bitácora.
    """
    campos_requeridos = ['torre', 'nivel', 'depto', 'operador', 'piezas']
    for c in campos_requeridos:
        if c not in data or not data[c]:
            return {'error': f'Falta campo requerido: {c}'}
    
    if not isinstance(data['piezas'], dict) or len(data['piezas']) == 0:
        return {'error': 'Debe incluir al menos una pieza medida'}
    
    lid = crear_levantamiento(data)
    return {
        'ok': True,
        'levantamiento_id': lid,
        'mensaje': f'Levantamiento #{lid} recibido en el taller'
    }

def obtener_levantamientos(solo_nuevos: bool = False) -> List[Dict]:
    """Para que el taller vea qué hay en cola de la obra."""
    return listar_levantamientos(solo_nuevos=solo_nuevos)

def confirmar_levantamiento_recibido(lid: int) -> bool:
    """Marca un levantamiento como procesado por el taller."""
    return marcar_levantamiento_recibido(lid)
