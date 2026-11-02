# Tutorial: Despliegue de Torremonterra con GitHub Pages + Tailscale Funnel

Este tutorial explica paso a paso cómo publicar la interfaz estática del **Visor de Taller** en **GitHub Pages** y conectarla con el **backend Flask** que corre en la **Raspberry Pi** a través de **Tailscale Funnel**.

---

## 📋 Requisitos previos

| Componente | Versión mínima | Cómo verificar |
|------------|----------------|----------------|
| Python | 3.11 | `python3 --version` |
| pip | 23.x | `pip --version` |
| Git | 2.40 | `git --version` |
| Tailscale | 1.60 | `tailscale version` |
| Flask | 3.0 | `pip list \| grep Flask` |
| Navegador moderno | — | Chrome/Firefox/Edge/Safari |

---

## 1️⃣ Preparar la Raspberry Pi (Backend)

### 1.1 Clonar el repositorio en la Pi

```bash
# En la Pi (ejecuta como usuario pi)
cd /home/pi
git clone ssh://pi@192.168.1.24/home/pi/workspace_local/torremonterra.git
cd torremonterra
git checkout main   # o la rama que contenga los cambios finales
```

### 1.2 Crear entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt   # si existe
# Mínimo necesario:
pip install flask flask-cors
```

### 1.3 Verificar configuración del backend

El archivo `server/app.py` ya incluye:

- `host='0.0.0.0', port=5000` en `app.run()`.
- CORS habilitado para `*.github.io` y `*.githubusercontent.com`.
- Rutas de plantillas y estáticos configuradas.

```python
# Fragmento relevante
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/frontend', template_folder=TEMPLATE_DIR)
CORS(app, origins=["https://*.github.io", "https://*.githubusercontent.com"])
```

### 1.4 Iniciar Flask (mantén esta terminal abierta)

```bash
cd /home/pi/torremonterra
source .venv/bin/activate
python -m server.app
```

Deberías ver:
```
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

---

## 2️⃣ Configurar Tailscale y habilitar Funnel

### 2.1 Instalar Tailscale (si no está)

```bash
curl -fsSL https://tailscale.com/install.sh | sudo sh
sudo tailscale up
# Sigue el enlace que aparece en la consola para autenticar la Pi.
```

### 2.2 Comprobar que la Pi está en la red Tailscale

```bash
tailscale status
# Debe mostrar una IP 100.x.x.x y estado "active"
```

### 2.3 Habilitar Funnel para el puerto 5000 (HTTPS + auth automático)

```bash
# Opción recomendada: HTTPS terminado en Cloudflare + auth Tailscale
sudo tailscale serve --https=5000 --auth=auto
# O, forma explícita:
# sudo tailscale serve --allow-unauthenticated=false --port 5000
```

### 2.4 Obtener la URL pública de Funnel

```bash
tailscale funnel list
# Ejemplo de salida:
# Port 5000: https://100.101.102.103.trycloudflare.com
```

> **Guarda esa URL** (p. ej. `https://100.101.102.103.trycloudflare.com`). La necesitarás en el frontend.

---

## 3️⃣ Preparar el Frontend Estático para GitHub Pages

### 3.1 Rama dedicada `gh-pages-visor`

En tu máquina de desarrollo (donde tienes el repo clonado):

```bash
git checkout main
git checkout -b gh-pages-visor
```

### 3.2 Copiar archivos estáticos a la raíz de la rama

```bash
# Asegúrate de estar en la raíz del repo
mkdir -p static/css static/js static/images

# Copia CSS y JS del frontend original
cp frontend/css/styles.css static/css/
cp frontend/js/app.js static/js/

# Copia imágenes usadas por el visor
cp frontend/visor/screen.png static/images/

# Copia la plantilla Jinja como HTML estático (sin tags Jinja)
cp templates/visor.html index.html
```

### 3.3 Eliminar referencias a `{{ url_for(...) }}` en `index.html`

Abre `index.html` y reemplaza **todas** las ocurrencias:

| Antes (Jinja) | Después (relativo) |
|---------------|---------------------|
| `{{ url_for('static', filename='css/styles.css') }}` | `static/css/styles.css` |
| `{{ url_for('static', filename='js/app.js') }}` | `static/js/app.js` |
| `{{ url_for('static', filename='images/screen.png') }}` | `static/images/screen.png` |

> Puedes hacerlo con `sed`:
> ```bash
> sed -i "s/{{ url_for('static', filename='\([^']*\)') }}/static\/\1/g" index.html
> ```

### 3.4 Apuntar las llamadas `fetch` a la URL de Funnel

Edita `static/js/app.js` (o el archivo JS que haga peticiones al API) y añade al inicio:

```js
// URL pública de Funnel (copia la que obtuviste con `tailscale funnel list`)
const PI_URL = "https://100.101.102.103.trycloudflare.com";
```

Luego sustituye cada `fetch('/api/...` por `fetch(`${PI_URL}/api/...`)`:

```js
// Antes
fetch('/api/guardar_estado', { ... })

// Después
fetch(`${PI_URL}/api/guardar_estado`, { ... })
```

> Haz lo mismo para `/api/guardar_especificacion`, `/api/calcular`, etc.

### 3.5 Commit y push de la rama

```bash
git add index.html static/
git commit -m "Add static GH Pages assets for visor + point API to Funnel"
git push github gh-pages-visor
```

---

## 4️⃣ Activar GitHub Pages

1. Abre el repositorio en GitHub: <https://github.com/mundocancel/torremonterra>
2. Ve a **Settings → Pages** (en la barra lateral izquierda).
3. En **Source**, selecciona:
   - **Branch**: `gh-pages-visor`
   - **Folder**: `/ (root)`
4. Haz clic en **Save**.
5. Espera ~1-2 minutos. GitHub mostrará la URL, p.ej.:
   ```
   https://mundocancel.github.io/torremonterra/
   ```

---

## 5️⃣ Probar la integración completa

| Qué probar | Cómo hacerlo | Qué esperar |
|------------|--------------|-------------|
| **Carga de la UI** | Abre la URL de GitHub Pages en el navegador. | Se ve la barra superior, tabs, canvas del visor, panel lateral. |
| **Marcar un corte** | Haz clic en un elemento del croquis → botón "Marcar" / checkbox. | La acción se guarda localmente y se envía `POST` al backend. |
| **Ver request en la Pi** | En la terminal donde corre Flask, observa los logs. | Debe aparecer `POST /api/guardar_estado` con código 200. |
| **Revisar consola del navegador** | F12 → Console / Network. | No errores de CORS; respuesta JSON `{ "ok": true }`. |
| **Recargar página** | F5 en la UI de GitHub Pages. | Los cortes marcados persisten (si el backend los guarda en BD). |

---

## 6️⃣ Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `ERR_CONNECTION_REFUSED` al abrir la URL de Funnel | Funnel no está activo o Flask no escucha en `0.0.0.0`. | `sudo tailscale serve --https=5000 --auth=auto` y verifica `python -m server.app`. |
| Error **CORS** en consola del navegador | Falta origen en `CORS(app, origins=...)`. | Añade `https://mundocancel.github.io` (o `https://*.github.io`) y reinicia Flask. |
| `404 Not Found` en `static/...` | Rutas en `index.html` no coinciden con la estructura de `gh-pages`. | Verifica que `index.html` use rutas relativas `static/...` y que los archivos existan en la rama. |
| Los datos no persisten al recargar | Backend no guarda en BD o BD no inicializada. | Revisa `services.guardar_estado_pieza` y que `taller.db` exista en `data/`. |
| `tailscale funnel list` no muestra nada | Funnel no habilitado. | Ejecuta `sudo tailscale serve ...` y luego `tailscale funnel list`. |

---

## 7️⃣ Comandos de referencia rápida

```bash
# --- En la Pi ---
# Iniciar backend
cd /home/pi/torremonterra && source .venv/bin/activate && python -m server.app

# Habilitar / deshabilitar Funnel
sudo tailscale serve --https=5000 --auth=auto
sudo tailscale funnel disable 5000

# Ver URL pública
tailscale funnel list

# Ver estado Tailscale
tailscale status

# --- En tu máquina de desarrollo ---
# Subir cambios a GH Pages
git checkout gh-pages-visor
# (edita index.html / static/js/app.js)
git add . && git commit -m "Update static UI" && git push github gh-pages-visor

# Ver logs de GitHub Pages (Actions)
# https://github.com/mundocancel/torremonterra/actions
```

---

## 8️⃣ Seguridad y buenas prácticas

1. **Autenticación Tailscale** (`--auth=auto`) asegura que solo miembros de tu red puedan llamar al API, aunque la UI sea pública.
2. **HTTPS end-to-end**: GitHub Pages (HTTPS) → Funnel (HTTPS en Cloudflare) → Flask (HTTP local). El tráfico nunca viaja en claro por internet.
3. **Rate-limiting** (opcional): instala `flask-limiter` para proteger endpoints públicos.
4. **Tokens de API** (opcional): añade un header `X-API-Key` validado en `services.py` para una capa extra.
5. **Separación de ramas**: mantén `main` para código del backend y `gh-pages-visor` solo para assets estáticos.

---

## 9️⃣ Próximos pasos sugeridos

- [ ] Añadir **CI/CD** (GitHub Actions) que, al hacer push a `main`, genere automáticamente la rama `gh-pages-visor` con los assets actualizados.
- [ ] Implementar **WebSockets** (Socket.IO) para actualizaciones en tiempo real del estado de cortes entre varios operarios.
- [ ] Crear **tests automatizados** (pytest + Playwright) que verifiquen la UI contra la Pi en un entorno de staging.
- [ ] Documentar **API** con OpenAPI/Swagger (`flask-smorest` o `apispec`).

---

## 📚 Referencias

- **Tailscale Funnel**: <https://tailscale.com/kb/1223/funnel>
- **GitHub Pages**: <https://docs.github.com/en/pages>
- **Flask CORS**: <https://flask-cors.readthedocs.io/>
- **Flask tutorial oficial**: <https://flask.palletsprojects.com/en/stable/tutorial/>

---

> **Última actualización**: 2026-09-07  
> **Autor**: David Plascencia (Y4otzin)  
> **Repo**: <https://github.com/mundocancel/torremonterra>