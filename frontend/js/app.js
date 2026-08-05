// ============ CONFIGURACIÓN ============
const SCALE = 2;
const DIM = { width: 11.72 * SCALE, depth: 10.33 * SCALE, floorHeight: 2.60 * SCALE };

const LEVELS = {
  pb: { npt: 0.65, name: 'Planta Baja', color: 0xe8e4dc },
  n1: { npt: 3.25, name: 'Nivel 1', color: 0xe8e4dc },
  n2: { npt: 5.85, name: 'Nivel 2', color: 0xe8e4dc },
  n3: { npt: 8.45, name: 'Nivel 3', color: 0xe8e4dc },
  n4: { npt: 11.05, name: 'Nivel 4', color: 0xe8e4dc },
  azotea: { npt: 13.65, name: 'Azotea', color: 0xd4d0c8 }
};

const INFO = {
  all: '<strong>Vista completa</strong><br>Torre de 6 niveles con acabados premium.<br>Altura total: 13.65m',
  pb: '<strong>Planta Baja - NPT +0.65m</strong><br>• Puerta P-04 WPC Nogal SIN-12<br>• Cerradura TECDOFY H5H<br>• Piso LAMOSA Sinatra Gris<br>• Muro Piedra Georgetown',
  n1: '<strong>Nivel 1 - NPT +3.25m</strong><br>• Piso CASTEL Geo Silver 60x60<br>• Cancelería aluminio 3" negro<br>• Closet MDF Arauco Monarca<br>• Cocina Lu Marquina KOBER',
  n2: '<strong>Nivel 2 - NPT +5.85m</strong><br>• Balcones en "L" laterales<br>• Barandal H-02 acero Pimienta K5-12<br>• Cancelería V-05 a V-09',
  n3: '<strong>Nivel 3 - NPT +8.45m</strong><br>• Muros CEMIX Reserved White<br>• Ventanales aluminio cristal 6mm<br>• Accesorios baño DICA cromo',
  n4: '<strong>Nivel 4 - NPT +11.05m</strong><br>• Molduras concreto colado<br>• Pintura Harrison Gray AP46-5<br>• Acabados premium',
  azotea: '<strong>Azotea - NPT +13.65m</strong><br>• IMPAC Hogar 3.5mm<br>• Escotilla H-08 acero Portafolio<br>• Escalera marina H-07 tubular'
};

// ============ VARIABLES GLOBALES ============
let scene, camera, renderer, controls;
let building = { levels: {} };
let allMeshes = [];
let wireframeMode = false;

// ============ INICIALIZACIÓN ============
function init() {
  // Escena
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a192f);
  scene.fog = new THREE.Fog(0x0a192f, 80, 200);

  // Cámara
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 500);
  camera.position.set(35, 25, 35);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.getElementById('canvas-container').appendChild(renderer.domElement);

  // Controles
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 10;
  controls.maxDistance = 80;
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.target.set(0, 13, 0);

  // Iluminación
  setupLighting();

  // Suelo
  createGround();

  // Edificio
  createBuilding();

  // Eventos
  window.addEventListener('resize', onResize);
  setupControls();

  document.getElementById('loading').classList.add('hidden');
  animate();
}

function setupLighting() {
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  scene.add(new THREE.HemisphereLight(0x87ceeb, 0x3a3a3a, 0.4));

  const sun = new THREE.DirectionalLight(0xfff4e0, 1.0);
  sun.position.set(30, 40, 20);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  sun.shadow.camera.left = -40;
  sun.shadow.camera.right = 40;
  sun.shadow.camera.top = 40;
  sun.shadow.camera.bottom = -40;
  scene.add(sun);

  const fill = new THREE.DirectionalLight(0x4facfe, 0.3);
  fill.position.set(-20, 15, -10);
  scene.add(fill);
}

function createGround() {
  const platform = new THREE.Mesh(
    new THREE.BoxGeometry(45, 0.3, 40),
    new THREE.MeshStandardMaterial({ color: 0x2a2a3e, roughness: 0.8 })
  );
  platform.position.y = -0.15;
  platform.receiveShadow = true;
  scene.add(platform);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    new THREE.MeshStandardMaterial({ color: 0x1a1a2e, roughness: 0.9 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.3;
  ground.receiveShadow = true;
  scene.add(ground);
}

// ============ CONSTRUCCIÓN DEL EDIFICIO ============
function createBuilding() {
  const W = DIM.width, D = DIM.depth, H = DIM.floorHeight;

  // Medidas base tomadas de ARQ-07: frente 11.72m, lateral 10.33m y entrepisos de 2.60m.
  // El modelo usa SCALE=2 para que el edificio se aprecie con claridad en el visor.
  const wallMat = new THREE.MeshStandardMaterial({ color: 0xf0ece3, roughness: 0.76 });
  const redMat = new THREE.MeshStandardMaterial({ color: 0x6f1e1a, roughness: 0.7 });
  const concreteMat = new THREE.MeshStandardMaterial({ color: 0xcac5ba, roughness: 0.65 });
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x15191d, roughness: 0.34, metalness: 0.62 });
  const glassMat = new THREE.MeshPhysicalMaterial({ color: 0x7fa6b7, roughness: 0.08, metalness: 0.05, transparent: true, opacity: 0.62 });
  const woodMat = new THREE.MeshStandardMaterial({ color: 0x4f3320, roughness: 0.68 });
  const stairMat = new THREE.MeshStandardMaterial({ color: 0x32302c, roughness: 0.88 });

  const addMesh = (group, geometry, material, position) => {
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...position);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
    allMeshes.push(mesh);
    return mesh;
  };

  Object.keys(LEVELS).forEach(key => {
    const levelData = LEVELS[key];
    const group = new THREE.Group();
    group.userData.level = key;

    const baseY = levelData.npt * SCALE;

    // Volumen principal y moldura perimetral de concreto.
    addMesh(group, new THREE.BoxGeometry(W, H, D), wallMat, [0, baseY + H / 2, 0]);
    addMesh(group, new THREE.BoxGeometry(W + 0.32, 0.22, D + 0.32), concreteMat, [0, baseY + 0.11, 0]);

    if (key === 'pb') {
      // PB: zócalo Brier Branch, puerta doble central y dos accesos laterales.
      addMesh(group, new THREE.BoxGeometry(W + 0.08, H - 0.22, 0.2), redMat, [0, baseY + H / 2, D / 2 + 0.11]);
      [-7.9, 7.9].forEach(x => addDoor(group, x, baseY + H / 2, D / 2 + 0.24, 1.62 * SCALE, 2.25 * SCALE, woodMat, frameMat, addMesh));
      addDoor(group, 0, baseY + H / 2, D / 2 + 0.24, 2.35 * SCALE, 2.45 * SCALE, woodMat, frameMat, addMesh, true);
      addFrontRail(group, -4.7, baseY + 1.05, D / 2 + 0.35, 3.25 * SCALE, frameMat, addMesh);
      addFrontRail(group, 4.7, baseY + 1.05, D / 2 + 0.35, 3.25 * SCALE, frameMat, addMesh);
    }

    if (['n1', 'n2', 'n3', 'n4'].includes(key)) {
      // Fachada ARQ-07: dos campos de ventanas 2x2, balcones exteriores y vacío central de escaleras.
      [-4.25, 4.25].forEach(x => addFourPaneWindow(group, x, baseY + H / 2, D / 2 + 0.12, 1.72 * SCALE, 2.1 * SCALE, frameMat, glassMat, addMesh));
      [-9.05, 9.05].forEach(x => {
        addTallWindow(group, x, baseY + H / 2, D / 2 + 0.12, 1.28 * SCALE, 2.1 * SCALE, frameMat, glassMat, addMesh);
        addFrontRail(group, x, baseY + H * 0.38, D / 2 + 0.36, 1.48 * SCALE, frameMat, addMesh);
      });

      // Hueco vertical de escalera: profundo, oscuro y con descansos / barandales visibles.
      addMesh(group, new THREE.BoxGeometry(2.64 * SCALE, H - 0.35, 0.32), stairMat, [0, baseY + H / 2, D / 2 + 0.11]);
      addMesh(group, new THREE.BoxGeometry(2.24 * SCALE, 0.14, 1.2), concreteMat, [0, baseY + 0.55, D / 2 + 0.68]);
      addFrontRail(group, 0, baseY + H * 0.38, D / 2 + 0.78, 2.12 * SCALE, frameMat, addMesh, true);
    }

    if (key === 'n1') {
      // Aberturas discretas en lateral derecho, como el alzado ARQ-09.
      [-6.0, 0.5, 6.6].forEach(z => addSideWindow(group, W / 2 + 0.12, baseY + H / 2, z, 1.05 * SCALE, 1.45 * SCALE, frameMat, glassMat, addMesh));
    }

    if (key === 'azotea') {
      // Pretil y torreón central de azotea, rematados por moldura de concreto.
      addMesh(group, new THREE.BoxGeometry(W + 0.42, 0.28, D + 0.42), concreteMat, [0, baseY + H + 0.14, 0]);
      addMesh(group, new THREE.BoxGeometry(W * 0.46, 2.2, 0.42), redMat, [0, baseY + H + 1.05, D / 2 - 1.1]);
      addMesh(group, new THREE.BoxGeometry(W - 1.1, 0.75, D - 1.1), wallMat, [0, baseY + H + 0.38, 0]);
      // Azotea trasera: moldura de concreto colado en sitio.
      addMesh(group, new THREE.BoxGeometry(W + 0.42, 0.28, D + 0.42), concreteMat, [0, baseY + H + 0.14, 0]);
    }

    // ============ FACHADA POSTERIOR (ARQ-08 / ARQ-20) ============
    // Z = -D/2 (atrás). Simétrica: ventanal 2x2 centrado + 2 ventanas laterales estrechas + muros ciegos extremos.
    if (['n1', 'n2', 'n3', 'n4'].includes(key)) {
      // Ventanal central 2x2 (cuatro paños)
      addFourPaneWindow(group, 0, baseY + H / 2, -D / 2 - 0.12, 1.72 * SCALE, 2.1 * SCALE, frameMat, glassMat, addMesh);
      // Ventanas verticales estrechas flanqueando el centro
      [-3.4, 3.4].forEach(x => addTallWindow(group, x, baseY + H / 2, -D / 2 - 0.12, 0.95 * SCALE, 2.1 * SCALE, frameMat, glassMat, addMesh));
      // Muros ciegos en extremos (±5.86 m del centro = 2.82 m desde borde), sin huecos.
    }

    if (key === 'pb') {
      // PB posterior: dos portones de servicio con cristal (rayas diagonales) a ±4.54 m del centro.
      [-4.54, 4.54].forEach(x => addServiceDoor(group, x, baseY + H / 2, -D / 2 - 0.12, 2.0 * SCALE, 2.2 * SCALE, woodMat, frameMat, glassMat, addMesh));
      // Zona central (rampa/escaleras) sin hueco visible: muro bajo / barandilla.
      addMesh(group, new THREE.BoxGeometry(3.5 * SCALE, 1.2 * SCALE, 0.18), concreteMat, [0, baseY + 0.6 * SCALE, -D / 2 - 0.11]);
      // Molduras de concreto a 0.80 m (izq/der) según alzado.
      [-5.5, 5.5].forEach(x => addMesh(group, new THREE.BoxGeometry(0.6 * SCALE, 0.22, 0.3), concreteMat, [x, baseY + 0.8 * SCALE, -D / 2 - 0.11]));
    }

    // ============ LATERAL DERECHO (ARQ-09) ============
    // X = +W/2. 4 ventanas centradas por nivel + escalera en PB.
    if (['n1', 'n2', 'n3', 'n4'].includes(key)) {
      addSideWindow(group, W / 2 + 0.12, baseY + H / 2, 0, 1.05 * SCALE, 1.45 * SCALE, frameMat, glassMat, addMesh);
    }
    if (key === 'pb') {
      // Escalera de acceso lateral derecho
      addMesh(group, new THREE.BoxGeometry(0.3, 2.6 * SCALE, 1.8 * SCALE), stairMat, [W / 2 + 0.15, baseY + 1.3 * SCALE, -D / 2 + 2.5 * SCALE]);
      addFrontRail(group, W / 2 + 0.15, baseY + 1.3 * SCALE, -D / 2 + 1.6 * SCALE, 1.6 * SCALE, frameMat, addMesh);
    }

    // ============ LATERAL IZQUIERDO (ARQ-10/11) ============
    // X = -W/2. Simétrico al derecho pero sin escalera en PB.
    if (['n1', 'n2', 'n3', 'n4'].includes(key)) {
      addSideWindow(group, -W / 2 - 0.12, baseY + H / 2, 0, 1.05 * SCALE, 1.45 * SCALE, frameMat, glassMat, addMesh);
    }

    building.levels[key] = group;
    scene.add(group);
  });
}

function addFourPaneWindow(group, x, y, z, width, height, frameMat, glassMat, addMesh) {
  addMesh(group, new THREE.BoxGeometry(width + 0.18, height + 0.18, 0.15), frameMat, [x, y, z]);
  addMesh(group, new THREE.BoxGeometry(width - 0.16, height - 0.16, 0.07), glassMat, [x, y, z + 0.1]);
  addMesh(group, new THREE.BoxGeometry(0.11, height - 0.06, 0.19), frameMat, [x, y, z + 0.13]);
  addMesh(group, new THREE.BoxGeometry(width - 0.06, 0.11, 0.19), frameMat, [x, y, z + 0.13]);
}

function addTallWindow(group, x, y, z, width, height, frameMat, glassMat, addMesh) {
  addMesh(group, new THREE.BoxGeometry(width + 0.16, height + 0.16, 0.15), frameMat, [x, y, z]);
  addMesh(group, new THREE.BoxGeometry(width - 0.12, height - 0.12, 0.07), glassMat, [x, y, z + 0.1]);
  addMesh(group, new THREE.BoxGeometry(0.1, height - 0.04, 0.19), frameMat, [x, y, z + 0.13]);
}

function addSideWindow(group, x, y, z, width, height, frameMat, glassMat, addMesh) {
  addMesh(group, new THREE.BoxGeometry(0.15, height + 0.16, width + 0.16), frameMat, [x, y, z]);
  addMesh(group, new THREE.BoxGeometry(0.07, height - 0.12, width - 0.12), glassMat, [x + 0.1, y, z]);
}

function addFrontRail(group, x, y, z, width, material, addMesh, diagonal = false) {
  const height = 1.35 * SCALE;
  addMesh(group, new THREE.BoxGeometry(width, 0.1, 0.1), material, [x, y + height / 2, z]);
  addMesh(group, new THREE.BoxGeometry(width, 0.1, 0.1), material, [x, y - height / 2, z]);
  const bars = Math.max(3, Math.round(width / 0.55));
  for (let i = 0; i <= bars; i++) {
    const barX = x - width / 2 + (width / bars) * i;
    addMesh(group, new THREE.BoxGeometry(0.07, height, 0.07), material, [barX, y, z]);
  }
  if (diagonal) {
    [-1, 1].forEach(direction => {
      const diagonalBar = addMesh(group, new THREE.BoxGeometry(0.07, height * 1.32, 0.07), material, [x + direction * width * 0.2, y, z + 0.02]);
      diagonalBar.rotation.z = direction * Math.PI / 5.5;
    });
  }
}

function addDoor(group, x, y, z, width, height, woodMat, frameMat, addMesh, doubleDoor = false) {
  addMesh(group, new THREE.BoxGeometry(width + 0.24, height + 0.24, 0.17), frameMat, [x, y, z]);
  addMesh(group, new THREE.BoxGeometry(width, height, 0.1), woodMat, [x, y, z + 0.11]);
  if (doubleDoor) addMesh(group, new THREE.BoxGeometry(0.1, height - 0.12, 0.16), frameMat, [x, y, z + 0.18]);
}

function addServiceDoor(group, x, y, z, width, height, woodMat, frameMat, glassMat, addMesh) {
  // Portón de servicio con paneles de cristal (simulando rayas diagonales con cristales subdivididos)
  addMesh(group, new THREE.BoxGeometry(width + 0.18, height + 0.18, 0.15), frameMat, [x, y, z]);
  addMesh(group, new THREE.BoxGeometry(width - 0.12, height - 0.12, 0.07), glassMat, [x, y, z + 0.1]);
  // Subdivisión en 4 paños (2x2) para sugerir paneles
  addMesh(group, new THREE.BoxGeometry(0.1, height - 0.06, 0.19), frameMat, [x, y, z + 0.13]);
  addMesh(group, new THREE.BoxGeometry(width - 0.06, 0.1, 0.19), frameMat, [x, y, z + 0.13]);
  // Detalle de "X" simulado con barras diagonales delgadas
  const diag1 = addMesh(group, new THREE.BoxGeometry(width * 0.7, 0.04, 0.12), frameMat, [x, y, z + 0.15]);
  diag1.rotation.z = Math.PI / 4.2;
  const diag2 = addMesh(group, new THREE.BoxGeometry(width * 0.7, 0.04, 0.12), frameMat, [x, y, z + 0.15]);
  diag2.rotation.z = -Math.PI / 4.2;
}

function addWindows(group, baseY, H, W, D, frameMat, glassMat) {
  const winH = 1.9 * SCALE, winW = 1.6 * SCALE;

  // Frontal y posterior
  for (let i = 0; i < 5; i++) {
    const x = -W/2 + (W/6) * (i + 1);
    [D/2 + 0.05, -D/2 - 0.05].forEach((z, idx) => {
      const frame = new THREE.Mesh(new THREE.BoxGeometry(winW, winH, 0.15), frameMat);
      frame.position.set(x, baseY + H/2, z);
      frame.castShadow = true;
      group.add(frame);
      allMeshes.push(frame);

      const glass = new THREE.Mesh(new THREE.BoxGeometry(winW - 0.2, winH - 0.2, 0.05), glassMat);
      glass.position.set(x, baseY + H/2, z + (idx === 0 ? 0.07 : -0.07));
      group.add(glass);
      allMeshes.push(glass);
    });
  }

  // Laterales
  for (let i = 0; i < 3; i++) {
    const z = -D/2 + (D/4) * (i + 1);
    [W/2 + 0.05, -W/2 - 0.05].forEach((x, idx) => {
      const frame = new THREE.Mesh(new THREE.BoxGeometry(0.15, winH, winW), frameMat);
      frame.position.set(x, baseY + H/2, z);
      frame.castShadow = true;
      group.add(frame);
      allMeshes.push(frame);

      const glass = new THREE.Mesh(new THREE.BoxGeometry(0.05, winH - 0.2, winW - 0.2), glassMat);
      glass.position.set(x + (idx === 0 ? 0.07 : -0.07), baseY + H/2, z);
      group.add(glass);
      allMeshes.push(glass);
    });
  }
}

function addBalconies(group, baseY, W, D, balconyMat, railingMat) {
  const bDepth = 1.5 * SCALE, bLength = 3.5 * SCALE;

  [1, -1].forEach(side => {
    const xOff = side * (W/2);

    // Plataforma 1
    const p1 = new THREE.Mesh(new THREE.BoxGeometry(bDepth, 0.15, bLength), balconyMat);
    p1.position.set(xOff + side * bDepth/2, baseY + 0.075, D/2 - bLength/2);
    p1.castShadow = true;
    group.add(p1);
    allMeshes.push(p1);

    // Plataforma 2
    const p2 = new THREE.Mesh(new THREE.BoxGeometry(bLength, 0.15, bDepth), balconyMat);
    p2.position.set(xOff - side * bLength/2 + side * bDepth, baseY + 0.075, -D/2 + bDepth/2);
    p2.castShadow = true;
    group.add(p2);
    allMeshes.push(p2);

    // Barandal
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.1, bLength), railingMat);
    rail.position.set(xOff + side * bDepth, baseY + 0.55, D/2 - bLength/2);
    group.add(rail);
    allMeshes.push(rail);
  });
}

function addMainAccess(group, baseY, W, D, accessMat, molduraMat) {
  const aW = 2.2 * SCALE, aH = 2.4 * SCALE;

  const frame = new THREE.Mesh(new THREE.BoxGeometry(aW + 0.3, aH + 0.15, 0.2), accessMat);
  frame.position.set(0, baseY + aH/2, D/2 + 0.1);
  frame.castShadow = true;
  group.add(frame);
  allMeshes.push(frame);

  const door = new THREE.Mesh(
    new THREE.BoxGeometry(aW, aH, 0.1),
    new THREE.MeshStandardMaterial({ color: 0x5a4530, roughness: 0.5 })
  );
  door.position.set(0, baseY + aH/2, D/2 + 0.2);
  group.add(door);
  allMeshes.push(door);

  const dintel = new THREE.Mesh(new THREE.BoxGeometry(aW + 0.6, 0.3, 0.3), molduraMat);
  dintel.position.set(0, baseY + aH + 0.15, D/2 + 0.1);
  group.add(dintel);
  allMeshes.push(dintel);
}

// ============ CONTROLES ============
function setupControls() {
  document.querySelectorAll('.btn[data-level]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn[data-level]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      showLevel(btn.dataset.level);
    });
  });

  document.getElementById('btn-wireframe').addEventListener('click', () => {
    wireframeMode = !wireframeMode;
    allMeshes.forEach(m => { if (m.material) m.material.wireframe = wireframeMode; });
  });

  document.getElementById('btn-reset').addEventListener('click', () => {
    camera.position.set(35, 25, 35);
    controls.target.set(0, 13, 0);
    showLevel('all');
    document.querySelectorAll('.btn[data-level]').forEach(b => b.classList.remove('active'));
    document.querySelector('.btn[data-level="all"]').classList.add('active');
  });

  document.getElementById('btn-rotate').addEventListener('click', () => {
    controls.autoRotate = !controls.autoRotate;
    controls.autoRotateSpeed = 1.5;
  });
}

function showLevel(level) {
  document.getElementById('info-text').innerHTML = INFO[level] || INFO.all;

  Object.entries(building.levels).forEach(([key, group]) => {
    group.visible = true;
    group.traverse(child => {
      if (child.isMesh) {
        if (level === 'all' || key === level) {
          child.material.transparent = false;
          child.material.opacity = 1;
        } else {
          child.material.transparent = true;
          child.material.opacity = 0.15;
        }
      }
    });
  });
}

// ============ LOOP ============
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

// Iniciar
init();
