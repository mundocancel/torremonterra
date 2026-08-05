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
