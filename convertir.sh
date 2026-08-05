#!/bin/bash
# ============================================================
# CONVERTIR MD A PROYECTO NODE.JS - Torre MONTERRA
# Uso: ./convertir.sh
# ============================================================

set -e  # Detener en errores

# ============ CONFIGURACIÓN ============
INPUT="backend.md"
PROJECT_DIR="torre-monterra-backend"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ FUNCIONES ============
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    exit 1
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Función para extraer bloques de código por lenguaje
extract_block() {
    local lang=$1
    local output=$2
    
    sed -n "/\`\`\`$lang/,/\`\`\`/ {
        /\`\`\`$lang/d
        /\`\`\`/d
        p
    }" "$INPUT" > "$output"
}

# Función para extraer bloques con nombre específico
extract_named_block() {
    local name=$1
    local lang=$2
    local output=$3
    
    awk -v name="$name" -v lang="$lang" '
    BEGIN { found=0; inside=0; }
    $0 ~ "## 📄 " name {
        found=1;
        next;
    }
    found && /```/ && !inside {
        inside=1;
        next;
    }
    inside && /```/ {
        inside=0;
        found=0;
        next;
    }
    inside {
        print;
    }
    ' "$INPUT" > "$output"
}

# ============ VALIDACIÓN ============
print_header "🔍 VALIDANDO ARCHIVO"

if [ ! -f "$INPUT" ]; then
    print_error "No se encuentra el archivo $INPUT"
fi

print_success "Archivo $INPUT encontrado"

# ============ CREAR ESTRUCTURA ============
print_header "📁 CREANDO ESTRUCTURA DE CARPETAS"

mkdir -p "$PROJECT_DIR"/{routes,data,frontend}
print_success "Estructura creada: $PROJECT_DIR/"

# ============ EXTRAER ARCHIVOS ============
print_header "📤 EXTRAYENDO CÓDIGO FUENTE"

# 1. server.js
if extract_block "javascript" "$PROJECT_DIR/server.js"; then
    print_success "server.js extraído"
else
    print_warning "No se encontró server.js"
fi

# 2. routes/api.js
mkdir -p "$PROJECT_DIR/routes"
if extract_block "javascript" "$PROJECT_DIR/routes/api.js"; then
    print_success "routes/api.js extraído"
else
    print_warning "No se encontró routes/api.js"
fi

# 3. package.json
if extract_block "json" "$PROJECT_DIR/package.json"; then
    print_success "package.json extraído"
else
    print_warning "No se encontró package.json"
fi

# 4. Archivos de datos
if extract_block "json" "$PROJECT_DIR/data/project.json"; then
    print_success "data/project.json extraído"
else
    print_warning "No se encontró data/project.json"
fi

if extract_block "json" "$PROJECT_DIR/data/materials.json"; then
    print_success "data/materials.json extraído"
else
    print_warning "No se encontró data/materials.json"
fi

if extract_block "json" "$PROJECT_DIR/data/components.json"; then
    print_success "data/components.json extraído"
else
    print_warning "No se encontró data/components.json"
fi

if extract_block "json" "$PROJECT_DIR/data/tour.json"; then
    print_success "data/tour.json extraído"
else
    print_warning "No se encontró data/tour.json"
fi

# 5. .env
if extract_block "env" "$PROJECT_DIR/.env"; then
    print_success ".env extraído"
else
    print_warning "No se encontró .env, creando uno por defecto"
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Configuración del servidor
PORT=3000
NODE_ENV=development

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5500

# API
API_PREFIX=/api
API_VERSION=v1
EOF
fi

# 6. README.md
if extract_block "markdown" "$PROJECT_DIR/README.md"; then
    print_success "README.md extraído"
else
    print_warning "No se encontró README.md, creando uno básico"
    cat > "$PROJECT_DIR/README.md" << 'EOF'
# Torre MONTERRA - Backend API

API REST para el proyecto arquitectónico Torre MONTERRA.

## Instalación
```bash
npm install
```

Ejecución

```bash
npm start
```

Endpoints

· GET /api/health
· GET /api/project
· GET /api/levels
· GET /api/materials
· GET /api/components
· GET /api/tour
· GET /api/drawings
· GET /api/search?q=term
  EOF
  fi

============ CREAR SCRIPT DE INSTALACIÓN ============

print_header "🔧 CREANDO SCRIPT DE INSTALACIÓN"

cat > "$PROJECT_DIR/setup.sh" << 'EOF'
#!/bin/bash

Script de instalación y configuración

echo "🚀 Instalando dependencias..."
npm install

echo "📦 Instalando nodemon como dependencia de desarrollo..."
npm install --save-dev nodemon

echo "✅ Instalación completada"

echo ""
echo "📋 Comandos disponibles:"
echo "  npm start    - Ejecutar en producción"
echo "  npm run dev  - Ejecutar en desarrollo"
echo ""
echo "🌐 Servidor disponible en: http://localhost:3000"
EOF

chmod +x "$PROJECT_DIR/setup.sh"
print_success "setup.sh creado"

============ CREAR SCRIPT DE INICIO RÁPIDO ============

print_header "⚡ CREANDO SCRIPT DE INICIO RÁPIDO"

cat > "iniciar.sh" << 'EOF'
#!/bin/bash

Iniciar el proyecto Torre MONTERRA

cd torre-monterra-backend

echo "=========================================="
echo "🏢 TORRE MONTERRA - Iniciando Backend"
echo "=========================================="

Verificar si node_modules existe

if [ ! -d "node_modules" ]; then
echo "📦 Instalando dependencias..."
npm install
fi

Iniciar servidor

echo "🚀 Iniciando servidor..."
npm start
EOF

chmod +x "iniciar.sh"
print_success "iniciar.sh creado"

============ CREAR SCRIPT DE LIMPIEZA ============

cat > "limpiar.sh" << 'EOF'
#!/bin/bash

Limpiar archivos generados

echo "🧹 Limpiando proyecto..."
rm -rf torre-monterra-backend/node_modules
rm -rf torre-monterra-backend/package-lock.json
echo "✅ Limpieza completada"
EOF

chmod +x "limpiar.sh"
print_success "limpiar.sh creado"

============ CREAR .gitignore ============

print_header "📝 CREANDO .gitignore"

cat > "$PROJECT_DIR/.gitignore" << 'EOF'

Dependencias

node_modules/
package-lock.json
yarn.lock

Variables de entorno

.env
.env.local
.env.*.local

Logs

logs/
.log
npm-debug.log
yarn-debug.log*
yarn-error.log*

Sistema operativo

.DS_Store
Thumbs.db

IDE

.vscode/
.idea/
*.swp
*.swo

Build

dist/
build/

Backup

*.backup
*.bak
EOF

print_success ".gitignore creado"

============ CREAR ARCHIVO DE PRUEBA ============

print_header "🧪 CREANDO TEST DE API"

mkdir -p "$PROJECT_DIR/test"
cat > "$PROJECT_DIR/test/api-test.sh" << 'EOF'
#!/bin/bash

Prueba rápida de la API

BASE_URL="http://localhost:3000/api"

echo "🧪 Probando endpoints de la API..."

Test 1: Health

echo "1️⃣ Health Check:"
curl -s $BASE_URL/health | json_pp
echo ""

Test 2: Project

echo "2️⃣ Proyecto:"
curl -s $BASE_URL/project | json_pp | head -10
echo "..."

Test 3: Levels

echo "3️⃣ Niveles:"
curl -s $BASE_URL/levels | json_pp | head -10
echo "..."

Test 4: Tour

echo "4️⃣ Tour - Paso 1:"
curl -s $BASE_URL/tour/1 | json_pp | head -10
echo "..."

echo "✅ Pruebas completadas"
EOF

chmod +x "$PROJECT_DIR/test/api-test.sh"
print_success "test/api-test.sh creado"

============ RESUMEN FINAL ============

print_header "🎉 PROYECTO GENERADO EXITOSAMENTE"

echo -e "${GREEN}📂 Directorio:${NC} $PROJECT_DIR/"
echo ""
echo -e "${BLUE}📊 Resumen de archivos:${NC}"
tree -L 3 "$PROJECT_DIR" 2>/dev/null || ls -la "$PROJECT_DIR"

echo ""
echo -e "${YELLOW}🚀 Pasos para usar:${NC}"
echo "1. cd $PROJECT_DIR"
echo "2. ./setup.sh         # Instalar dependencias"
echo "3. npm start          # Iniciar servidor"
echo ""
echo -e "${BLUE}📋 O desde la raíz:${NC}"
echo "./iniciar.sh          # Inicia todo automáticamente"
echo "./limpiar.sh          # Limpia node_modules"
echo ""
echo -e "${GREEN}✅ ¡Todo listo! Tu backend de Torre MONTERRA está preparado.${NC}"
echo "=========================================="

============ VERIFICACIÓN FINAL ============

if [ -f "$PROJECT_DIR/server.js" ]; then
    echo -e "${GREEN}✅ server.js existe${NC}"
else
    echo -e "${RED}❌ server.js no encontrado - revisa el archivo MD${NC}"
fi

if [ -f "$PROJECT_DIR/package.json" ]; then
    echo -e "${GREEN}✅ package.json existe${NC}"
else
    echo -e "${RED}❌ package.json no encontrado - revisa el archivo MD${NC}"
fi

echo ""
echo -e "${BLUE}💡 Comandos útiles:${NC}"
echo "  cd $PROJECT_DIR && npm install && npm start"
echo "  curl http://localhost:3000/api/health"
echo ""

```

---

## 📝 **Cómo usar este script**

1. **Guarda** el script como `convertir.sh`
2. **Asegúrate** de tener `backend.md` en el mismo directorio
3. **Ejecuta**:
```bash
chmod +x convertir.sh
./convertir.sh
```

4. Resultado: Se creará la carpeta torre-monterra-backend/ con toda la estructura del proyecto

---

🎯 Lo que hace el script

Función Descripción
✅ Extrae todos los bloques de código JavaScript, JSON, env, markdown
✅ Crea estructura de carpetas routes/, data/, frontend/
✅ Genera archivos individuales server.js, package.json, .env, etc.
✅ Crea scripts auxiliares setup.sh, iniciar.sh, limpiar.sh
✅ Añade .gitignore Para control de versiones
✅ Incluye test de API Para verificar endpoints
✅ Colores en output Mejor legibilidad
✅ Manejo de errores Detiene ejecución si falla

---

🚀 Después de ejecutar

```bash
# Entrar al proyecto
cd torre-monterra-backend

# Instalar dependencias
./setup.sh
# o
npm install

# Iniciar servidor
npm start

# Probar API
curl http://localhost:3000/api/health
