#!/bin/bash
# ============================================================
# CONVERTIR MD A PROYECTO + TEST AUTOMÁTICO
# Torre MONTERRA - Full Automation
# ============================================================

set -e

INPUT="backend.md"
OUTPUT="torre-monterra-backend"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ============ 1. CREAR PROYECTO ============
print_header "📦 CREANDO PROYECTO DESDE MD"

# Crear estructura
mkdir -p "$OUTPUT"/{routes,data,test}

# Función para extraer archivos
extract_file() {
    local filename=$1
    local output=$2
    
    awk -v fname="$filename" '
    BEGIN { inside=0; }
    $0 ~ "## 📄 .*" fname {
        inside=1;
        next;
    }
    inside && /```/ && !inside_code {
        inside_code=1;
        next;
    }
    inside && inside_code && /```/ {
        inside_code=0;
        inside=0;
        next;
    }
    inside && inside_code {
        print;
    }
    ' "$INPUT" > "$output"
    
    if [ -s "$output" ]; then
        print_success "$output"
        return 0
    else
        print_error "$output (vacío)"
        return 1
    fi
}

# Extraer todos los archivos
extract_file "package.json" "$OUTPUT/package.json"
extract_file "server.js" "$OUTPUT/server.js"
extract_file "routes/api.js" "$OUTPUT/routes/api.js"
extract_file "data/project.json" "$OUTPUT/data/project.json"
extract_file "data/materials.json" "$OUTPUT/data/materials.json"
extract_file "data/components.json" "$OUTPUT/data/components.json"
extract_file "data/tour.json" "$OUTPUT/data/tour.json"
extract_file ".env" "$OUTPUT/.env"
extract_file "README.md" "$OUTPUT/README.md"

# Crear .gitignore
cat > "$OUTPUT/.gitignore" << 'EOF'
node_modules/
.env
*.log
package-lock.json
EOF

print_success "Proyecto creado en $OUTPUT/"

# ============ 2. INSTALAR DEPENDENCIAS ============
print_header "📦 INSTALANDO DEPENDENCIAS"

cd "$OUTPUT"

if npm install --silent 2>&1 | grep -v "added"; then
    print_success "Dependencias instaladas"
else
    print_error "Error instalando dependencias"
    exit 1
fi

# ============ 3. INICIAR SERVIDOR EN BACKGROUND ============
print_header "🚀 INICIANDO SERVIDOR"

# Matar procesos previos en puerto 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Iniciar servidor en background
npm start > server.log 2>&1 &
SERVER_PID=$!

print_info "Servidor iniciado con PID: $SERVER_PID"
print_info "Esperando que el servidor esté listo..."

# Esperar a que el servidor responda
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Servidor listo en http://localhost:3000"
        break
    fi
    sleep 1
    RETRY=$((RETRY+1))
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    print_error "Servidor no respondió después de $MAX_RETRIES segundos"
    cat server.log
    kill $SERVER_PID
    exit 1
fi

# ============ 4. EJECUTAR PRUEBAS ============
print_header "🧪 EJECUTANDO PRUEBAS DE API"

# Crear archivo de resultados
RESULTS_FILE="test-results.txt"
echo "=== TEST DE API - Torre MONTERRA ===" > "$RESULTS_FILE"
echo "Fecha: $(date)" >> "$RESULTS_FILE"
echo "=====================================" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "  Probando $name... "
    
    RESPONSE=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        print_success "$name (200 OK)"
        echo "✅ $name: OK" >> "$RESULTS_FILE"
        echo "   URL: $url" >> "$RESULTS_FILE"
        echo "   Status: $HTTP_CODE" >> "$RESULTS_FILE"
        
        # Verificar contenido esperado
        if [ ! -z "$expected" ] && echo "$BODY" | grep -q "$expected"; then
            echo "   ✅ Contiene: $expected" >> "$RESULTS_FILE"
        fi
        echo "" >> "$RESULTS_FILE"
        return 0
    else
        print_error "$name (HTTP $HTTP_CODE)"
        echo "❌ $name: FALLÓ" >> "$RESULTS_FILE"
        echo "   URL: $url" >> "$RESULTS_FILE"
        echo "   Status: $HTTP_CODE" >> "$RESULTS_FILE"
        echo "   Response: $BODY" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 1
    fi
}

print_info "Probando endpoints..."

# Tests
test_endpoint "Health Check" "http://localhost:3000/api/health" "online"
test_endpoint "Project Info" "http://localhost:3000/api/project" "Torre MONTERRA"
test_endpoint "Levels" "http://localhost:3000/api/levels" "Planta Baja"
test_endpoint "Materials" "http://localhost:3000/api/materials" "floors"
test_endpoint "Components" "http://localhost:3000/api/components" "doors"
test_endpoint "Tour" "http://localhost:3000/api/tour" "Tour Arquitectónico"
test_endpoint "Drawings" "http://localhost:3000/api/drawings" "ARQ-01"
test_endpoint "Search" "http://localhost:3000/api/search?q=CEMIX" "CEMIX"

# ============ 5. GENERAR REPORTE ============
print_header "📊 GENERANDO REPORTE DE PRUEBAS"

echo "" >> "$RESULTS_FILE"
echo "=====================================" >> "$RESULTS_FILE"
echo "RESUMEN DE PRUEBAS" >> "$RESULTS_FILE"
echo "=====================================" >> "$RESULTS_FILE"

PASSED=$(grep -c "✅" "$RESULTS_FILE")
FAILED=$(grep -c "❌" "$RESULTS_FILE")
TOTAL=$((PASSED + FAILED))

echo "Total de pruebas: $TOTAL" >> "$RESULTS_FILE"
echo "✅ Pasaron: $PASSED" >> "$RESULTS_FILE"
echo "❌ Fallaron: $FAILED" >> "$RESULTS_FILE"

if [ $FAILED -eq 0 ]; then
    echo "🎉 TODAS LAS PRUEBAS PASARON" >> "$RESULTS_FILE"
else
    echo "⚠️  ALGUNAS PRUEBAS FALLARON" >> "$RESULTS_FILE"
fi

echo "=====================================" >> "$RESULTS_FILE"

# Mostrar resumen
cat "$RESULTS_FILE"

# ============ 6. CREAR SCRIPT DE TEST REUTILIZABLE ============
cat > "test-api.sh" << 'EOF'
#!/bin/bash
# Script de pruebas reutilizable

BASE_URL="http://localhost:3000/api"

echo "🧪 Probando Torre MONTERRA API..."

test_endpoint() {
    local name=$1
    local url=$2
    
    echo -n "  $name... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "✅ OK (200)"
    else
        echo "❌ FAIL ($HTTP_CODE)"
    fi
}

test_endpoint "Health" "$BASE_URL/health"
test_endpoint "Project" "$BASE_URL/project"
test_endpoint "Levels" "$BASE_URL/levels"
test_endpoint "Materials" "$BASE_URL/materials"
test_endpoint "Components" "$BASE_URL/components"
test_endpoint "Tour" "$BASE_URL/tour"
test_endpoint "Drawings" "$BASE_URL/drawings"
test_endpoint "Search" "$BASE_URL/search?q=puerta"

echo "✅ Pruebas completadas"
EOF

chmod +x "test-api.sh"
print_success "Script de pruebas creado: test-api.sh"

# ============ 7. CREAR SCRIPT DE INICIO RÁPIDO ============
cat > "start.sh" << 'EOF'
#!/bin/bash
echo "🚀 Iniciando Torre MONTERRA..."
npm start
EOF

chmod +x "start.sh"
print_success "Script de inicio creado: start.sh"

# ============ 8. MOSTRAR RESULTADOS FINALES ============
print_header "🎉 PROYECTO COMPLETADO CON ÉXITO"

echo -e "${GREEN}📂 Proyecto:${NC} $OUTPUT/"
echo -e "${GREEN}📊 Pruebas:${NC} $PASSED/$TOTAL exitosas"
echo -e "${GREEN}📄 Reporte:${NC} $OUTPUT/test-results.txt"
echo -e "${GREEN}🧪 Test script:${NC} $OUTPUT/test-api.sh"
echo -e "${GREEN}🚀 Inicio:${NC} $OUTPUT/start.sh"
echo ""

echo -e "${BLUE}📋 Servidor corriendo en:${NC} http://localhost:3000"
echo -e "${BLUE}📡 API disponible en:${NC} http://localhost:3000/api"
echo ""

echo -e "${YELLOW}💡 Comandos útiles:${NC}"
echo "  cd $OUTPUT"
echo "  ./test-api.sh        # Ejecutar pruebas"
echo "  ./start.sh           # Iniciar servidor"
echo "  cat test-results.txt # Ver reporte de pruebas"
echo ""

# ============ 9. LIMPIEZA ==========
print_info "Presiona Ctrl+C para detener el servidor cuando termines"

# Mantener servidor corriendo
wait $SERVER_PID
```

---

🚀 Cómo usarlo

```bash
# 1. Guarda el script
nano convertir-y-testear.sh

# 2. Dale permisos
chmod +x convertir-y-testear.sh

# 3. Ejecuta (TODO AUTOMÁTICO)
./convertir-y-testear.sh
```

---

📊 Lo que hace automáticamente

Paso Acción Resultado
1️⃣ Extrae código del MD Crea todos los archivos
2️⃣ Instala dependencias npm install
3️⃣ Inicia servidor En background en puerto 3000
4️⃣ Ejecuta 8 pruebas Health, Project, Levels, etc.
5️⃣ Genera reporte test-results.txt
6️⃣ Crea scripts útiles test-api.sh y start.sh
7️⃣ Muestra resumen Pasados/Fallados

---

✅ Ejemplo de salida

```
🧪 EJECUTANDO PRUEBAS DE API
  Probando Health Check... ✅ Health Check (200 OK)
  Probando Project Info... ✅ Project Info (200 OK)
  Probando Levels... ✅ Levels (200 OK)
  Probando Materials... ✅ Materials (200 OK)
  Probando Components... ✅ Components (200 OK)
  Probando Tour... ✅ Tour (200 OK)
  Probando Drawings... ✅ Drawings (200 OK)
  Probando Search... ✅ Search (200 OK)

📊 GENERANDO REPORTE DE PRUEBAS
Total de pruebas: 8
✅ Pasaron: 8
❌ Fallaron: 0
🎉 TODAS LAS PRUEBAS PASARON
```

---

📁 Archivos generados

```
torre-monterra-backend/
├── server.js
├── package.json
├── .env
├── test-results.txt      # 📊 Reporte de pruebas
├── test-api.sh           # 🧪 Script de pruebas reutilizable
├── start.sh              # 🚀 Inicio rápido
├── routes/api.js
└── data/*.json
