# 🏗️ Backend Torre MONTERRA - API REST

He creado un backend completo en **Node.js + Express** que expone todos los datos arquitectónicos del proyecto mediante una API REST estructurada.

## 📁 Estructura del Proyecto

```
torre-monterra/
├── backend/
│   ├── server.js              # Servidor principal
│   ├── package.json           # Dependencias
│   ├── routes/
│   │   └── api.js            # Rutas de la API
│   ├── data/
│   │   ├── project.json      # Datos del proyecto
│   │   ├── materials.json    # Materiales y acabados
│   │   ├── components.json   # Puertas, ventanas, herrería
│   │   └── tour.json         # Pasos del tour
│   └── README.md
└── frontend/
    └── index.html            # Modelo 3D (ya creado)
```

---

## 📄 1. `package.json`

```json
{
  "name": "torre-monterra-backend",
  "version": "1.0.0",
  "description": "API REST para el proyecto arquitectónico Torre MONTERRA",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "compression": "^1.7.4"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": ">=16.0.0"
  }
}
```

---

## 📄 2. `server.js` - Servidor Principal

```javascript
/**
 * ============================================================
 * TORRE MONTERRA - Backend API
 * Proyecto Arquitectónico V2
 * Clave: MON-EDI-TT-ARQ
 * Fecha: 29-Nov-2024
 * ============================================================
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const compression = require('compression');
const path = require('path');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;

// ============ MIDDLEWARE ============
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Servir archivos estáticos del frontend
app.use(express.static(path.join(__dirname, '../frontend')));

// Logger de requests
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(
      `[${new Date().toISOString()}] ${req.method} ${req.originalUrl} - ${res.statusCode} (${duration}ms)`
    );
  });
  next();
});

// ============ RUTAS API ============
app.use('/api', apiRoutes);

// ============ RUTA PRINCIPAL ============
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// ============ MANEJO DE ERRORES ============
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint no encontrado',
    availableEndpoints: [
      'GET /api/project',
      'GET /api/levels',
      'GET /api/levels/:id',
      'GET /api/materials',
      'GET /api/materials/:type',
      'GET /api/components',
      'GET /api/components/:type',
      'GET /api/tour',
      'GET /api/tour/:step',
      'GET /api/drawings',
      'GET /api/health'
    ]
  });
});

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: 'Error interno del servidor',
    message: err.message
  });
});

// ============ INICIO DEL SERVIDOR ============
app.listen(PORT, () => {
  console.log('\n========================================');
  console.log('🏢 TORRE MONTERRA - Backend API');
  console.log('========================================');
  console.log(`🚀 Servidor corriendo en: http://localhost:${PORT}`);
  console.log(`📡 API disponible en: http://localhost:${PORT}/api`);
  console.log(`🏗️  Frontend en: http://localhost:${PORT}`);
  console.log('========================================\n');
});

module.exports = app;
```

---

## 📄 3. `routes/api.js` - Rutas de la API

```javascript
/**
 * ============================================================
 * RUTAS API - Torre MONTERRA
 * Endpoints organizados por categoría arquitectónica
 * ============================================================
 */

const express = require('express');
const router = express.Router();

// Cargar datos
const projectData = require('../data/project.json');
const materialsData = require('../data/materials.json');
const componentsData = require('../data/components.json');
const tourData = require('../data/tour.json');

// ============ HEALTH CHECK ============
router.get('/health', (req, res) => {
  res.json({
    success: true,
    status: 'online',
    project: 'Torre MONTERRA',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    endpoints: {
      project: '/api/project',
      levels: '/api/levels',
      materials: '/api/materials',
      components: '/api/components',
      tour: '/api/tour',
      drawings: '/api/drawings'
    }
  });
});

// ============ PROJECT INFO ============
router.get('/project', (req, res) => {
  res.json({
    success: true,
    data: projectData.info
  });
});

// ============ LEVELS (NIVELES) ============
router.get('/levels', (req, res) => {
  res.json({
    success: true,
    count: projectData.levels.length,
    data: projectData.levels
  });
});

router.get('/levels/:id', (req, res) => {
  const level = projectData.levels.find(l => l.id === req.params.id);
  if (!level) {
    return res.status(404).json({
      success: false,
      error: 'Nivel no encontrado',
      available: projectData.levels.map(l => l.id)
    });
  }
  res.json({ success: true, data: level });
});

// ============ MATERIALS (MATERIALES) ============
router.get('/materials', (req, res) => {
  res.json({
    success: true,
    categories: Object.keys(materialsData),
    data: materialsData
  });
});

router.get('/materials/:type', (req, res) => {
  const type = req.params.type;
  if (!materialsData[type]) {
    return res.status(404).json({
      success: false,
      error: `Categoría '${type}' no encontrada`,
      available: Object.keys(materialsData)
    });
  }
  res.json({
    success: true,
    type,
    count: materialsData[type].length,
    data: materialsData[type]
  });
});

// ============ COMPONENTS (COMPONENTES) ============
router.get('/components', (req, res) => {
  res.json({
    success: true,
    categories: Object.keys(componentsData),
    data: componentsData
  });
});

router.get('/components/:type', (req, res) => {
  const type = req.params.type;
  const validTypes = ['doors', 'windows', 'ironwork', 'equipment', 'bathroom_accessories'];
  
  if (!validTypes.includes(type)) {
    return res.status(404).json({
      success: false,
      error: `Tipo '${type}' no encontrado`,
      available: validTypes
    });
  }
  
  res.json({
    success: true,
    type,
    count: componentsData[type].length,
    data: componentsData[type]
  });
});

router.get('/components/:type/:id', (req, res) => {
  const { type, id } = req.params;
  const item = componentsData[type]?.find(c => c.id === id);
  
  if (!item) {
    return res.status(404).json({
      success: false,
      error: `Componente '${id}' no encontrado en '${type}'`
    });
  }
  res.json({ success: true, data: item });
});

// ============ TOUR (TOUR GUIADO) ============
router.get('/tour', (req, res) => {
  res.json({
    success: true,
    totalSteps: tourData.steps.length,
    data: tourData
  });
});

router.get('/tour/:step', (req, res) => {
  const stepNum = parseInt(req.params.step);
  const step = tourData.steps.find(s => s.step === stepNum);
  
  if (!step) {
    return res.status(404).json({
      success: false,
      error: 'Paso no encontrado',
      available: tourData.steps.map(s => s.step)
    });
  }
  res.json({ success: true, data: step });
});

// ============ DRAWINGS (PLANOS) ============
router.get('/drawings', (req, res) => {
  res.json({
    success: true,
    count: projectData.drawings.length,
    data: projectData.drawings
  });
});

// ============ SEARCH (BÚSQUEDA GLOBAL) ============
router.get('/search', (req, res) => {
  const query = req.query.q?.toLowerCase();
  if (!query) {
    return res.status(400).json({
      success: false,
      error: 'Parámetro de búsqueda "q" requerido'
    });
  }

  const results = {
    materials: [],
    components: [],
    levels: []
  };

  // Buscar en materiales
  Object.entries(materialsData).forEach(([category, items]) => {
    items.forEach(item => {
      const text = JSON.stringify(item).toLowerCase();
      if (text.includes(query)) {
        results.materials.push({ ...item, category });
      }
    });
  });

  // Buscar en componentes
  Object.entries(componentsData).forEach(([type, items]) => {
    items.forEach(item => {
      const text = JSON.stringify(item).toLowerCase();
      if (text.includes(query)) {
        results.components.push({ ...item, type });
      }
    });
  });

  // Buscar en niveles
  projectData.levels.forEach(level => {
    const text = JSON.stringify(level).toLowerCase();
    if (text.includes(query)) {
      results.levels.push(level);
    }
  });

  res.json({
    success: true,
    query,
    totalResults: results.materials.length + results.components.length + results.levels.length,
    results
  });
});

module.exports = router;
```

---

## 📄 4. `data/project.json` - Datos del Proyecto

```json
{
  "info": {
    "name": "Torre MONTERRA",
    "project": "Proyecto Arquitectónico V2",
    "location": "Monterra",
    "type": "Edificio Departamentos",
    "key": "MON-EDI-TT-ARQ",
    "date": "29-Nov-2024",
    "version": "01",
    "revision": "01",
    "units": "Metros",
    "scale": "1:40 / 1:50 / 1:75",
    "designer": "INDEM | Innovación en Desarrollos",
    "website": "www.indemexico.com",
    "dimensions": {
      "width": 11.72,
      "depth": 10.33,
      "totalHeight": 13.65,
      "floorArea": 121.9,
      "units": "m / m²"
    },
    "levelsSummary": {
      "basement": "Acceso NPT +0.05m",
      "groundFloor": "Planta Baja NPT +0.65m",
      "typicalFloors": "Niveles 1-4",
      "rooftop": "Azotea NPT +13.65m",
      "totalLevels": 6
    }
  },
  "levels": [
    {
      "id": "pb",
      "name": "Planta Baja",
      "npt": 0.65,
      "height": 2.60,
      "description": "Acceso principal a torre con puerta doble hoja WPC",
      "drawing": "ARQ-01",
      "features": [
        "Acceso principal P-04 WPC Nogal",
        "Cerradura TECDOFY H5H",
        "Piso LAMOSA Sinatra Gris",
        "Muro exterior Piedra Georgetown"
      ]
    },
    {
      "id": "n1",
      "name": "Nivel 1",
      "npt": 3.25,
      "height": 2.60,
      "description": "Departamentos tipo con 2 recámaras",
      "drawing": "ARQ-02",
      "features": [
        "Piso CASTEL Geo Silver 60x60cm",
        "Cancelería aluminio 3\" negro",
        "Closet MDF Arauco Monarca",
        "Cocina cubierta Lu Marquina"
      ]
    },
    {
      "id": "n2",
      "name": "Nivel 2",
      "npt": 5.85,
      "height": 2.60,
      "description": "Departamentos con balcones en L",
      "drawing": "ARQ-03",
      "features": [
        "Balcones en L laterales",
        "Barandales acero Pimienta K5-12",
        "H-02/H-03 barandales tubulares",
        "Cancelería V-05 a V-09"
      ]
    },
    {
      "id": "n3",
      "name": "Nivel 3",
      "npt": 8.45,
      "height": 2.60,
      "description": "Nivel intermedio con balcones",
      "drawing": "ARQ-04",
      "features": [
        "Balcones en L",
        "Muros pasta CEMIX Reserved White",
        "Ventanales aluminio negro cristal 6mm",
        "Accesorios baño DICA cromo"
      ]
    },
    {
      "id": "n4",
      "name": "Nivel 4",
      "npt": 11.05,
      "height": 2.60,
      "description": "Último nivel habitable con acabados premium",
      "drawing": "ARQ-05",
      "features": [
        "Molduras concreto colado en sitio",
        "Pintura PRISA Harrison Gray AP46-5",
        "Acabados caracoleados",
        "Acceso a azotea"
      ]
    },
    {
      "id": "azotea",
      "name": "Azotea",
      "npt": 13.65,
      "height": 0.80,
      "description": "Cubierta con impermeabilizante y accesos",
      "drawing": "ARQ-06",
      "features": [
        "Impermeabilizante IMPAC 3.5mm",
        "Pretil perimetral",
        "Escotilla H-08 acero Portafolio",
        "Escalera marina H-07 tubular"
      ]
    }
  ],
  "drawings": [
    { "sheet": "ARQ-00", "title": "Especificaciones", "scale": "-" },
    { "sheet": "ARQ-01", "title": "Planta Baja", "scale": "1:40" },
    { "sheet": "ARQ-02", "title": "Nivel 1", "scale": "1:40" },
    { "sheet": "ARQ-03", "title": "Nivel 2", "scale": "1:40" },
    { "sheet": "ARQ-04", "title": "Nivel 3", "scale": "1:40" },
    { "sheet": "ARQ-05", "title": "Nivel 4", "scale": "1:40" },
    { "sheet": "ARQ-06", "title": "Azotea", "scale": "1:40" },
    { "sheet": "ARQ-07", "title": "Alzado Frontal", "scale": "1:50" },
    { "sheet": "ARQ-08", "title": "Alzado Posterior", "scale": "1:50" },
    { "sheet": "ARQ-09", "title": "Alzado Lateral Derecho", "scale": "1:50" },
    { "sheet": "ARQ-10", "title": "Alzado Lateral Izquierdo", "scale": "1:50" },
    { "sheet": "ARQ-11", "title": "Sección X-1", "scale": "1:50" },
    { "sheet": "ARQ-12", "title": "Sección X-2", "scale": "1:50" },
    { "sheet": "ARQ-13", "title": "Sección Y-1", "scale": "1:50" },
    { "sheet": "ARQ-14", "title": "Sección Y-2", "scale": "1:50" },
    { "sheet": "ARQ-15", "title": "Balcones L Derecho", "scale": "1:40" },
    { "sheet": "ARQ-15.1", "title": "Balcones L Izquierdo", "scale": "1:40" },
    { "sheet": "ARQ-15.2", "title": "Torres Colindantes", "scale": "1:40" },
    { "sheet": "ARQ-16", "title": "Acabados PB y N1", "scale": "1:50" },
    { "sheet": "ARQ-17", "title": "Acabados N2 y N3", "scale": "1:50" },
    { "sheet": "ARQ-18", "title": "Acabados N4 y Azotea", "scale": "1:50" },
    { "sheet": "ARQ-19", "title": "Alzado Frontal Acabados", "scale": "1:50" },
    { "sheet": "ARQ-20", "title": "Alzado Posterior Acabados", "scale": "1:50" },
    { "sheet": "ARQ-21", "title": "Alzado Lateral Der. Acabados", "scale": "1:50" },
    { "sheet": "ARQ-22", "title": "Alzado Lateral Izq. Acabados", "scale": "1:50" },
    { "sheet": "ARQ-23", "title": "Cancelerías PB, N1, N2", "scale": "1:75" },
    { "sheet": "ARQ-24", "title": "Cancelerías N3 y N4", "scale": "1:75" },
    { "sheet": "ARQ-25", "title": "Puertas PB, N1, N2", "scale": "1:75" },
    { "sheet": "ARQ-26", "title": "Puertas N3 y N4", "scale": "1:75" },
    { "sheet": "ARQ-27", "title": "Herrerías PB", "scale": "1:75" },
    { "sheet": "ARQ-28", "title": "Herrerías N1, N2, N3", "scale": "1:75" },
    { "sheet": "ARQ-29", "title": "Herrerías N4 y Azotea", "scale": "1:75" },
    { "sheet": "ARQ-30", "title": "Equipamiento PB, N1, N2", "scale": "1:75" },
    { "sheet": "ARQ-31", "title": "Equipamiento N3 y N4", "scale": "1:75" },
    { "sheet": "ARQ-32", "title": "Detalles de Baños", "scale": "1:20" },
    { "sheet": "ARQ-33", "title": "Señalética", "scale": "1:75" }
  ]
}
```

---

## 📄 5. `data/materials.json` - Materiales

```json
{
  "floors": [
    {
      "id": "S-01",
      "name": "Piso Interior Departamentos",
      "brand": "CASTEL",
      "model": "Geo Silver",
      "format": "60x60 cm",
      "color": "Silver",
      "joint": "Mínima 3mm color TAN",
      "location": "Interior departamentos",
      "hexColor": "#b8b8b8"
    },
    {
      "id": "S-02",
      "name": "Pasillos y Escalera",
      "brand": "LAMOSA",
      "model": "Sinatra",
      "format": "44x44 cm",
      "color": "Gris",
      "adhesive": "PEGAPISO INTERCERAMIC",
      "joint": "Arena color BONE",
      "location": "Pasillos y escaleras",
      "hexColor": "#8a8a8a"
    },
    {
      "id": "S-03",
      "name": "Piso Baños",
      "brand": "PORCELANITE",
      "model": "Bramasole Bone",
      "format": "30x60 cm",
      "color": "Bone",
      "joint": "Mínima +/- 3mm color BONE",
      "location": "Baños",
      "hexColor": "#d4c4a8"
    },
    {
      "id": "S-04",
      "name": "Impermeabilizante",
      "brand": "IMPAC",
      "model": "Hogar Fibra Poliéster",
      "thickness": "3.5mm",
      "color": "Blanco con grávilla",
      "location": "Azotea",
      "hexColor": "#f5f5f5"
    }
  ],
  "walls": [
    {
      "id": "W-01",
      "name": "Muro Interior Departamentos",
      "system": "Aplanado pasta CEMIX ADEBLOK PLUS",
      "finish": "Caracoleado con grano especial",
      "thickness": "+/- 2cm",
      "sealer": "Sellador 5X1 Reforzado (1 mano)",
      "paint": "PRISA Reserved White AP14-2 (2 manos)",
      "paintLine": "RIVINOL",
      "location": "Interior",
      "hexColor": "#e8e4dc"
    },
    {
      "id": "W-02",
      "name": "Muro Exterior",
      "system": "Aplanado pasta CEMIX ADEBLOK Constructor",
      "finish": "Caracoleado con grano especial",
      "sealer": "Sellador 5X1 Reforzado (1 mano)",
      "paint": "PRISA Ivory Too AP57-1 (2 manos)",
      "paintLine": "RIVINOL Uso Profesional",
      "location": "Exterior",
      "hexColor": "#e5dcc8"
    },
    {
      "id": "W-04",
      "name": "Muro Recubierto Piedra",
      "system": "Muro de concreto",
      "finish": "Piedra Georgetown",
      "brand": "INTERSTONE",
      "waterproofing": "FESTER CR-66",
      "location": "Exterior",
      "hexColor": "#a89882"
    },
    {
      "id": "W-09",
      "name": "Columnas de Concreto",
      "size": "30x30 cm",
      "system": "Aplanado pasta CEMIX ADEBLOK Constructor",
      "finish": "Caracoleado",
      "paint": "PRISA Harrison Gray AP46-5 (2 manos)",
      "paintLine": "RIVINOL Uso Profesional",
      "location": "Columnas exteriores",
      "hexColor": "#6b6f75"
    }
  ],
  "ceilings": [
    {
      "id": "B-01",
      "name": "Bóveda Interior",
      "system": "Aplanado pasta caracoleado",
      "thickness": "+/- 2cm",
      "sealer": "Sellador 5X1 Reforzado (1 mano)",
      "paint": "PRISA Hush White AP5-2 (2 manos)",
      "altPaint": "COMEX Foco J5-02",
      "location": "Interior departamentos",
      "hexColor": "#f5f1e8"
    },
    {
      "id": "B-02",
      "name": "Losa Concreto Azotea",
      "system": "Impermeabilizante IMPAC",
      "model": "Asfalto Modificado 3.5 POL GB",
      "color": "Blanco",
      "location": "Azotea y exterior",
      "hexColor": "#ffffff"
    }
  ]
}
```

---

## 📄 6. `data/components.json` - Componentes

```json
{
  "doors": [
    {
      "id": "P-01",
      "name": "Puerta Ingreso Principal",
      "material": "Lámina CAPECO",
      "model": "Ébano",
      "frame": "Metálico color negro o chocolate oscuro",
      "lock": "DEXTER PP100 WIFI",
      "stopper": "Tope Catarina",
      "dimensions": "0.96 x 2.17 m",
      "location": "Departamentos"
    },
    {
      "id": "P-02",
      "name": "Puerta Recámara",
      "material": "EUCAPLAC",
      "color": "Blanco Arena",
      "frame": "Metálico blanco",
      "lock": "HYM Manija Redonda 00101637",
      "stopper": "Tope Catarina",
      "dimensions": "0.86 x 2.14 m"
    },
    {
      "id": "P-03",
      "name": "Puerta Baño",
      "material": "EUCAPLAC",
      "color": "Blanco Arena",
      "frame": "Metálico blanco",
      "lock": "HYM Manija Redonda 00101637",
      "dimensions": "0.76 x 2.14 m"
    },
    {
      "id": "P-04",
      "name": "Ingreso Principal Torre",
      "type": "Doble hoja con fijo intermedio",
      "frame": "PTR 2\"x2\"x3/4\"",
      "cladding": "WPC Exterior color Nogal SIN-12",
      "lock": "TECDOFY H5H (solo hoja izquierda)",
      "stopper": "HYM Tope Níquel con Imán",
      "location": "Acceso principal a torre"
    },
    {
      "id": "P-05",
      "name": "Puerta Abatible Aluminio",
      "material": "Aluminio 3\" color negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "0.97 x 2.14 m"
    },
    {
      "id": "P-06",
      "name": "Puerta Abatible Aluminio",
      "material": "Aluminio 3\" color negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "0.99 x 2.14 m"
    }
  ],
  "windows": [
    {
      "id": "V-01",
      "name": "Ventanal 1 Fijo + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "1.99 x 2.40 m",
      "type": "Fijo + Corrediza"
    },
    {
      "id": "V-02",
      "name": "Ventanal 1 Fijo + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "1.25 x 1.60 m"
    },
    {
      "id": "V-03",
      "name": "Ventanal 1 Fijo + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "1.23 x 2.40 m"
    },
    {
      "id": "V-04",
      "name": "Ventana Louver",
      "type": "Louver con 2 rejillas",
      "brand": "REFLECTO",
      "material": "Aluminio negro",
      "line": "Cuprum Panorama",
      "output": "Salida secadora 4\"",
      "dimensions": "0.74 x 0.40 m"
    },
    {
      "id": "V-05",
      "name": "Ventanal 1 Fijo + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "1.60 x 1.99 m"
    },
    {
      "id": "V-06",
      "name": "Ventanal 3 Fijos + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "1.99 x 2.40 m"
    },
    {
      "id": "V-07",
      "name": "Ventanal Tipo Sifón",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm con película privacidad",
      "dimensions": "0.33 x 0.40 m"
    },
    {
      "id": "V-08",
      "name": "Ventanal 3 Fijos + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "0.97 x 2.40 m"
    },
    {
      "id": "V-09",
      "name": "Ventanal 3 Fijos + 1 Corrediza",
      "material": "Aluminio 3\" negro",
      "glass": "Cristal claro 6mm",
      "dimensions": "0.99 x 2.40 m"
    },
    {
      "id": "CAN-01",
      "name": "Cancel de Baño",
      "type": "1 Fijo + 1 Corredizo",
      "glass": "Cristal claro templado 6mm"
    }
  ],
  "ironwork": [
    {
      "id": "H-01",
      "name": "Puerta Doble Abatible Acero",
      "profiles": "Tubular cuadrado 1.5\"x1.5\" laterales",
      "rail": "Solera 1.5\"x1/4\" horizontal",
      "intermediates": "Perfiles verticales 1/2\"",
      "color": "Pimienta K5-12",
      "paint": "COMEX Línea Acqua"
    },
    {
      "id": "H-02",
      "name": "Barandal Acero",
      "profiles": "Tubular cuadrado 1.5\"x1.5\"",
      "rail": "Solera 1.5\"x1/4\"",
      "intermediates": "Perfiles verticales 1/2\"",
      "color": "Pimienta K5-12",
      "paint": "COMEX Línea Acqua",
      "location": "Balcones"
    },
    {
      "id": "H-03",
      "name": "Barandal Acero",
      "spec": "Igual que H-02",
      "location": "Balcones"
    },
    {
      "id": "H-07",
      "name": "Escalera Marina",
      "material": "Tubular 1\"x1\"",
      "finish": "Fondeado + esmalte semimate",
      "color": "Portafolio 313-06",
      "paint": "COMEX",
      "location": "Acceso a azotea"
    },
    {
      "id": "H-08",
      "name": "Escotilla",
      "frame": "Ángulo 2\"x2\" (3/16\") corte 45°",
      "sheet": "Lámina lisa 1/4\"",
      "finish": "Pasta automotiva en uniones",
      "primer": "Fondo anticorrosivo gris",
      "color": "Portafolio 313-06",
      "paint": "COMEX esmalte semimate"
    },
    {
      "id": "H-09",
      "name": "Puerta Corrediza Aluminio Louver",
      "material": "Aluminio negro 3\"",
      "type": "Con louver"
    },
    {
      "id": "H-10",
      "name": "Barandal Acero",
      "spec": "Igual que H-02",
      "location": "Azotea"
    }
  ],
  "equipment": [
    {
      "id": "EQU-01",
      "name": "Closet Recámara Principal",
      "material": "MDF 16mm con melamina",
      "brand": "ARAUCO",
      "model": "Monarca",
      "handles": "HERRAJES BULNES C3",
      "interior": "Color blanco"
    },
    {
      "id": "EQU-02",
      "name": "Closet Recámara Secundaria",
      "material": "MDF 16mm con melamina",
      "brand": "ARAUCO",
      "model": "Monarca",
      "handles": "HERRAJES BULNES C3"
    },
    {
      "id": "EQU-03",
      "name": "Cocina Integral",
      "upperCabinets": {
        "material": "MDF 15mm melamina ARAUCO Visión",
        "interior": "Melamina blanca semimate"
      },
      "lowerCabinets": {
        "material": "MDF ARAUCO Monarca",
        "interior": "Melamina blanca semimate"
      },
      "countertop": {
        "brand": "KOBER",
        "model": "Lu Marquina Original Q",
        "type": "Sin respaldo"
      },
      "splash": "Lu Marquina MCA. KOBER"
    },
    {
      "id": "EQU-04",
      "name": "Puerta Reforzada Maletero",
      "type": "Doble abatible reforzada",
      "profiles": "2 perfiles por hoja antipandeo",
      "frame": "Melamina ARAUCO Monarca",
      "lock": "Chapa de llave",
      "ventilation": "Rejilla superior"
    },
    {
      "id": "EQU-05",
      "name": "Lavadero",
      "material": "Polietileno",
      "brand": "VERSAPLAS",
      "size": "24x43x64 cm",
      "color": "Gris",
      "model": "Sin pileta",
      "faucet": "Llave nariz",
      "note": "Considerar ménsulas de fijación"
    }
  ],
  "bathroom_accessories": [
    { "id": "BA-01", "name": "Lavamanos", "brand": "SPAZIO", "includes": "Push", "color": "Blanco" },
    { "id": "BA-02", "name": "Monomando", "brand": "CASTEL", "model": "Damasco Alto 3210", "color": "Cromo" },
    { "id": "BA-03", "name": "Regadera", "brand": "DICA", "model": "4538R", "arm": "30cm a pared", "color": "Cromo" },
    { "id": "BA-04", "name": "Gancho Doble", "brand": "DICA", "model": "3300", "color": "Cromo" },
    { "id": "BA-05", "name": "Jabonera", "brand": "DICA", "model": "3300", "color": "Cromo" },
    { "id": "BA-06", "name": "WC One Piece", "brand": "CORONA", "model": "CIMA", "color": "Blanco" },
    { "id": "BA-07", "name": "Portarollo", "brand": "DICA", "model": "3300", "color": "Cromo" },
    { "id": "BA-08", "name": "Toallero Argolla", "brand": "DICA", "model": "3300", "color": "Cromo" },
    { "id": "BA-09", "name": "Manerales", "brand": "DICA", "model": "MCR", "color": "Cromo" },
    { "id": "BA-10", "name": "Portavaso", "brand": "DICA", "model": "3300", "color": "Cromo" },
    { "id": "BA-11", "name": "Vanity", "brand": "ECO", "size": "45x50x15 cm", "material": "MDF 15mm melamina ARAUCO Monarca" }
  ]
}
```

---

## 📄 7. `data/tour.json` - Tour Guiado

```json
{
  "title": "Tour Arquitectónico Torre MONTERRA",
  "description": "Recorrido interactivo por los elementos arquitectónicos del proyecto",
  "totalSteps": 8,
  "steps": [
    {
      "step": 1,
      "title": "Vista General del Edificio",
      "description": "Torre de departamentos con 6 niveles (PB + 4 + Azotea). Altura total: 13.65m. Planta rectangular de 11.72m × 10.33m.",
      "highlights": ["6 Niveles", "13.65m Altura", "121.9 m² Planta"],
      "camera": { "pos": [30, 20, 30], "target": [0, 13, 0] },
      "focus": null,
      "specs": [
        { "label": "Ubicación", "value": "Monterra" },
        { "label": "Tipo", "value": "Edificio Departamentos" },
        { "label": "Clave", "value": "MON-EDI-TT-ARQ" },
        { "label": "Fecha", "value": "29-Nov-2024" }
      ]
    },
    {
      "step": 2,
      "title": "Planta Baja - Acceso Principal",
      "description": "NPT +0.65m. Acceso principal con puerta doble hoja WPC color Nogal (P-04). Cerradura TECDOFY H5H. Piso LAMOSA Sinatra Gris.",
      "highlights": ["NPT +0.65m", "Puerta WPC Nogal", "Cerradura WIFI"],
      "camera": { "pos": [0, 4, 22], "target": [0, 2, 0] },
      "focus": "pb",
      "specs": [
        { "label": "Puerta P-04", "value": "Doble hoja WPC Nogal SIN-12" },
        { "label": "Cerradura", "value": "TECDOFY MOD. H5H" },
        { "label": "Piso", "value": "LAMOSA Sinatra Gris 44x44cm" },
        { "label": "Muro exterior", "value": "Piedra Georgetown INTERSTONE" }
      ]
    },
    {
      "step": 3,
      "title": "Nivel 1 - Departamento Tipo",
      "description": "NPT +3.25m. Departamentos con 2 recámaras. Piso CASTEL Geo Silver 60x60cm. Cancelería aluminio 3\" negro con cristal 6mm.",
      "highlights": ["NPT +3.25m", "2 Recámaras", "Piso CASTEL"],
      "camera": { "pos": [20, 10, 20], "target": [0, 7, 0] },
      "focus": "n1",
      "specs": [
        { "label": "Piso interior", "value": "CASTEL Geo Silver 60x60cm" },
        { "label": "Cancelería", "value": "Aluminio 3\" negro, cristal 6mm" },
        { "label": "Muros", "value": "Pasta CEMIX Reserved White" },
        { "label": "Closet", "value": "MDF Arauco Monarca" }
      ]
    },
    {
      "step": 4,
      "title": "Niveles 2 y 3 - Balcones en \"L\"",
      "description": "NPT +5.85m y +8.45m. Balcones en forma de \"L\" en ambos laterales. Barandales acero color Pimienta K5-12 (COMEX).",
      "highlights": ["Balcones en L", "Barandales acero", "Pimienta K5-12"],
      "camera": { "pos": [-22, 14, 18], "target": [0, 12, 0] },
      "focus": "n2-n3",
      "specs": [
        { "label": "Barandal H-02/03", "value": "Acero tubular 1.5\"x1.5\"" },
        { "label": "Color", "value": "Pimienta K5-12 COMEX" },
        { "label": "Solera", "value": "1.5\" x 1/4\" horizontal" },
        { "label": "Perfiles", "value": "Verticales 1/2\"" }
      ]
    },
    {
      "step": 5,
      "title": "Nivel 4 - Último Piso Habitable",
      "description": "NPT +11.05m. Último nivel con acabados premium. Molduras de concreto colado en sitio color Harrison Gray AP46-5.",
      "highlights": ["NPT +11.05m", "Molduras Harrison Gray", "Acabados premium"],
      "camera": { "pos": [18, 22, 22], "target": [0, 22, 0] },
      "focus": "n4",
      "specs": [
        { "label": "Molduras", "value": "Concreto colado en sitio" },
        { "label": "Pintura", "value": "PRISA Harrison Gray AP46-5" },
        { "label": "Muros", "value": "Aplanado caracoleado" },
        { "label": "Ventanales", "value": "Aluminio negro cristal 6mm" }
      ]
    },
    {
      "step": 6,
      "title": "Azotea - NPT +13.65m",
      "description": "Impermeabilizante IMPAC 3.5mm. Pretil perimetral. Escotilla H-08 acero Portafolio. Escalera marina H-07 tubular.",
      "highlights": ["NPT +13.65m", "IMPAC 3.5mm", "Escotilla acero"],
      "camera": { "pos": [15, 32, 20], "target": [0, 27, 0] },
      "focus": "azotea",
      "specs": [
        { "label": "Impermeabilizante", "value": "IMPAC Hogar 3.5mm" },
        { "label": "Escotilla H-08", "value": "Acero Portafolio 313-06" },
        { "label": "Escalera H-07", "value": "Tubular 1\"x1\" marina" },
        { "label": "Pretil", "value": "Perimetral de concreto" }
      ]
    },
    {
      "step": 7,
      "title": "Cancelería y Ventanales",
      "description": "Sistema de ventanales V-01 a V-09. Aluminio 3\" color negro con cristal claro templado 6mm. Fijo + corrediza.",
      "highlights": ["V-01 a V-09", "Aluminio 3\" negro", "Cristal 6mm"],
      "camera": { "pos": [12, 12, 18], "target": [0, 10, 5] },
      "focus": "windows",
      "specs": [
        { "label": "V-01/02/03", "value": "1 fijo + 1 corrediza" },
        { "label": "V-06/08/09", "value": "3 fijos + 1 corrediza" },
        { "label": "V-04", "value": "Louver 2 rejillas REFLECTO" },
        { "label": "V-07", "value": "Sifón con película privacidad" }
      ]
    },
    {
      "step": 8,
      "title": "Acabados Exteriores",
      "description": "Muros pasta CEMIX ADEBLOK PLUS caracoleado. Pintura PRISA Ivory Too AP57-1. Molduras Harrison Gray. Piedra Georgetown.",
      "highlights": ["CEMIX ADEBLOK", "Ivory Too", "Georgetown"],
      "camera": { "pos": [-25, 15, 20], "target": [-10, 12, 0] },
      "focus": "finishes",
      "specs": [
        { "label": "Muro 2 (Exterior)", "value": "CEMIX ADEBLOK Constructor" },
        { "label": "Pintura", "value": "PRISA Ivory Too AP57-1" },
        { "label": "Piedra", "value": "Georgetown INTERSTONE" },
        { "label": "Columnas (Muro 9)", "value": "PRISA Harrison Gray AP46-5" }
      ]
    }
  ]
}
```

---

## 📄 8. `.env` (archivo de configuración)

```env
# Configuración del servidor
PORT=3000
NODE_ENV=development

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5500

# API
API_PREFIX=/api
API_VERSION=v1
```

---

## 📄 9. `README.md` - Documentación

```markdown
# 🏢 Torre MONTERRA - Backend API

API REST para el proyecto arquitectónico **Torre MONTERRA V2**.

## 🚀 Instalación

```bash
cd backend
npm install
```

## ▶️ Ejecución

**Modo desarrollo:**
```bash
npm run dev
```

**Modo producción:**
```bash
npm start
```

## 📡 Endpoints

### Salud del sistema
- `GET /api/health` - Estado del servidor

### Proyecto
- `GET /api/project` - Información general del proyecto

### Niveles
- `GET /api/levels` - Lista todos los niveles
- `GET /api/levels/:id` - Detalle de un nivel (pb, n1, n2, n3, n4, azotea)

### Materiales
- `GET /api/materials` - Todos los materiales
- `GET /api/materials/:type` - Por categoría (floors, walls, ceilings)

### Componentes
- `GET /api/components` - Todos los componentes
- `GET /api/components/:type` - Por tipo (doors, windows, ironwork, equipment, bathroom_accessories)
- `GET /api/components/:type/:id` - Componente específico

### Tour Guiado
- `GET /api/tour` - Todos los pasos del tour
- `GET /api/tour/:step` - Paso específico (1-8)

### Planos
- `GET /api/drawings` - Lista de láminas del proyecto

### Búsqueda
- `GET /api/search?q=term` - Búsqueda global

## 📊 Ejemplos de Respuesta

```json
{
  "success": true,
  "data": { ... }
}
```

## 🛠️ Tecnologías

- **Node.js** - Runtime
- **Express** - Framework web
- **CORS** - Cross-Origin Resource Sharing
- **Compression** - Compresión gzip
- **dotenv** - Variables de entorno

## 📁 Estructura

```
backend/
├── server.js          # Servidor principal
├── routes/api.js      # Rutas
├── data/              # Datos JSON
│   ├── project.json
│   ├── materials.json
│   ├── components.json
│   └── tour.json
└── package.json
```
```

---

## 🎯 Cómo Usar el Backend

### 1️⃣ **Instalar dependencias**
```bash
cd backend
npm install
```

### 2️⃣ **Iniciar el servidor**
```bash
npm start
```

### 3️⃣ **Probar endpoints**
```bash
# Salud
curl http://localhost:3000/api/health

# Todos los niveles
curl http://localhost:3000/api/levels

# Material específico
curl http://localhost:3000/api/materials/walls

# Tour paso 3
curl http://localhost:3000/api/tour/3

# Búsqueda
curl "http://localhost:3000/api/search?q=CEMIX"
```

### 4️⃣ **Conectar con el Frontend**
En el HTML del modelo 3D, puedes cargar los datos dinámicamente:

```javascript
// Ejemplo de integración con el frontend
async function loadProjectData() {
  const response = await fetch('http://localhost:3000/api/project');
  const data = await response.json();
  console.log(data);
}

async function loadTourStep(step) {
  const response = await fetch(`http://localhost:3000/api/tour/${step}`);
  const data = await response.json();
  updateTourPanel(data.data);
}
```

---

## ✨ Características del Backend

✅ **API REST completa** con 15+ endpoints  
✅ **Datos reales** extraídos del PDF arquitectónico  
✅ **Búsqueda global** en todos los datos  
✅ **Manejo de errores** robusto  
✅ **CORS habilitado** para integración frontend  
✅ **Compresión gzip** para mejor rendimiento  
✅ **Logger de requests** para debugging  
✅ **Modular y escalable** - fácil de extender  
✅ **Documentación completa** en README  
✅ **Datos estructurados** en JSON separado  

El backend está listo para servir todos los datos arquitectónicos de la Torre MONTERRA de manera eficiente y estructurada. 🏗️