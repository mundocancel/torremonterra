"""
MONTERRA — API Flask para Sistema de Taller de Ventanería
===========================================================
Servidor: http://localhost:5000
Frontend: /frontend/taller.html
Base de datos: SQLite (data/taller.db)
"""

import json
import os
from flask import Flask, jsonify, request
from db import (
    init_db,
    get_db,
    get_proyecto,
    get_dashboard,
    get_pieza,
    marcar_corte_cortado,
    registrar_instalacion,
    calcular_y_guardar_pieza,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
FRONTEND_DIR = os.path.join(SCRIPT_DIR, '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/frontend')

# ===========================================================================
# INICIALIZACIÓN
# ===========================================================================
os.makedirs(DATA_DIR, exist_ok=True)
init_db()


# ===========================================================================
# CATÁLOGO (solo lectura, desde DB)
# ===========================================================================

@app.route('/api/catalog/sistemas')
def catalog_sistemas():
    """Lista de sistemas de ventanas/puertas disponibles."""
    conn = get_db()
    rows = conn.execute(
        "SELECT sistema_id, nombre, descripcion FROM catalogo_sistemas WHERE activo=1 ORDER BY nombre"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/catalog/materiales')
def catalog_materiales():
    """Lista de materiales/herrajes disponibles."""
    conn = get_db()
    rows = conn.execute(
        "SELECT material_id, nombre, unidad, precio_unitario, observaciones "
        "FROM catalogo_materiales ORDER BY material_id"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/catalog/calcular', methods=['POST'])
def catalog_calcular():
    """Calcula despiece para un sistema y medidas dadas (sin persistir)."""
    from calculos import calcular_sistema

    body = request.get_json(force=True, silent=True) or {}
    sistema_id = body.get('sistema_id', 'corrediza_3')
    ancho = float(body.get('ancho', body.get('ancho_mm', 0)))
    alto = float(body.get('alto', body.get('alto_mm', 0)))
    alto_total = body.get('alto_total')
    if isinstance(alto_total, (int, float)):
        alto_total = float(alto_total)
    else:
        alto_total = None

    # Parámetros extra para sistemas configurables
    params = {}
    for k in ('fijas', 'corredizas', 'mosquitero'):
        v = body.get(k)
        if v is not None:
            params[k] = v

    try:
        resultado = calcular_sistema(sistema_id, ancho, alto, alto_total=alto_total, **params)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===========================================================================
# PROYECTO (estructura del proyecto MONTERRA)
# ===========================================================================

@app.route('/api/proyecto')
def api_proyecto():
    """Retorna la estructura completa del proyecto: torres, niveles, piezas."""
    return jsonify(get_proyecto())


@app.route('/api/piezas')
def api_piezas():
    """Lista de piezas del proyecto (estado actual)."""
    proyecto = get_proyecto()
    return jsonify(proyecto['piezas'])


@app.route('/api/piezas/<codigo>')
def api_pieza(codigo):
    """Detalle de una pieza: cortes, vidrios, insumos, estado."""
    pieza = get_pieza(codigo)
    if pieza is None:
        return jsonify({'error': f'Pieza {codigo} no encontrada'}), 404
    return jsonify(pieza)


@app.route('/api/piezas/<codigo>/calcular', methods=['POST'])
def api_pieza_calcular(codigo):
    """Calcula y persiste cortes/vidrios/insumos para una pieza."""
    resultado = calcular_y_guardar_pieza(codigo)
    if resultado is None:
        return jsonify({'error': f'No se pudo calcular {codigo}'}), 404
    return jsonify(resultado)


@app.route('/api/piezas/<codigo>/cortar/<int:corte_id>', methods=['POST'])
def api_corte_marcar(codigo, corte_id):
    """Marca un corte como cortado."""
    ok = marcar_corte_cortado(codigo, corte_id)
    if not ok:
        return jsonify({'error': 'Corte no encontrado o ya marcado'}), 404
    return jsonify({'ok': True, 'corte_id': corte_id})


@app.route('/api/instalar', methods=['POST'])
def api_instalar():
    """Registra una instalación."""
    body = request.get_json(force=True, silent=True) or {}
    pieza_codigo = body.get('pieza_codigo')
    operador = body.get('operador', '').strip()
    ubicacion = body.get('ubicacion_instalacion', '').strip() or None
    observaciones = body.get('observaciones', '').strip() or None

    if not pieza_codigo:
        return jsonify({'error': 'pieza_codigo es requerido'}), 400
    if not operador:
        return jsonify({'error': 'operador es requerido'}), 400

    pieza = get_pieza(pieza_codigo)
    if pieza is None:
        return jsonify({'error': f'Pieza {pieza_codigo} no encontrada'}), 404

    iid = registrar_instalacion(pieza_codigo, operador, ubicacion, observaciones)
    return jsonify({
        'ok': True,
        'instalacion_id': iid,
        'pieza_codigo': pieza_codigo,
        'operador': operador,
    }), 201


# ===========================================================================
# DASHBOARD
# ===========================================================================

@app.route('/api/dashboard')
def api_dashboard():
    """Resumen de avance del proyecto."""
    return jsonify(get_dashboard())


# ===========================================================================
# STATUS
# ===========================================================================

@app.route('/api/status')
def api_status():
    """Estado del servidor y base de datos."""
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM piezas")
    piezas_count = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM cortes")
    cortes_count = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM instalaciones")
    instalaciones_count = cur.fetchone()[0]
    conn.close()

    return jsonify({
        'server': 'MONTERRA · Taller de Ventanería API',
        'version': '1.0.0',
        'database': {
            'path': os.path.abspath('data/taller.db'),
            'piezas': piezas_count,
            'cortes': cortes_count,
            'instalaciones': instalaciones_count,
        },
        'status': 'operational',
    })


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
