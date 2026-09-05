"""
MONTERRA — API Flask (Capa de Entrada)
Responsabilidad: Definir rutas, validar requests y retornar respuestas JSON.
"""

import os
from flask import Flask, jsonify, request
import services

# Rutas de directorios
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(SCRIPT_DIR, '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/frontend')

# Inicialización del sistema
services.initialize_system()

# ===========================================================================
# RUTAS DEL PROYECTO
# ===========================================================================

@app.route('/api/proyecto')
def api_proyecto():
    """Retorna la estructura completa del proyecto."""
    return jsonify(services.get_full_project())

@app.route('/api/piezas/<codigo>')
def api_pieza(codigo):
    """Detalle de una pieza: cortes, vidrios, insumos."""
    pieza = services.get_pieza_detail(codigo)
    if not pieza:
        return jsonify({'error': f'Pieza {codigo} no encontrada'}), 404
    return jsonify(pieza)

@app.route('/api/piezas/<codigo>/calcular', methods=['POST'])
def api_pieza_calcular(codigo):
    """Calcula y persiste el despiece de una pieza."""
    resultado = services.calculate_and_persist_pieza(codigo)
    if not resultado:
        return jsonify({'error': f'No se pudo calcular la pieza {codigo}'}), 404
    return jsonify(resultado)

@app.route('/api/calcular', methods=['POST'])
@app.route('/api/catalog/calcular', methods=['POST'])
def api_catalogo_calcular():
    """Calcula un sistema por sus medidas, sin modificar la base de datos."""
    resultado = services.calculate_catalogo_sistema(request.get_json(silent=True) or {})
    if 'error' in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado)

@app.route('/api/piezas/<codigo>/cortar/<int:corte_id>', methods=['POST'])
def api_corte_marcar(codigo, corte_id):
    """Marca un corte como cortado en la base de datos."""
    if services.mark_corte_como_cortado(codigo, corte_id):
        return jsonify({'ok': True, 'corte_id': corte_id})
    return jsonify({'error': 'Corte no encontrado o ya marcado'}), 404

@app.route('/api/dashboard')
def api_dashboard():
    """Resumen de avance general del proyecto."""
    return jsonify(services.get_global_dashboard())

@app.route('/api/status')
def api_status():
    """Estado básico del servidor."""
    return jsonify({
        'server': 'MONTERRA · Taller de Ventanería API',
        'version': '2.0.0',
        'status': 'operational'
    })

# ===========================================================================
# RUTAS DE LEVANTAMIENTO (Obra → Taller)
# ===========================================================================

@app.route('/api/levantamientos', methods=['POST'])
def api_levantamiento_crear():
    """
    Recibe un levantamiento capturado en obra.
    Body esperado:
    {
        "torre": "T-01", "nivel": "PB", "depto": "DEP1", "lado": "A",
        "operador": "Juan Ramírez",
        "piezas": {
            "V-01": {"ancho_mm": 1995, "alto_mm": 2410, "estado": "medido", "notas": "..."},
            ...
        },
        "notas_generales": "Se midió con..."
    }
    """
    data = request.get_json(silent=True) or {}
    resultado = services.crear_levantamiento_desde_obra(data)
    if 'error' in resultado:
        return jsonify(resultado), 400
    return jsonify(resultado), 201

@app.route('/api/levantamientos', methods=['GET'])
@app.route('/api/levantamientos/nuevos', methods=['GET'])
def api_levantamientos_listar():
    """Lista todos los levantamientos o solo los nuevos (no procesados)."""
    solo_nuevos = 'nuevos' in request.path
    return jsonify(services.obtener_levantamientos(solo_nuevos=solo_nuevos))

@app.route('/api/levantamientos/<int:lid>/recibir', methods=['POST'])
def api_levantamiento_recibir(lid):
    """Marca un levantamiento como recibido/procesado por el taller."""
    if services.confirmar_levantamiento_recibido(lid):
        return jsonify({'ok': True, 'levantamiento_id': lid})
    return jsonify({'error': 'Levantamiento no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
