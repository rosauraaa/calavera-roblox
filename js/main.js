import * as THREE from "three";
import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import { sfx, unlockAudio } from "./sfx.js";

// Perillas de calibracion
const MOUTH_TRIGGER = 0.45;   // jawOpen > 45 % -> lluvia de petalos
const BROWS_TRIGGER = 0.55;   // browInnerUp > 55 % -> cambio de color + velas
const COOLDOWN = 1.2;         // segundos entre disparos
const PALETTES = ["clasica", "turquesa", "dorada"];
const PETAL_COLORS = { clasica: ["#ff8c00", "#ffc300"], turquesa: ["#00b4c5", "#8be9ff"], dorada: ["#ffb000", "#ffe066"] };

const $ = (id) => document.getElementById(id);
const video = $("cam");
const canvas = $("gl");
const status = (t) => ($("status").textContent = t);

// ---------------------------------------------------------------- three.js (camara en pixeles del video)
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(1);
const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(0, 1, 0, -1, -10000, 10000);

let W = 1, H = 1;
function resize() {
  W = video.videoWidth;
  H = video.videoHeight;
  renderer.setSize(W, H, false);
  Object.assign(camera, { left: 0, right: W, top: 0, bottom: -H });
  camera.updateProjectionMatrix();
}

// ---------------------------------------------------------------- malla facial con la textura pintada
const geometry = new THREE.BufferGeometry();
const positions = new Float32Array(468 * 3);
geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3).setUsage(THREE.DynamicDrawUsage));
const material = new THREE.MeshBasicMaterial({ transparent: true, side: THREE.DoubleSide, alphaTest: 0.02 });
const face = new THREE.Mesh(geometry, material);
face.frustumCulled = false;
face.visible = false;
scene.add(face);

const textures = {};
let palette = 0;

async function loadMask() {
  const mesh = await (await fetch("assets/mesh/face_mesh.json")).json();
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(mesh.uv, 2));
  geometry.setIndex(mesh.index);
  const loader = new THREE.TextureLoader();
  await Promise.all(PALETTES.map(async (p) => {
    const t = await loader.loadAsync(`assets/textures/calavera-${p}.png`);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    textures[p] = t;
  }));
  material.map = textures[PALETTES[0]];
  material.needsUpdate = true;
}

function updateMesh(lm) {
  for (let i = 0; i < 468; i++) {
    positions[i * 3] = lm[i].x * W;
    positions[i * 3 + 1] = -lm[i].y * H;
    positions[i * 3 + 2] = -lm[i].z * W;
  }
  geometry.attributes.position.needsUpdate = true;
}

// ---------------------------------------------------------------- sprites dibujados en canvas
function canvasTexture(draw, size = 64) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  draw(c.getContext("2d"), size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const petalTex = canvasTexture((g, s) => {
  g.fillStyle = "#fff";
  g.beginPath();
  g.ellipse(s / 2, s / 2, s * 0.22, s * 0.45, 0, 0, Math.PI * 2);
  g.fill();
  g.strokeStyle = "rgba(0,0,0,.35)";
  g.lineWidth = 3;
  g.beginPath();
  g.moveTo(s / 2, s * 0.15);
  g.lineTo(s / 2, s * 0.85);
  g.stroke();
});

const flameTex = canvasTexture((g, s) => {
  const grad = g.createRadialGradient(s / 2, s * 0.62, 2, s / 2, s * 0.55, s * 0.45);
  grad.addColorStop(0, "#fffbe0");
  grad.addColorStop(0.35, "#ffd23f");
  grad.addColorStop(0.7, "#ff7b00");
  grad.addColorStop(1, "rgba(255,80,0,0)");
  g.fillStyle = grad;
  g.beginPath();
  g.moveTo(s / 2, s * 0.05);
  g.quadraticCurveTo(s * 0.9, s * 0.6, s / 2, s * 0.95);
  g.quadraticCurveTo(s * 0.1, s * 0.6, s / 2, s * 0.05);
  g.fill();
});

// petalos de cempasuchil
const petals = [];
for (let i = 0; i < 140; i++) {
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: petalTex, transparent: true }));
  sp.visible = false;
  scene.add(sp);
  petals.push({ sp, v: new THREE.Vector2(), life: 0, phase: 0 });
}

function spawnPetal(x, y, vx, vy, size, life) {
  const p = petals.find((q) => q.life <= 0);
  if (!p) return;
  const cols = PETAL_COLORS[PALETTES[palette]];
  p.sp.material.color.set(cols[Math.floor(Math.random() * cols.length)]);
  p.sp.position.set(x, y, 500);
  p.sp.scale.set(size * 0.6, size, 1);
  p.sp.material.rotation = Math.random() * Math.PI * 2;
  p.sp.visible = true;
  p.v.set(vx, vy);
  p.life = life;
  p.phase = Math.random() * 10;
}

function updatePetals(dt, faceW) {
  for (const p of petals) {
    if (p.life <= 0) continue;
    p.life -= dt;
    p.phase += dt * 3;
    p.v.y -= faceW * 0.9 * dt;                  // gravedad
    p.v.y = Math.max(p.v.y, -faceW * 1.1);      // caen suave, como petalos
    p.sp.position.x += (p.v.x + Math.sin(p.phase) * faceW * 0.4) * dt;
    p.sp.position.y += p.v.y * dt;
    p.sp.material.rotation += dt * 2;
    p.sp.material.opacity = Math.min(p.life * 2, 1);
    if (p.life <= 0) p.sp.visible = false;
  }
}

// velas que aparecen en arco sobre la cabeza
const candles = [];
for (let i = 0; i < 7; i++) {
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: flameTex, transparent: true, depthWrite: false }));
  sp.visible = false;
  scene.add(sp);
  candles.push(sp);
}
let candleTime = 0;

function updateCandles(dt, lm, faceW) {
  candleTime -= dt;
  const show = candleTime > 0 && lm;
  for (const [i, sp] of candles.entries()) {
    sp.visible = !!show;
    if (!show) continue;
    const ang = Math.PI * (0.02 + 0.96 * i / (candles.length - 1));
    const top = lm[10];
    const flicker = 1 + Math.sin(performance.now() / 70 + i * 1.7) * 0.12;
    const grow = Math.min((2.5 - candleTime) * 4, 1, candleTime * 2);   // aparecen y se apagan suave
    sp.position.set(top.x * W + Math.cos(ang) * faceW * 0.85, -top.y * H + Math.sin(ang) * faceW * 0.4 - faceW * 0.3, 600);
    sp.scale.set(faceW * 0.18 * grow, faceW * 0.3 * flicker * grow, 1);
  }
}

// ---------------------------------------------------------------- gestos
const cooldown = { mouth: 0, brows: 0 };
let flash = 0;

function chip(id) {
  const el = $(`chip-${id}`);
  el.classList.add("on");
  setTimeout(() => el.classList.remove("on"), 600);
}

function applyGestures(bs, lm, faceW, dt) {
  const s = (n) => bs[n] ?? 0;
  for (const k in cooldown) cooldown[k] -= dt;

  if (s("jawOpen") > MOUTH_TRIGGER && cooldown.mouth <= 0) {
    cooldown.mouth = COOLDOWN;
    const top = lm[10], mouth = lm[13];
    for (let i = 0; i < 45; i++) {     // lluvia desde arriba de la cabeza
      spawnPetal(top.x * W + (Math.random() - 0.5) * faceW * 2.4, -top.y * H + faceW * (0.4 + Math.random() * 0.8),
        (Math.random() - 0.5) * faceW * 0.3, -Math.random() * faceW * 0.3, faceW * 0.12, 2.2 + Math.random());
    }
    for (let i = 0; i < 18; i++) {     // y un soplo desde la boca
      spawnPetal(mouth.x * W, -mouth.y * H, (Math.random() - 0.5) * faceW * 2.5, faceW * (0.6 + Math.random()), faceW * 0.09, 1.6);
    }
    sfx.marimba();
    chip("mouth");
  }

  const brows = Math.max(s("browInnerUp"), (s("browOuterUpLeft") + s("browOuterUpRight")) / 2);
  if (brows > BROWS_TRIGGER && cooldown.brows <= 0) {
    cooldown.brows = COOLDOWN;
    palette = (palette + 1) % PALETTES.length;
    material.map = textures[PALETTES[palette]];
    flash = 0.35;
    candleTime = 2.5;
    sfx.chime();
    chip("brows");
  }
}

// ---------------------------------------------------------------- arranque
async function startCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
  resize();
}

async function loadLandmarker() {
  const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm");
  return FaceLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numFaces: 1,
    outputFaceBlendshapes: true,
  });
}

$("sound").addEventListener("click", (e) => {
  unlockAudio();
  e.currentTarget.hidden = true;
});
window.addEventListener("pointerdown", unlockAudio, { once: true });
video.addEventListener("resize", resize);

let landmarker;
try {
  await startCamera();
  status("Cargando detector facial y máscara…");
  [landmarker] = await Promise.all([loadLandmarker(), loadMask()]);
  $("loading").hidden = true;
} catch (err) {
  console.error(err);
  status(`No se pudo iniciar 😢 (${err.name || err.message}). Abre la página con HTTPS y permite la cámara.`);
  throw err;
}

const clock = new THREE.Clock();
let lastVideoTime = -1;
let faceW = 200;
let lm = null;
let ambient = 0;

renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    const res = landmarker.detectForVideo(video, performance.now());
    lm = res.faceLandmarks[0] ?? null;
    if (lm) {
      updateMesh(lm);
      faceW = Math.hypot((lm[454].x - lm[234].x) * W, (lm[454].y - lm[234].y) * H);
      const bs = Object.fromEntries(res.faceBlendshapes[0].categories.map((c) => [c.categoryName, c.score]));
      applyGestures(bs, lm, faceW, dt);
    }
    face.visible = !!lm;
    $("hint").hidden = !!lm;
  }

  // animacion ambiente: siempre caen algunos petalos alrededor
  ambient -= dt;
  if (lm && ambient <= 0) {
    ambient = 0.35;
    spawnPetal(lm[10].x * W + (Math.random() - 0.5) * faceW * 3, -lm[10].y * H + faceW * 0.9, 0, 0, faceW * 0.08, 3);
  }

  // destello blanco al cambiar de color
  flash = Math.max(flash - dt, 0);
  material.color.setScalar(1 + flash * 3);

  updatePetals(dt, faceW);
  updateCandles(dt, lm, faceW);
  renderer.render(scene, camera);
});
