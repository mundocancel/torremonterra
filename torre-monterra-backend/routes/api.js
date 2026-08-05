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
