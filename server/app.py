import json
import os
from flask import Flask, jsonify, request
from db import (
    init_db,
    get_db,
    get_inventory_snapshot,
    update_inventory_snapshot,
    add_inventory_movement,
    add_piece_installation,
    get_piece_installations,
    get_piece_installation,
    update_piece_installation,
    add_production_task,
    get_production_tasks,
    get_production_task,
    update_production_task,
    get_inventory_movements,
)

app = Flask(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "monterra.json")

def load_json():
    """Carga monterra.json con fallback seguro para estructuras faltantes."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================================
# INICIALIZACIÓN
# ============================================================================
init_db()

# ============================================================================
# CATÁLOGO (desde monterra.json)
# ============================================================================

@app.route("/api/catalog/pieces")
def catalog_pieces():
    data = load_json()
    return jsonify(data.get("catalogos", {}).get("piezas_catalogo", []))

@app.route("/api/catalog/types")
def catalog_types():
    data = load_json()
    return jsonify(data.get("catalogos", {}).get("tipos_pieza", []))

@app.route("/api/catalog/components")
def catalog_components():
    data = load_json()
    return jsonify({
        "corrediza_3pulg": data["catalogos"]["componentes"].get("corrediza_3pulg", []),
        "fijo_inferior": data["catalogos"]["componentes"].get("fijo_inferior", []),
    })

@app.route("/api/catalog/hardware")
def catalog_hardware():
    data = load_json()
    return jsonify({
        "corrediza_3pulg": data["catalogos"]["herrajes"].get("corrediza_3pulg", []),
        "fijo_inferior": data["catalogos"]["herrajes"].get("fijo_inferior", []),
    })

@app.route("/api/catalog/rules")
def catalog_rules():
    data = load_json()
    reglas = data.get("catalogos", {}).get("reglas_calculo", {})
    return jsonify({
        "corrediza_3pulg": reglas.get("corrediza_3pulg", []),
        "fijo_inferior": reglas.get("fijo_inferior", []),
    })

@app.route("/api/catalog/calculate", methods=["POST"])
def calculate():
    body = request.get_json()
    ancho = float(body.get("ancho_mm", 0))
    alto = float(body.get("alto_mm", 0))
    tipo = body.get("tipo_calculo", "corrediza_3pulg")

    if tipo == "corrediza_3pulg":
        # Leer reglas desde monterra.json (es un array de objetos con nombre/valor)
        data = load_json()
        reglas_lista = data.get("catalogos", {}).get("reglas_calculo", {}).get("corrediza_3pulg", [])

        def _get_regla(nombre_buscar: str, default: float) -> float:
            for r in reglas_lista:
                if nombre_buscar.lower() in r.get("nombre", "").lower():
                    return float(r.get("valor_numerico", default))
            return default

        resta_hojas = _get_regla("Resta hojas ancho", 185.0)
        resta_cerco = _get_regla("Resta cerco chapa alto", 30.0)
        resta_traslape = _get_regla("Resta traslape alto", 40.0)
        resta_vidrio_ancho = _get_regla("Resta vidrio ancho", 155.0)
        resta_vidrio_fijo_alto = _get_regla("Resta vidrio alto panel fijo", 125.0)
        resta_vidrio_cored_alto = _get_regla("Resta vidrio alto panel corredizo", 135.0)

        zoclo = (ancho - resta_hojas) / 2
        vidrio_fijo_ancho = (ancho - resta_vidrio_ancho) / 2

        return jsonify({
            "tipo": "corrediza_3pulg",
            "ancho_mm": ancho,
            "alto_mm": alto,
            "componentes": [
                {"nombre": "Riel de 3\"", "medida_mm": ancho, "cantidad": 1},
                {"nombre": "Jamba de 3\"", "medida_mm": ancho, "cantidad": 2},
                {"nombre": "Cabezal de 3\"", "medida_mm": ancho, "cantidad": 1},
                {"nombre": "Zoclo doble vena", "medida_mm": round(zoclo, 2), "cantidad": 2},
                {"nombre": "Cabezal hojas", "medida_mm": round(zoclo, 2), "cantidad": 2},
                {"nombre": "Cerco chapa fijo", "medida_mm": alto - resta_cerco, "cantidad": 1},
                {"nombre": "Traslape corredizo", "medida_mm": alto - resta_traslape, "cantidad": 1},
                {"nombre": "Vidrio panel fijo", "medida_mm_ancho": round(vidrio_fijo_ancho, 2),
                 "medida_mm_alto": alto - resta_vidrio_fijo_alto, "cantidad": 1},
                {"nombre": "Vidrio panel corredizo", "medida_mm_ancho": round(vidrio_fijo_ancho, 2),
                 "medida_mm_alto": alto - resta_vidrio_cored_alto, "cantidad": 1}
            ]
        })

    return jsonify({"error": "tipo_calculo no soportado"}), 400

# ============================================================================
# INVENTARIO (desde monterra.json + DB snapshot)
# ============================================================================

@app.route("/api/inventory")
def inventory():
    """Lista inventario: datos del JSON + snapshot de DB."""
    data = load_json()
    inventario_json = data["inventario"]
    
    conn = get_db()
    cur = conn.execute("SELECT * FROM inventory_snapshot")
    rows = cur.fetchall()
    conn.close()
    
    snapshots = {row["material_id"]: dict(row) for row in rows}
    
    resultado = {}
    for material_id, info in inventario_json.items():
        snapshot = snapshots.get(material_id, {})
        # Snapshot de DB (actualizado por movimientos)
        cant_db = snapshot.get("cantidad_disponible", info.get("cantidad_disponible", 0))
        resultado[material_id] = {
            "tipo_material": info.get("tipo_material", ""),
            "unidad_medida": info.get("unidad_medida", ""),
            "cantidad_disponible": info.get("cantidad_disponible", 0),
            "cantidad_minima": info.get("cantidad_minima", 0),
            "proveedor_principal": info.get("proveedor_principal", ""),
            "costo_unitario": info.get("costo_unitario", 0),
            "cantidad_disponible_db": cant_db,
            "alerta_stock_negativo": cant_db < 0,
            "fecha_actualizacion_db": snapshot.get("fecha_actualizacion", None),
        }
    return jsonify(resultado)

@app.route("/api/inventory/snapshot/<material_id>")
def inventory_snapshot(material_id):
    """Snapshot actual de un material desde DB, con flag de stock negativo."""
    snapshot = get_inventory_snapshot(material_id)
    if snapshot:
        snapshot["alerta_stock_negativo"] = snapshot.get("cantidad_disponible", 0) < 0
        return jsonify(snapshot)
    return jsonify({"error": "Material no encontrado"}), 404

@app.route("/api/inventory/move", methods=["POST"])
def inventory_move():
    """Registra un movimiento de inventario."""
    body = request.get_json()
    material_id = body.get("material_id", "")
    tipo = body.get("tipo", "salida")
    cantidad = float(body.get("cantidad", 0))
    motivo = body.get("motivo", "")
    usuario_id = body.get("usuario_id", "")
    ref_instalacion_id = body.get("ref_instalacion_id", "")
    
    if not material_id or tipo not in ("entrada", "salida", "ajuste"):
        return jsonify({"error": "Datos inválidos"}), 400
    
    mov_id = add_inventory_movement(
        material_id=material_id,
        tipo_movimiento=tipo,
        cantidad=cantidad,
        motivo=motivo or None,
        usuario_id=usuario_id or None,
        ref_instalacion_id=ref_instalacion_id or None
    )
    
    # Retornar snapshot actualizado, con alerta si el stock quedó negativo
    snapshot = get_inventory_snapshot(material_id)
    alerta = False
    if snapshot is not None:
        alerta = snapshot.get("cantidad_disponible", 0) < 0
    return jsonify({
        "movimiento_id": mov_id,
        "material_id": material_id,
        "tipo": tipo,
        "cantidad": cantidad,
        "snapshot_actualizado": snapshot,
        "alerta_stock_negativo": alerta,
    })

@app.route("/api/inventory/movements")
def inventory_movements():
    """Historial de movimientos de inventario."""
    material_id = request.args.get("material_id", "")
    limite = request.args.get("limite", 100, type=int)
    
    movimientos = get_inventory_movements(
        material_id=material_id or None,
        limite=limite
    )
    return jsonify(movimientos)

# ============================================================================
# PRODUCCIÓN - PIECE INSTALLATIONS
# ============================================================================

@app.route("/api/production/pieces", methods=["GET"])
def get_pieces():
    """Lista piezas instaladas."""
    torre = request.args.get("torre", "")
    nivel = request.args.get("nivel", "")
    estado = request.args.get("estado", "")
    
    pieces = get_piece_installations(
        torre_codigo=torre or None,
        nivel_nombre=nivel or None,
        estado=estado or None
    )
    return jsonify(pieces)

@app.route("/api/production/pieces", methods=["POST"])
def create_piece():
    """Registra una pieza instalada/fabricada."""
    body = request.get_json()
    
    required = ["codigo_plano", "pieza_catalogo_id", "departamento_id", "torre_codigo", "nivel_nombre"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Campo requerido: {field}"}), 400
    
    # Validar que pieza_catalogo_id existe en el catálogo
    data = load_json()
    catalogo_piezas = data.get("catalogos", {}).get("piezas_catalogo", [])
    catalogo_ids = {p.get("codigo_plano") for p in catalogo_piezas if p.get("codigo_plano")}
    
    pieza_catalogo_id = body["pieza_catalogo_id"]
    if pieza_catalogo_id not in catalogo_ids:
        return jsonify({
            "error": f"pieza_catalogo_id '{pieza_catalogo_id}' no existe en el catálogo",
            "catalogo_disponible": sorted(catalogo_ids)
        }), 400
    
    piece_id = add_piece_installation(
        codigo_plano=body["codigo_plano"],
        pieza_catalogo_id=pieza_catalogo_id,
        departamento_id=body["departamento_id"],
        torre_codigo=body["torre_codigo"],
        nivel_nombre=body["nivel_nombre"],
        estado=body.get("estado", "pendiente"),
        usuario_asignado=body.get("usuario_asignado"),
        observaciones=body.get("observaciones")
    )
    
    return jsonify({"id": piece_id, "estado": "pendiente"}), 201

@app.route("/api/production/pieces/<piece_id>", methods=["GET"])
def get_piece(piece_id):
    """Retorna una pieza instalada por ID."""
    piece = get_piece_installation(piece_id)
    if piece:
        return jsonify(piece)
    return jsonify({"error": "Pieza no encontrada"}), 404

@app.route("/api/production/pieces/<piece_id>", methods=["PUT"])
def update_piece(piece_id):
    """Actualiza una pieza instalada."""
    body = request.get_json()
    update_piece_installation(
        piece_id=piece_id,
        estado=body.get("estado"),
        usuario_asignado=body.get("usuario_asignado"),
        observaciones=body.get("observaciones"),
        fecha_fin_fabricacion=body.get("fecha_fin_fabricacion"),
        fecha_fin_instalacion=body.get("fecha_fin_instalacion")
    )
    piece = get_piece_installation(piece_id)
    return jsonify(piece)

# ============================================================================
# TAREAS DE PRODUCCIÓN
# ============================================================================

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    """Lista tareas de producción."""
    usuario = request.args.get("usuario", "")
    estado = request.args.get("estado", "")
    
    tasks = get_production_tasks(
        usuario_asignado=usuario or None,
        estado=estado or None
    )
    return jsonify(tasks)

@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Crea una tarea de producción."""
    body = request.get_json()
    
    required = ["tipo", "titulo", "usuario_asignado"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Campo requerido: {field}"}), 400
    
    task_id = add_production_task(
        tipo=body["tipo"],
        titulo=body["titulo"],
        descripcion=body.get("descripcion"),
        prioridad=body.get("prioridad", 1),
        usuario_asignado=body["usuario_asignado"],
        pieza_instalacion_id=body.get("pieza_instalacion_id"),
        tiempo_estimado_minutos=body.get("tiempo_estimado_minutos")
    )
    
    return jsonify({"id": task_id}), 201

@app.route("/api/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    """Retorna una tarea por ID."""
    task = get_production_task(task_id)
    if task:
        return jsonify(task)
    return jsonify({"error": "Tarea no encontrada"}), 404

@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    """Actualiza una tarea de producción."""
    body = request.get_json()
    update_production_task(
        task_id=task_id,
        estado=body.get("estado"),
        fecha_completado=body.get("fecha_completado"),
        tiempo_real_minutos=body.get("tiempo_real_minutos")
    )
    task = get_production_task(task_id)
    return jsonify(task)

# ============================================================================
# STATUS DEL SERVIDOR
# ============================================================================

@app.route("/api/status")
def status():
    """Estado del servidor y base de datos."""
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM piece_installations")
    pieces_count = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM inventory_movements")
    movements_count = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM production_tasks")
    tasks_count = cur.fetchone()[0]
    conn.close()
    
    return jsonify({
        "server": "Taller Ventanería API",
        "version": "1.0.0",
        "database": {
            "path": os.path.abspath("data/taller.db"),
            "pieces": pieces_count,
            "movements": movements_count,
            "tasks": tasks_count,
        },
        "status": "operational"
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
