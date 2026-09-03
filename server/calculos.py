import ast
import json
import math
import os
from typing import Any, Dict, Optional

# ============================================================================
# EVALUADOR DE EXPRESIONES MATEMÁTICAS SEGURO
# Solo permite: números, variables, operaciones aritméticas,
# funciones floor/ceil/round. No strings, listas, etc.
# ============================================================================

class ExpressionEvaluator(ast.NodeVisitor):
    SAFE_FUNCTIONS = {
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
    }

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Str(self, node):
        raise ValueError("String literals not allowed")

    def visit_Num(self, node):
        return node.n

    def visit_Name(self, node):
        name = node.id
        if name in self.context:
            val = self.context[name]
            if isinstance(val, (int, float)):
                return val
            raise ValueError(f"Variable '{name}' no es numérica")
        raise NameError(f"name '{name}' is not defined")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left ** right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        raise ValueError(f"Operador no soportado: {type(node.op).__name__}")

    def visit_Compare(self, node):
        """Evalúa comparaciones: x > y, x <= y, etc."""
        left = self.visit(node.left)
        result = True
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if isinstance(op, ast.Gt):
                result = result and (left > right)
            elif isinstance(op, ast.Lt):
                result = result and (left < right)
            elif isinstance(op, ast.GtE):
                result = result and (left >= right)
            elif isinstance(op, ast.LtE):
                result = result and (left <= right)
            elif isinstance(op, ast.Eq):
                result = result and (left == right)
            else:
                raise ValueError(f"Comparador no soportado: {type(op).__name__}")
            left = right
        return result

    def visit_BoolOp(self, node):
        """Evalúa and / or"""
        values = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValueError(f"Operador booleano no soportado: {type(node.op).__name__}")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Operador unario no soportado: {type(node.op).__name__}")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.SAFE_FUNCTIONS:
            args = [self.visit(arg) for arg in node.args]
            return self.SAFE_FUNCTIONS[node.func.id](*args)
        raise ValueError(f"Llamada a función no soportada: {ast.dump(node)}")

    def evaluate(self, expr_str: str) -> Any:
        try:
            tree = ast.parse(expr_str.strip(), mode='eval')
            return self.visit(tree)
        except Exception as e:
            raise ValueError(f"Error evaluando '{expr_str}': {e}")


# ============================================================================
# CARGA DE DATOS
# ============================================================================

DATA_PATH = None


def _find_data_path() -> str:
    """Busca el JSON normalizado en ubicaciones conocidas.

    Prioridad:
    1. Misma carpeta que este archivo (para desarrollo local)
    2. Carpeta .hermes/desktop-attachments/ relativa al repo root
    3. Carpetas comunes de descargas del usuario
    """
    server_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(server_dir, 'proyecto_ventanas_normalizado.json'),
        os.path.join(server_dir, '..', '.hermes', 'desktop-attachments',
                     'proyecto_ventanas_normalizado.json'),
        os.path.join(server_dir, '..', 'proyecto_ventanas_normalizado.json'),
        os.path.expanduser('~/Downloads/proyecto_ventanas_normalizado.json'),
        os.path.expanduser('~/.hermes/desktop-attachments/proyecto_ventanas_normalizado.json'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    raise FileNotFoundError(
        "JSON no encontrado. Bajálo a server/ o ponlo en ~/.hermes/desktop-attachments/"
    )


def load_data() -> dict:
    global DATA_PATH
    if DATA_PATH is None:
        DATA_PATH = _find_data_path()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_catalogo_materiales() -> Dict[int, dict]:
    data = load_data()
    catalogo = {}
    for mat in data.get('catalogo_materiales', []):
        catalogo[mat['id']] = mat
    return catalogo


# ============================================================================
# FUNS DE CÁLCULO
# ============================================================================

def evaluate_cut(corte: Optional[dict], context: Dict[str, Any],
                 default_base: Optional[str] = None) -> Optional[float]:
    """Evalúa un corte: (base - resta) / dividir_entre.

    Si el corte no tiene 'base' explícito, usa default_base.
    """
    if not corte:
        return None
    base_key = corte.get('base') or default_base
    if not base_key:
        return None
    base_val = context.get(base_key)
    if base_val is None:
        return None
    resta = corte.get('resta', 0)
    div = corte.get('dividir_entre', 1)
    return (base_val - resta) / div


def evaluate_expression(expr_str: str, context: Dict[str, Any]) -> Any:
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate(expr_str)


# ============================================================================
# CÁLCULO DE SISTEMA
def calcular_sistema(sistema_id: str,
                     ancho: float,
                     alto: float,
                     alto_total: Optional[float] = None,
                     **parametros_extra) -> Dict[str, Any]:
    """Calcula el despiece de un sistema.

    Args:
        sistema_id: ID del sistema (ej. 'corrediza_3', 'ventanal_4_hojas')
        ancho: ancho real medido (mm)
        alto: alto real medido (mm)
        alto_total: alto total del vano (mm) — para fijo inferior
        **parametros_extra: parámetros adicionales del sistema
            (ej. fijas=2, corredizas=2, mosquitero=False)
    """
    data = load_data()
    sistemas = data['sistemas_formulas']
    sistema = sistemas.get(sistema_id)
    if not sistema:
        return {'error': f'Sistema "{sistema_id}" no encontrado'}

    alto_total_val = alto_total if alto_total is not None else alto
    ancho_f = float(ancho)
    alto_f = float(alto)
    alto_total_f = float(alto_total_val)

    # Contexto base para fórmulas
    context = {
        'ancho': ancho_f,
        'alto': alto_f,
        'ancho_total': ancho_f,
        'alto_total': alto_total_f,
        'perimetro_total': 2 * (ancho_f + alto_f),
        **parametros_extra,  # Agregar parámetros configurables
    }

    # Vidrios
    vidrios_calc = []
    for v in sistema.get('vidrios', []):
        ancho_v = evaluate_cut(v.get('corte_ancho', {}), context, 'ancho')
        alto_v_cfg = v.get('corte_alto', {})
        if 'expresion' in alto_v_cfg:
            alto_v = evaluate_expression(alto_v_cfg['expresion'], context)
        else:
            alto_v = evaluate_cut(alto_v_cfg, context, 'alto')
        cantidad = v.get('cantidad', 1)
        if v.get('cantidad_formula'):
            cantidad = evaluate_expression(v['cantidad_formula']['expresion'], context)
        if cantidad and cantidad > 0:
            vidrios_calc.append({
                'posicion': v.get('posicion', ''),
                'ancho_mm': round(ancho_v, 2) if ancho_v is not None else None,
                'alto_mm': round(alto_v, 2) if alto_v is not None else None,
                'cantidad': round(float(cantidad), 2),
                'observaciones': v.get('observaciones', ''),
            })

    # Insumos de mosquitero
    if parametros_extra.get('mosquitero', False):
        for ins in sistema.get('insumos_mosquitero', []):
            qty = ins.get('cantidad', 0)
            if ins.get('expresion'):
                qty = evaluate_expression(ins['expresion'], context)
            if qty and qty > 0:
                insumos_fijos.append({
                    'material_id': ins.get('material_id'),
                    'nombre': ins.get('nombre', ''),
                    'cantidad': round(float(qty), 2),
                    'unidad': ins.get('unidad', 'pieza'),
                    'observaciones': ins.get('observaciones', ''),
                })

    # Variables de perimetro para insumos (basados en vidrios calculados)
    if vidrios_calc:
        perimetros = []
        for v in vidrios_calc:
            if v['ancho_mm'] is not None and v['alto_mm'] is not None:
                perimetros.append(2 * (v['ancho_mm'] + v['alto_mm']))
        context['perimetro_un_vidrio'] = perimetros[0] if perimetros else 0
        context['suma_perimetros_ambos_vidrios'] = sum(perimetros) if perimetros else 0
    else:
        context['perimetro_un_vidrio'] = 0
        context['suma_perimetros_ambos_vidrios'] = 0

    # Componentes de perfil
    componentes = []
    for comp in sistema.get('componentes', []):
        corte = comp.get('corte')
        longitud = evaluate_cut(corte, context) if corte else None
        cantidad = comp.get('cantidad')
        if comp.get('cantidad_formula'):
            cantidad = evaluate_expression(comp['cantidad_formula']['expresion'], context)
        if cantidad and cantidad > 0:
            componentes.append({
                'pieza': comp.get('pieza', ''),
                'material_id': comp.get('material_id'),
                'longitud_mm': round(longitud, 2) if longitud is not None else None,
                'cantidad': round(float(cantidad), 2) if cantidad is not None else None,
                'observaciones': comp.get('observaciones', ''),
            })

    # Insumos fijos
    insumos_fijos = []
    for ins in sistema.get('insumos_fijos', []):
        insumos_fijos.append({
            'material_id': ins.get('material_id'),
            'nombre': ins.get('nombre', ''),
            'cantidad': ins.get('cantidad', 0),
            'unidad': ins.get('unidad', 'pieza'),
            'observaciones': ins.get('observaciones', ''),
        })

    # Componentes e insumos de mosquitero (solo si se requiere)
    if parametros_extra.get('mosquitero', False):
        for comp in sistema.get('componentes_mosquitero', []):
            corte = comp.get('corte')
            longitud = evaluate_cut(corte, context) if corte else None
            cantidad = comp.get('cantidad')
            if cantidad and cantidad > 0:
                componentes.append({
                    'pieza': comp.get('pieza', ''),
                    'material_id': comp.get('material_id'),
                    'longitud_mm': round(longitud, 2) if longitud is not None else None,
                    'cantidad': round(float(cantidad), 2) if cantidad is not None else None,
                    'observaciones': comp.get('observaciones', ''),
                })
        for ins in sistema.get('insumos_mosquitero', []):
            qty = ins.get('cantidad', 0)
            if ins.get('expresion'):
                qty = evaluate_expression(ins['expresion'], context)
            if qty and qty > 0:
                insumos_fijos.append({
                    'material_id': ins.get('material_id'),
                    'nombre': ins.get('nombre', ''),
                    'cantidad': round(float(qty), 2),
                    'unidad': ins.get('unidad', 'pieza'),
                    'observaciones': ins.get('observaciones', ''),
                })

    # Insumos por expresión
    insumos_expr = []
    for ins in sistema.get('insumos_por_expresion', []):
        qty = evaluate_expression(ins['expresion'], context)
        insumos_expr.append({
            'material_id': ins.get('material_id'),
            'nombre': ins.get('nombre', ''),
            'cantidad': round(float(qty), 2) if qty is not None else 0,
            'unidad': ins.get('unidad', 'pieza'),
            'observaciones': ins.get('observaciones', ''),
        })

    # Insumos condicionales
    insumos_cond = []
    for ins in sistema.get('insumos_condicionales', []):
        for cond in ins.get('condiciones', []):
            si_expr = cond.get('si', '')
            try:
                result = evaluate_expression(si_expr, context)
                if result:
                    nombre_final = cond.get('nombre', ins.get('nombre', ''))
                    observaciones_final = cond.get('observaciones', ins.get('observaciones', ''))
                    insumos_cond.append({
                        'material_id': ins.get('material_id'),
                        'nombre': nombre_final,
                        'cantidad': cond.get('cantidad', 0),
                        'unidad': ins.get('unidad', 'pieza'),
                        'observaciones': observaciones_final,
                    })
                    break
            except Exception as e:
                print(f"ERROR evaluando condicion '{si_expr}': {e}")
                pass

    # Resumen por material_id
    resumen_dict = {}

    def agregar(item):
        mid = item.get('material_id')
        if mid is None:
            return
        if mid not in resumen_dict:
            resumen_dict[mid] = {
                'material_id': mid,
                'nombre': item.get('nombre', ''),
                'cantidad_total': 0.0,
                'longitud_total_mm': 0.0,
                'unidad': item.get('unidad', 'pieza'),
                'observaciones': item.get('observaciones', ''),
            }
        cantidad = item.get('cantidad') or 0
        resumen_dict[mid]['cantidad_total'] += cantidad
        longitud = item.get('longitud_mm')
        if longitud is not None:
            resumen_dict[mid]['longitud_total_mm'] += longitud * cantidad

    for c in componentes:
        agregar(c)
    for i in insumos_fijos:
        agregar(i)
    for i in insumos_expr:
        agregar(i)
    for i in insumos_cond:
        agregar(i)

    return {
        'sistema': sistema_id,
        'sistema_nombre': sistema.get('nombre', ''),
        'ancho_mm': ancho,
        'alto_mm': alto,
        'alto_total_mm': alto_total_val,
        'componentes': componentes,
        'vidrios': vidrios_calc,
        'insumos': insumos_fijos + insumos_expr + insumos_cond,
        'resumen': list(resumen_dict.values()),
    }


# ============================================================================
# PRUEBAS (ejecutar: python server/calculos.py)
# ============================================================================

if __name__ == '__main__':
    print("=== PRUEBAS DEL MOTOR DE CÁLCULO ===\n")

    pruebas = [
        ('corrediza_3', 1990, 2400, None, 'V-01 Sala PB (corrediza 3" 1990x2400)'),
        ('corrediza_3', 1230, 1600, None, 'V-02 Comedor N1 (corrediza 3" 1230x1600)'),
        ('corrediza_3', 1230, 2400, None, 'V-03 Balcón (corrediza 3" 1230x2400)'),
        ('celosias_fijas', 740, 400, None, 'V-04 Lavandería (celosías 740x400)'),
        ('corrediza_3', 1990, 1600, None, 'V-05 Sala N1 (corrediza 3" 1990x1600)'),
        ('corrediza_3', 1990, 1200, 2400, 'V-06 Salas N2-N4 (corredera 1990x1200 + fijo inferior)'),
        ('sifon_eco', 430, 330, 330, 'V-07 Baño (sifón ecológico 430x330)'),
        ('corrediza_3', 990, 1200, 2400, 'V-08 Recámara 1 (corredera 990x1200 + fijo)'),
        ('corrediza_3', 990, 1200, 2400, 'V-09 Recámara 2 (corredera 990x1200 + fijo)'),
    ]

    for sistema_id, ancho, alto, alto_total, desc in pruebas:
        print(f"\n{'='*60}")
        print(f"SISTEMA: {sistema_id}")
        print(f"  {desc}")
        print(f"  Ancho: {ancho}mm | Alto: {alto}mm | Alto total: {alto_total}")
        print(f"{'='*60}")
        try:
            resultado = calcular_sistema(sistema_id, ancho, alto, alto_total)
            if 'error' in resultado:
                print(f"  ERROR: {resultado['error']}")
                continue

            print(f"\n📐 COMPONENTES ({len(resultado['componentes'])}):")
            for comp in resultado['componentes']:
                long_str = f"{comp['longitud_mm']}mm" if comp['longitud_mm'] is not None else "N/A"
                cant = comp['cantidad']
                print(f"  - {comp['pieza']} (mat#{comp['material_id']}): {long_str} x {cant} uds")

            print(f"\n🪟 VIDRIOS ({len(resultado['vidrios'])}):")
            for v in resultado['vidrios']:
                print(f"  - {v['posicion']}: {v['ancho_mm']} x {v['alto_mm']} mm x {v['cantidad']}")

            print(f"\n📦 INSUMOS ({len(resultado['insumos'])}):")
            for ins in resultado['insumos']:
                unid = f" {ins['unidad']}" if ins.get('unidad') else ""
                print(f"  - {ins['nombre']} (mat#{ins['material_id']}): {ins['cantidad']}{unid}")

            print(f"\n📊 RESUMEN ({len(resultado['resumen'])} materiales):")
            for r in resultado['resumen']:
                long_total = r['longitud_total_mm']
                if long_total > 0:
                    long_str = f" | Long: {long_total:.0f}mm ({long_total/1000:.2f}m)"
                else:
                    long_str = ""
                print(f"  - Mat#{r['material_id']} {r['nombre']}: {r['cantidad_total']} uds{r['unidad']}{long_str}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
