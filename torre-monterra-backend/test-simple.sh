#!/bin/bash
# Tests simples sin dependencias externas

BASE_URL="http://localhost:3000/api"
PASSED=0
FAILED=0

echo "🧪 Torre MONTERRA - Tests Simples"
echo "=================================="

test_endpoint() {
    local name=$1
    local url=$2
    echo -n "  $name... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 304 ]; then
        echo "✅ OK ($HTTP_CODE)"
        ((PASSED++))
        return 0
    else
        echo "❌ FAIL ($HTTP_CODE)"
        ((FAILED++))
        return 1
    fi
}

# Ejecutar tests
test_endpoint "Health Check" "$BASE_URL/health"
test_endpoint "Project Info" "$BASE_URL/project"
test_endpoint "Levels List" "$BASE_URL/levels"
test_endpoint "Materials" "$BASE_URL/materials"
test_endpoint "Components" "$BASE_URL/components"
test_endpoint "Tour" "$BASE_URL/tour"
test_endpoint "Drawings" "$BASE_URL/drawings"
test_endpoint "Search" "$BASE_URL/search?q=puerta"

echo ""
echo "=================================="
echo "📊 RESULTADOS:"
echo "  ✅ Pasaron: $PASSED"
echo "  ❌ Fallaron: $FAILED"
TOTAL=$((PASSED+FAILED))
echo "  📝 Total: $TOTAL"

if [ $FAILED -eq 0 ]; then
    echo "🎉 ¡TODAS LAS PRUEBAS PASARON!"
else
    echo "⚠️  Algunas pruebas fallaron"
fi
