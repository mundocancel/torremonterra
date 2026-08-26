import json
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_PATH = "monterra.json"

def load_json():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/api/catalog/pieces")
def catalog_pieces():
    return jsonify(load_json()["catalogos"]["piezas_catalogo"])

@app.route("/api/catalog/types")
def catalog_types():
    return jsonify(load_json()["catalogos"]["tipos_pieza"])

@app.route("/api/inventory")
def inventory():
    return jsonify(load_json()["inventario"])

@app.route("/api/catalog/calculate", methods=["POST"])
def calculate():
    body = request.get_json()
    ancho = float(body.get("ancho_mm", 0))
    alto = float(body.get("alto_mm", 0))
    tipo = body.get("tipo_calculo", "corrediza_3pulg")

    if tipo == "corrediza_3pulg":
        resta_hojas = 185.0
        resta_cerco = 30.0
        resta_traslape = 40.0
        resta_vidrio_ancho = 155.0
        resta_vidrio_fijo_alto = 125.0
        resta_vidrio_cored_alto = 135.0

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
