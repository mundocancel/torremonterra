"""
MONTERRA — API Flask (Capa de Entrada)
Responsabilidad: Definir rutas, validar requests y retornar respuestas JSON.
"""

import os
from flask_cors import CORS
from flask import Flask, jsonify, request
from server import services

# Rutas de directorios
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(SCRIPT_DIR, '..', 'frontend')
# Configuramos la carpeta de plantillas (templates) que está en la raíz del proyecto
TEMPLATE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'templates'))

# Inicializamos Flask indicando carpeta estática y de plantillas
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/frontend', template_folder=TEMPLATE_DIR)
# Permitir que la UI estática en GitHub Pages haga peticiones al backend
CORS(app, origins=["https://*.github.io", "https://*.githubusercontent.com"])


# Inicialización del sistema – solo si la base de datos aún no existe
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'taller.db'))
if not os.path.isfile(DB_PATH):
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

# ---------------------------------------------------------------------------
# RUTAS ADICIONALES PARA INTERFAZ VISOR
# ---------------------------------------------------------------------------

# Ruta principal que renderiza la vista del visor (template Jinja)
@app.route('/')
def index():
    """Renderiza la página principal del visor de piezas."""
    from flask import render_template
    return render_template('visor.html')

# Endpoint para guardar el estado de los cortes marcados de una pieza
@app.route('/api/guardar_estado', methods=['POST'])
def api_guardar_estado():
    """Persiste el estado de los cortes de una pieza.
    Espera JSON:
    {
        "codigo": "V-01",
        "cortes": [{"id": "V-01-c0", "hecho": true}, ...]
    }
    """
    data = request.get_json(silent=True) or {}
    codigo = data.get('codigo')
    cortes = data.get('cortes')
    if not codigo or not isinstance(cortes, list):
        return jsonify({'error': 'Formato inválido'}), 400
    if services.guardar_estado_pieza(codigo, cortes):
        return jsonify({'ok': True, 'codigo': codigo})
    return jsonify({'error': 'No se pudo guardar'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
