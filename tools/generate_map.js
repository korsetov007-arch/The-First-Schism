const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const WIDTH = 2048;
const HEIGHT = 1024;
const SAMPLE = 2;
const GRID_WIDTH = WIDTH / SAMPLE;
const GRID_HEIGHT = HEIGHT / SAMPLE;
const SEA_COLUMNS = 8;
const SEA_ROWS = 5;

const STATE_DEFS = [
  { id: 1, key: "VOR_NW", country: "VOR", en: "Grey Coast", ru: "Серый Берег", vpEn: "Static's Harbour", vpRu: "Гавань Статика", category: "town", terrain: "plains", manpower: 52000, infrastructure: 3, industry: 1, arms: 1, resources: { steel: 4 }, color: [76, 91, 105] },
  { id: 2, key: "VOR_NE", country: "VOR", en: "Vortex Heights", ru: "Вихревые Высоты", vpEn: "Vortex Group", vpRu: "Вихрь-Групп", category: "rural", terrain: "mountain", manpower: 41000, infrastructure: 2, industry: 0, arms: 1, resources: { aluminium: 5 }, color: [67, 80, 94] },
  { id: 3, key: "VOR_CW", country: "VOR", en: "Ambrelnoe Selo", ru: "Село Амбрельное", vpEn: "Shlang's Redoubt", vpRu: "Опорный пункт Шланга", category: "rural", terrain: "forest", manpower: 67000, infrastructure: 2, industry: 1, arms: 0, resources: { oil: 3 }, color: [82, 96, 105] },
  { id: 4, key: "VOR_CE", country: "VOR", en: "Central Mandate", ru: "Центральный Мандат", vpEn: "Spartak's Command", vpRu: "Штаб Спартака", category: "city", terrain: "urban", manpower: 78000, infrastructure: 4, industry: 3, arms: 2, resources: { steel: 6 }, color: [87, 103, 119] },
  { id: 5, key: "VOR_SW", country: "VOR", en: "Shadow Reach", ru: "Теневой Предел", vpEn: "Echidna Crossing", vpRu: "Переправа Ехидны", category: "rural", terrain: "marsh", manpower: 46000, infrastructure: 2, industry: 0, arms: 0, resources: { tungsten: 3 }, color: [60, 76, 86] },
  { id: 6, key: "VOR_SE", country: "VOR", en: "WAR Bastion", ru: "Бастион WAR", vpEn: "Buzoganyvete Fort", vpRu: "Форт Бузоганьветё", category: "town", terrain: "hills", manpower: 59000, infrastructure: 3, industry: 2, arms: 2, resources: { chromium: 4 }, color: [72, 88, 108] },
  { id: 7, key: "OGO_NW", country: "OGO", en: "Old Garden", ru: "Старый Огород", vpEn: "Pidofil's Dacha", vpRu: "Дача Пидофила", category: "city", terrain: "urban", manpower: 76000, infrastructure: 4, industry: 2, arms: 1, resources: { steel: 3 }, color: [91, 96, 69] },
  { id: 8, key: "OGO_NE", country: "OGO", en: "Ilyich's Landing", ru: "Плацдарм Ильича", vpEn: "New Hydra", vpRu: "Новая Гидра", category: "town", terrain: "forest", manpower: 55000, infrastructure: 3, industry: 1, arms: 1, resources: { rubber: 3 }, color: [76, 85, 62] },
  { id: 9, key: "OGO_CW", country: "OGO", en: "Atamanov's March", ru: "Атамановский Уезд", vpEn: "Wagner Station", vpRu: "Станция Вагнер", category: "town", terrain: "hills", manpower: 58000, infrastructure: 3, industry: 1, arms: 2, resources: { steel: 5 }, color: [99, 91, 65] },
  { id: 10, key: "OGO_CE", country: "OGO", en: "Perchik Lowlands", ru: "Низины Перчика", vpEn: "Arena", vpRu: "Арена", category: "large_town", terrain: "plains", manpower: 72000, infrastructure: 3, industry: 2, arms: 1, resources: { oil: 5 }, color: [88, 98, 70] },
  { id: 11, key: "OGO_SW", country: "OGO", en: "Red Hammer Basin", ru: "Котловина Красного Молота", vpEn: "Dimbazgrad", vpRu: "Димбазград", category: "town", terrain: "mountain", manpower: 61000, infrastructure: 2, industry: 2, arms: 2, resources: { chromium: 5 }, color: [100, 81, 62] },
  { id: 12, key: "OGO_SE", country: "OGO", en: "Dolgan Expanse", ru: "Долганская Даль", vpEn: "Dark Watch", vpRu: "Дарк Вотч", category: "rural", terrain: "forest", manpower: 49000, infrastructure: 2, industry: 1, arms: 0, resources: { tungsten: 4 }, color: [69, 80, 59] },
];

function writeText(relativePath, contents) {
  const file = path.join(ROOT, relativePath);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, contents, "utf8");
}

function hash(x, y) {
  let value = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263);
  value = Math.imul(value ^ (value >>> 13), 1274126177);
  return (value ^ (value >>> 16)) >>> 0;
}

function pointInPolygon(x, y, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function preparePolygon(points) {
  return {
    points,
    minX: Math.min(...points.map((point) => point[0])),
    maxX: Math.max(...points.map((point) => point[0])),
    minY: Math.min(...points.map((point) => point[1])),
    maxY: Math.max(...points.map((point) => point[1])),
  };
}

const landPolygons = [
  [
    [255, 455], [282, 348], [358, 265], [390, 173], [545, 132], [680, 190],
    [814, 119], [954, 142], [1075, 205], [1200, 151], [1350, 176], [1455, 142],
    [1600, 184], [1748, 236], [1832, 344], [1792, 446], [1710, 514], [1690, 626],
    [1580, 702], [1450, 684], [1330, 755], [1180, 715], [1050, 777], [920, 724],
    [802, 769], [680, 703], [552, 738], [447, 670], [352, 700], [282, 621],
    [248, 536], [214, 474],
  ],
  [[1750, 82], [1815, 58], [1880, 91], [1892, 145], [1845, 178], [1780, 157], [1732, 119]],
  [[1900, 230], [1942, 211], [1974, 253], [1950, 307], [1913, 291]],
  [[934, 815], [996, 789], [1058, 826], [1030, 878], [970, 894], [918, 855]],
  [[126, 363], [181, 341], [218, 379], [204, 428], [157, 441], [116, 410]],
  [[1508, 792], [1561, 778], [1603, 814], [1574, 854], [1528, 844]],
  [[704, 835], [750, 814], [790, 846], [770, 884], [722, 878]],
].map(preparePolygon);

const lakePolygons = [
  [[1110, 300], [1150, 278], [1190, 300], [1178, 344], [1134, 354], [1098, 332]],
  [[520, 460], [548, 444], [578, 460], [565, 490], [530, 494]],
].map(preparePolygon);

function inPreparedPolygon(x, y, polygon) {
  return x >= polygon.minX && x <= polygon.maxX && y >= polygon.minY && y <= polygon.maxY && pointInPolygon(x, y, polygon.points);
}

function isLand(x, y) {
  return landPolygons.some((polygon) => inPreparedPolygon(x, y, polygon))
    && !lakePolygons.some((polygon) => inPreparedPolygon(x, y, polygon));
}

function frontierAt(y) {
  return 1015 + 42 * Math.sin(y / 104) + 15 * Math.sin(y / 37);
}

function stateKeyForPoint(x, y) {
  const country = x < frontierAt(y) ? "VOR" : "OGO";
  const row = y < 360 ? "N" : y < 610 ? "C" : "S";
  const splitX = country === "VOR" ? 635 : 1390;
  return `${country}_${row}${x < splitX ? "W" : "E"}`;
}

function generateProvinceSeeds() {
  const seeds = [];
  for (let y = 125; y <= 885; y += 82) {
    for (let x = 135; x <= 1970; x += 84) {
      const random = hash(x, y);
      const px = x + ((random & 31) - 15) * 1.35;
      const py = y + (((random >>> 8) & 31) - 15) * 1.35;
      if (isLand(px, py)) seeds.push({ x: px, y: py });
    }
  }
  for (const [x, y] of [
    [1805, 119], [1934, 258], [980, 841], [1550, 818], [164, 390], [744, 850],
    [420, 275], [670, 340], [875, 455], [1260, 470], [1490, 410], [1430, 620],
  ]) if (isLand(x, y)) seeds.push({ x, y });
  const distinct = [];
  for (const seed of seeds) {
    if (!distinct.some((other) => (seed.x - other.x) ** 2 + (seed.y - other.y) ** 2 < 42 ** 2)) distinct.push(seed);
  }
  return distinct;
}

const seaCells = [];
for (let seaY = 0; seaY < SEA_ROWS; seaY++) {
  for (let seaX = 0; seaX < SEA_COLUMNS; seaX++) {
    let hasWater = false;
    const startX = Math.floor(seaX * GRID_WIDTH / SEA_COLUMNS);
    const startY = Math.floor(seaY * GRID_HEIGHT / SEA_ROWS);
    const endX = Math.floor((seaX + 1) * GRID_WIDTH / SEA_COLUMNS);
    const endY = Math.floor((seaY + 1) * GRID_HEIGHT / SEA_ROWS);
    for (let gy = startY; gy < endY && !hasWater; gy += 3) {
      for (let gx = startX; gx < endX; gx += 3) {
        if (!isLand(gx * SAMPLE + SAMPLE / 2, gy * SAMPLE + SAMPLE / 2)) {
          hasWater = true;
          break;
        }
      }
    }
    if (hasWater) seaCells.push({ seaX, seaY, id: seaCells.length + 1 });
  }
}
const SEA_COUNT = seaCells.length;
const seaCellIds = new Map(seaCells.map((cell) => [`${cell.seaX},${cell.seaY}`, cell.id]));
const landProvinces = generateProvinceSeeds().map((seed, index) => ({
  id: SEA_COUNT + index + 1,
  seed,
  stateKey: stateKeyForPoint(seed.x, seed.y),
}));
const stateByKey = new Map(STATE_DEFS.map((state) => [state.key, state]));
for (const state of STATE_DEFS) {
  if (!landProvinces.some((province) => province.stateKey === state.key)) throw new Error(`No provinces for ${state.key}`);
}

function nearestProvince(x, y) {
  let nearest = landProvinces[0];
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const province of landProvinces) {
    const distance = (province.seed.x - x) ** 2 + (province.seed.y - y) ** 2;
    if (distance < bestDistance) {
      nearest = province;
      bestDistance = distance;
    }
  }
  return nearest;
}

const provinceGrid = new Uint16Array(GRID_WIDTH * GRID_HEIGHT);
for (let gy = 0; gy < GRID_HEIGHT; gy++) {
  for (let gx = 0; gx < GRID_WIDTH; gx++) {
    const x = gx * SAMPLE + SAMPLE / 2;
    const y = gy * SAMPLE + SAMPLE / 2;
    const offset = gy * GRID_WIDTH + gx;
    if (isLand(x, y)) {
      provinceGrid[offset] = nearestProvince(x, y).id;
    } else {
      const seaX = Math.min(SEA_COLUMNS - 1, Math.floor(gx * SEA_COLUMNS / GRID_WIDTH));
      const seaY = Math.min(SEA_ROWS - 1, Math.floor(gy * SEA_ROWS / GRID_HEIGHT));
      provinceGrid[offset] = seaCellIds.get(`${seaX},${seaY}`);
    }
  }
}
const representedProvinces = new Set(provinceGrid);
const unused = landProvinces.filter((province) => !representedProvinces.has(province.id));
if (unused.length) throw new Error(`Land provinces have no pixels: ${unused.map((province) => province.id).join(", ")}`);

const provinceById = new Map(landProvinces.map((province) => [province.id, province]));
const coastalProvinces = new Set();
for (let gy = 0; gy < GRID_HEIGHT; gy++) {
  for (let gx = 0; gx < GRID_WIDTH; gx++) {
    const id = provinceGrid[gy * GRID_WIDTH + gx];
    if (id <= SEA_COUNT) continue;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nx = gx + dx;
      const ny = gy + dy;
      if (nx < 0 || nx >= GRID_WIDTH || ny < 0 || ny >= GRID_HEIGHT || provinceGrid[ny * GRID_WIDTH + nx] <= SEA_COUNT) {
        coastalProvinces.add(id);
        break;
      }
    }
  }
}

const terrainByProvince = new Map();
for (const province of landProvinces) {
  const state = stateByKey.get(province.stateKey);
  const roll = hash(province.id, 91) % 100;
  let terrain = state.terrain;
  if (state.terrain !== "urban") {
    if (roll < 15) terrain = "plains";
    else if (roll < 24) terrain = "forest";
    else if (roll < 30 && state.terrain !== "mountain") terrain = "hills";
  }
  terrainByProvince.set(province.id, terrain);
}
for (const state of STATE_DEFS) {
  const owned = landProvinces.filter((province) => province.stateKey === state.key);
  state.provinces = owned;
  state.center = owned.reduce((sum, province) => ({
    x: sum.x + province.seed.x / owned.length,
    y: sum.y + province.seed.y / owned.length,
  }), { x: 0, y: 0 });
  state.capitalProvince = owned.reduce((best, province) => {
    const distance = (province.seed.x - state.center.x) ** 2 + (province.seed.y - state.center.y) ** 2;
    return distance < best.distance ? { id: province.id, distance } : best;
  }, { id: owned[0].id, distance: Number.POSITIVE_INFINITY }).id;
  terrainByProvince.set(state.capitalProvince, "urban");
}

function writeRgbBmp(file, pixels, width, height) {
  const rowSize = Math.ceil(width * 3 / 4) * 4;
  const dataSize = rowSize * height;
  const output = Buffer.alloc(54 + dataSize);
  output.write("BM", 0);
  output.writeUInt32LE(output.length, 2);
  output.writeUInt32LE(54, 10);
  output.writeUInt32LE(40, 14);
  output.writeInt32LE(width, 18);
  output.writeInt32LE(height, 22);
  output.writeUInt16LE(1, 26);
  output.writeUInt16LE(24, 28);
  output.writeUInt32LE(dataSize, 34);
  for (let y = 0; y < height; y++) {
    const sourceY = height - 1 - y;
    const rowStart = 54 + y * rowSize;
    for (let x = 0; x < width; x++) {
      const source = (sourceY * width + x) * 3;
      const target = rowStart + x * 3;
      output[target] = pixels[source + 2];
      output[target + 1] = pixels[source + 1];
      output[target + 2] = pixels[source];
    }
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, output);
}

function writeIndexedBmp(file, pixels, width, height, palette) {
  const rowSize = Math.ceil(width / 4) * 4;
  const dataSize = rowSize * height;
  const offset = 1078;
  const output = Buffer.alloc(offset + dataSize);
  output.write("BM", 0);
  output.writeUInt32LE(output.length, 2);
  output.writeUInt32LE(offset, 10);
  output.writeUInt32LE(40, 14);
  output.writeInt32LE(width, 18);
  output.writeInt32LE(height, 22);
  output.writeUInt16LE(1, 26);
  output.writeUInt16LE(8, 28);
  output.writeUInt32LE(dataSize, 34);
  output.writeUInt32LE(256, 46);
  for (let index = 0; index < 256; index++) {
    const color = palette[index] || [index, index, index];
    const target = 54 + index * 4;
    output[target] = color[2];
    output[target + 1] = color[1];
    output[target + 2] = color[0];
  }
  for (let y = 0; y < height; y++) {
    const sourceY = height - 1 - y;
    const rowStart = offset + y * rowSize;
    for (let x = 0; x < width; x++) output[rowStart + x] = pixels[sourceY * width + x];
  }
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, output);
}

function expandGridRgb(pixelForId) {
  const pixels = new Uint8Array(WIDTH * HEIGHT * 3);
  for (let gy = 0; gy < GRID_HEIGHT; gy++) {
    for (let gx = 0; gx < GRID_WIDTH; gx++) {
      const id = provinceGrid[gy * GRID_WIDTH + gx];
      const [r, g, b] = pixelForId(id, gx, gy);
      for (let dy = 0; dy < SAMPLE; dy++) {
        for (let dx = 0; dx < SAMPLE; dx++) {
          const target = ((gy * SAMPLE + dy) * WIDTH + gx * SAMPLE + dx) * 3;
          pixels[target] = r;
          pixels[target + 1] = g;
          pixels[target + 2] = b;
        }
      }
    }
  }
  return pixels;
}

function expandGridValues(valueForId) {
  const pixels = new Uint8Array(WIDTH * HEIGHT);
  for (let gy = 0; gy < GRID_HEIGHT; gy++) {
    for (let gx = 0; gx < GRID_WIDTH; gx++) {
      const id = provinceGrid[gy * GRID_WIDTH + gx];
      const value = valueForId(id, gx, gy);
      for (let dy = 0; dy < SAMPLE; dy++) {
        const row = (gy * SAMPLE + dy) * WIDTH;
        for (let dx = 0; dx < SAMPLE; dx++) pixels[row + gx * SAMPLE + dx] = value;
      }
    }
  }
  return pixels;
}

function provinceColor(id) {
  return [id & 255, (id >>> 8) & 255, (id >>> 16) & 255];
}
const provinceColors = new Map();
for (let id = 1; id <= SEA_COUNT + landProvinces.length; id++) provinceColors.set(id, provinceColor(id));
writeRgbBmp(path.join(ROOT, "map", "provinces.bmp"), expandGridRgb((id) => provinceColors.get(id)), WIDTH, HEIGHT);

const terrainPalette = Array.from({ length: 256 }, (_, index) => [index, index, index]);
for (const [index, color] of [
  [0, [0, 0, 255]], [1, [20, 20, 20]], [2, [0, 110, 45]], [3, [110, 110, 110]],
  [4, [235, 235, 235]], [5, [190, 170, 80]], [6, [0, 170, 170]], [7, [85, 40, 110]], [8, [170, 45, 45]],
]) terrainPalette[index] = color;
const terrainIndices = { plains: 1, forest: 2, hills: 3, mountain: 4, marsh: 6, urban: 8 };
writeIndexedBmp(path.join(ROOT, "map", "terrain.bmp"), expandGridValues((id) => id <= SEA_COUNT ? 0 : terrainIndices[terrainByProvince.get(id)]), WIDTH, HEIGHT, terrainPalette);

function mountainInfluence(x, y) {
  const ridgeA = Math.max(0, 1 - Math.abs(y - (250 + 45 * Math.sin(x / 180))) / 115) * Math.max(0, 1 - Math.abs(x - 1000) / 850);
  const ridgeB = Math.max(0, 1 - Math.abs(x - (1420 + 55 * Math.sin(y / 100))) / 90) * Math.max(0, 1 - Math.abs(y - 590) / 260);
  return Math.max(ridgeA, ridgeB);
}
const grayscale = Array.from({ length: 256 }, (_, index) => [index, index, index]);
writeIndexedBmp(path.join(ROOT, "map", "heightmap.bmp"), expandGridValues((id, gx, gy) => {
  if (id <= SEA_COUNT) return 72;
  const x = gx * SAMPLE;
  const y = gy * SAMPLE;
  const waves = 7 * Math.sin(x / 71) + 5 * Math.cos(y / 59) + 4 * Math.sin((x + y) / 43);
  return Math.max(82, Math.min(235, Math.round(105 + waves + (hash(gx, gy) % 9) - 4 + mountainInfluence(x, y) * 83)));
}), WIDTH, HEIGHT, grayscale);

const riverGrid = new Uint8Array(GRID_WIDTH * GRID_HEIGHT);
function drawRiverPoint(x, y, radius, value) {
  const gx = Math.round(x / SAMPLE);
  const gy = Math.round(y / SAMPLE);
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      if (dx * dx + dy * dy > radius * radius) continue;
      const nx = gx + dx;
      const ny = gy + dy;
      if (nx >= 0 && nx < GRID_WIDTH && ny >= 0 && ny < GRID_HEIGHT) riverGrid[ny * GRID_WIDTH + nx] = value;
    }
  }
}
function drawRiver(points, width = 1, major = false) {
  for (let index = 0; index < points.length - 1; index++) {
    const [x1, y1] = points[index];
    const [x2, y2] = points[index + 1];
    const steps = Math.ceil(Math.hypot(x2 - x1, y2 - y1) / SAMPLE);
    for (let step = 0; step <= steps; step++) {
      const t = step / steps;
      drawRiverPoint(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, width, major ? 3 : 1);
    }
  }
  drawRiverPoint(points[0][0], points[0][1], Math.max(1, width - 1), 2);
}
const frontierRiver = [];
for (let y = 210; y <= 745; y += 35) frontierRiver.push([frontierAt(y), y]);
drawRiver(frontierRiver, 1, true);
drawRiver([[760, 190], [730, 260], [770, 340], [720, 420], [680, 520], [610, 600], [520, 690], [430, 760]], 1);
drawRiver([[1510, 220], [1470, 300], [1505, 380], [1450, 470], [1490, 560], [1570, 650], [1660, 700]], 1);
drawRiver([[360, 300], [430, 340], [470, 410], [450, 490], [380, 560], [300, 600]], 0);
const riverPalette = Array.from({ length: 256 }, () => [0, 0, 0]);
riverPalette[1] = [0, 0, 255];
riverPalette[2] = [0, 255, 0];
riverPalette[3] = [255, 0, 0];
riverPalette[4] = [255, 255, 255];
writeIndexedBmp(path.join(ROOT, "map", "rivers.bmp"), expandGridValues((id, gx, gy) => riverGrid[gy * GRID_WIDTH + gx]), WIDTH, HEIGHT, riverPalette);

let definition = "province;red;green;blue;type;coastal;terrain;continent\n";
for (let id = 1; id <= SEA_COUNT + landProvinces.length; id++) {
  const [red, green, blue] = provinceColors.get(id);
  const isSea = id <= SEA_COUNT;
  definition += `${id};${red};${green};${blue};${isSea ? "sea" : "land"};${!isSea && coastalProvinces.has(id) ? "true" : "false"};${isSea ? "ocean" : terrainByProvince.get(id)};1\n`;
}
writeText("map/definition.csv", definition);

for (const state of STATE_DEFS) {
  const resources = Object.entries(state.resources).map(([key, value]) => `\t\t${key} = ${value}`).join("\n");
  writeText(`history/states/${String(state.id).padStart(3, "0")}-${state.key}.txt`, `state = {
\tid = ${state.id}
\tname = "STATE_${state.id}"
\tmanpower = ${state.manpower}
\tstate_category = ${state.category}
\tprovinces = { ${state.provinces.map((province) => province.id).join(" ")} }
\tresources = {
${resources}
\t}
\thistory = {
\t\towner = ${state.country}
\t\tadd_core_of = ${state.country}
\t\tvictory_points = { ${state.capitalProvince} 5 }
\t\tbuildings = {
\t\t\tinfrastructure = ${state.infrastructure}
\t\t\tindustrial_complex = ${state.industry}
\t\t\tarms_factory = ${state.arms}
\t\t}
\t}
}
`);
}

function capitalFor(country) {
  const target = country === "VOR" ? { x: 850, y: 455 } : { x: 1160, y: 450 };
  const owned = landProvinces.filter((province) => province.stateKey.startsWith(`${country}_`));
  return owned.reduce((best, province) => {
    const distance = (province.seed.x - target.x) ** 2 + (province.seed.y - target.y) ** 2;
    return distance < best.distance ? { id: province.id, distance } : best;
  }, { id: owned[0].id, distance: Number.POSITIVE_INFINITY }).id;
}
const countries = {
  VOR: { name: "Vortex", color: "58 76 96", capital: capitalFor("VOR"), characters: ["VOR_spartak", "VOR_shlang"], template: "Vortex Battalion" },
  OGO: { name: "Ogorod", color: "83 91 62", capital: capitalFor("OGO"), characters: ["OGO_pidofil", "OGO_atamanov", "OGO_ilyich", "OGO_dimbaz", "OGO_bair", "OGO_perchik"], template: "Garden Battalion" },
};
writeText("common/country_tags/first_schism.txt", `VOR = "countries/VOR.txt"\nOGO = "countries/OGO.txt"\n`);
for (const [tag, country] of Object.entries(countries)) {
  writeText(`common/countries/${tag}.txt`, `graphical_culture = eastern_european_gfx
graphical_culture_2d = eastern_european_2d
color = { ${country.color} }
color_ui = { ${country.color} }
`);
  const recruits = country.characters.map((character) => `recruit_character = ${character}`).join("\n");
  writeText(`history/countries/${tag} - ${country.name}.txt`, `capital = ${country.capital}
set_politics = {
\truling_party = neutrality
\telections_allowed = no
}
set_popularities = {
\tneutrality = 75
\tdemocratic = 5
\tcommunism = ${tag === "OGO" ? 12 : 7}
\tfascism = ${tag === "OGO" ? 8 : 13}
}
set_technology = {
\tinfantry_weapons = 1
\tinfantry_weapons1 = 1
\ttech_support = 1
\ttech_recon = 1
\ttech_engineers = 1
\tgw_artillery = 1
}
${recruits}
division_template = {
\tname = "${country.template}"
\tregiments = {
\t\tinfantry = { x = 0 y = 0 }
\t\tinfantry = { x = 0 y = 1 }
\t\tinfantry = { x = 1 y = 0 }
\t\tinfantry = { x = 1 y = 1 }
\t}
\tsupport = {
\t\tengineer = { x = 0 y = 0 }
\t}
}
`);
  const divisions = Array.from({ length: tag === "VOR" ? 5 : 6 }, (_, index) => `\tdivision = {
\t\tname = "${index + 1}. ${tag === "VOR" ? "Вихревой батальон" : "Батальон Огорода"}"
\t\tlocation = ${country.capital}
\t\tdivision_template = "${country.template}"
\t\tstart_experience_factor = 0.15
\t}`).join("\n");
  writeText(`history/units/${tag}_1962.txt`, `units = {\n${divisions}\n}\n`);
}

function writeTga(relativePath, width, height, pixelAt) {
  const header = Buffer.alloc(18);
  header[2] = 2;
  header.writeUInt16LE(width, 12);
  header.writeUInt16LE(height, 14);
  header[16] = 24;
  header[17] = 0x20;
  const output = Buffer.alloc(18 + width * height * 3);
  header.copy(output);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const [r, g, b] = pixelAt(x, y);
      const offset = 18 + (y * width + x) * 3;
      output[offset] = b;
      output[offset + 1] = g;
      output[offset + 2] = r;
    }
  }
  const file = path.join(ROOT, relativePath);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, output);
}
function segmentDistance(px, py, ax, ay, bx, by) {
  const dx = bx - ax;
  const dy = by - ay;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}
function flagColor(country, x, y, width, height) {
  const u = x / width;
  const v = y / height;
  const cx = u - 0.5;
  const cy = v - 0.5;
  const radius = Math.hypot(cx, cy);
  const angle = Math.atan2(cy, cx);
  const line = (ax, ay, bx, by, thickness) => segmentDistance(u, v, ax, ay, bx, by) < thickness;
  const palettes = {
    VOR: [[37, 48, 61], [116, 145, 164]], OGO: [[55, 65, 42], [151, 139, 91]],
    WAG: [[34, 29, 29], [147, 53, 47]], HYD: [[28, 25, 28], [128, 45, 45]],
    RED: [[104, 31, 29], [197, 166, 80]], WAR: [[25, 27, 30], [190, 193, 187]],
    DWA: [[24, 21, 31], [113, 82, 139]], ARE: [[58, 36, 37], [169, 117, 75]], DOL: [[41, 52, 66], [159, 134, 76]],
  };
  const [base, emblem] = palettes[country];
  let marked = false;
  if (country === "VOR") marked = Math.abs(radius - (0.035 + (angle + Math.PI) * 0.035)) < 0.022 && radius < 0.34;
  else if (country === "OGO") marked = line(0.5, 0.2, 0.5, 0.8, 0.025) || line(0.25, 0.38, 0.75, 0.38, 0.025) || line(0.35, 0.18, 0.65, 0.18, 0.025) || (radius < 0.09 && v < 0.35);
  else if (country === "WAG" || country === "WAR") {
    marked = (Math.hypot(cx, cy + 0.05) < 0.19 && v < 0.63) || (Math.abs(cx) < 0.12 && v > 0.5 && v < 0.76);
    if ((Math.hypot(cx - 0.07, cy + 0.06) < 0.04) || (Math.hypot(cx + 0.07, cy + 0.06) < 0.04)) return base;
    if (country === "WAR" && line(0.54, 0.18, 0.45, 0.52, 0.018)) return [142, 44, 40];
  } else if (country === "HYD") marked = Math.hypot(cx, cy) < 0.09 || Math.hypot(cx - 0.16, cy + 0.04) < 0.08 || Math.hypot(cx + 0.16, cy + 0.04) < 0.08 || line(0.34, 0.57, 0.5, 0.68, 0.025) || line(0.66, 0.57, 0.5, 0.68, 0.025);
  else if (country === "RED") marked = line(0.35, 0.25, 0.63, 0.7, 0.035) || line(0.33, 0.25, 0.62, 0.18, 0.04) || (v < 0.28 && radius < 0.12);
  else if (country === "DWA") {
    marked = Math.abs(cy) < 0.16 * (1 - Math.abs(cx) / 0.36) && Math.abs(cx) < 0.36;
    if (marked && radius < 0.075) return base;
    if (radius < 0.035) return emblem;
  } else if (country === "ARE") marked = Math.abs(radius - 0.26) < 0.025 || Math.abs(radius - 0.14) < 0.018;
  else if (country === "DOL") marked = line(0.3, 0.7, 0.3, 0.3, 0.025) || line(0.7, 0.7, 0.7, 0.3, 0.025) || line(0.3, 0.35, 0.5, 0.2, 0.025) || line(0.7, 0.35, 0.5, 0.2, 0.025) || line(0.25, 0.72, 0.75, 0.72, 0.025);
  return marked ? emblem : base;
}
for (const country of Object.keys({ VOR: 1, OGO: 1, WAG: 1, HYD: 1, RED: 1, WAR: 1, DWA: 1, ARE: 1, DOL: 1 })) {
  for (const [relativePath, width, height] of [
    [`gfx/flags/${country}.tga`, 82, 52], [`gfx/flags/medium/${country}.tga`, 41, 26], [`gfx/flags/small/${country}.tga`, 10, 7],
  ]) writeTga(relativePath, width, height, (x, y) => flagColor(country, x, y, width, height));
}

writeText("map/positions.txt", `${landProvinces.map((province) => `${province.id} = {
\tposition = { ${province.seed.x.toFixed(1)} ${province.seed.y.toFixed(1)} }
\trotation = 0.0
}`).join("\n")}\n`);
writeText("map/continents.txt", `continent = {
\tid = 1
\tname = CONTINENT_1
\tprovinces = { ${landProvinces.map((province) => province.id).join(" ")} }
}
`);
const seaStarts = seaCells.filter((cell) => cell.seaX === 0 || cell.seaX === SEA_COLUMNS - 1 || cell.seaY === 0 || cell.seaY === SEA_ROWS - 1).map((cell) => cell.id).join(" ");
writeText("map/default.map", `max_provinces = ${SEA_COUNT + landProvinces.length + 1}
definitions = "definition.csv"
provinces = "provinces.bmp"
positions = "positions.txt"
rivers = "rivers.bmp"
terrain = "terrain.bmp"
heightmap = "heightmap.bmp"
continent = "continents.txt"
adjacencies = "adjacencies.csv"
sea_starts = { ${seaStarts} }
lakes = { }
only_used_for_random = { }
impassable = { }
`);
writeText("map/strategicregions/1.txt", `strategic_region = {
\tid = 1
\tname = STRATEGICREGION_1
\tprovinces = { ${Array.from({ length: SEA_COUNT + landProvinces.length }, (_, index) => index + 1).join(" ")} }
}
`);
writeText("map/supplyareas/1.txt", `supply_area = {
\tid = 1
\tname = "SUPPLYAREA_1"
\tvalue = 12
\tstates = { ${STATE_DEFS.map((state) => state.id).join(" ")} }
}
`);
writeText("map/adjacencies.csv", "From;To;Type;Through;start_x;start_y;stop_x;stop_y;Adjacency Rule;Comment\n-1;-1;;-1;-1;-1;-1;-1;;\n");

const previewPixels = expandGridRgb((id, gx, gy) => {
  if (id <= SEA_COUNT) {
    const shade = (hash(gx, gy) % 7) - 3;
    return [24 + shade, 34 + shade, 43 + shade];
  }
  const state = stateByKey.get(provinceById.get(id).stateKey);
  const noise = (hash(gx, gy) % 11) - 5;
  let color = state.color.map((channel) => Math.max(0, Math.min(255, channel + noise)));
  const right = gx + 1 < GRID_WIDTH ? provinceGrid[gy * GRID_WIDTH + gx + 1] : id;
  const down = gy + 1 < GRID_HEIGHT ? provinceGrid[(gy + 1) * GRID_WIDTH + gx] : id;
  if (right !== id || down !== id) color = [40, 45, 48];
  if (right > SEA_COUNT && down > SEA_COUNT) {
    const rightState = provinceById.get(right)?.stateKey;
    const downState = provinceById.get(down)?.stateKey;
    if ((rightState && rightState !== state.key) || (downState && downState !== state.key)) color = [157, 153, 137];
  }
  if (riverGrid[gy * GRID_WIDTH + gx]) color = [74, 106, 125];
  return color;
});
const previewBmpPath = path.join(ROOT, "preview", "first_stage_map.bmp");
writeRgbBmp(previewBmpPath, previewPixels, WIDTH, HEIGHT);
const previewData = fs.readFileSync(previewBmpPath).toString("base64");
const stateLabels = STATE_DEFS.map((state) => `<text x="${state.center.x.toFixed(0)}" y="${state.center.y.toFixed(0)}" class="state-label">${state.ru}</text>`).join("\n    ");
writeText("preview/first_stage_map.svg", `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="2048" height="1120" viewBox="0 0 2048 1120">
  <rect width="2048" height="1120" fill="#15191d"/>
  <image x="0" y="48" width="2048" height="1024" xlink:href="data:image/bmp;base64,${previewData}"/>
  <g transform="translate(0 48)">
    ${stateLabels}
    <text x="700" y="500" class="country-label">ВИХРЬ</text>
    <text x="1325" y="500" class="country-label">ОГОРОД</text>
  </g>
  <rect width="2048" height="48" fill="#171b1f"/><rect y="1072" width="2048" height="48" fill="#171b1f"/>
  <rect x="40" y="17" width="90" height="4" fill="#8d302c"/>
  <text x="145" y="31" class="title">ПЕРВЫЙ РАСКОЛ / СЕВЕРНЫЙ РУБЕЖ</text>
  <text x="42" y="1103" class="footer">АРХИВ КЛАНОВЫХ ВОЙН · 01.01.1962 · ВИХРЬ / ОГОРОД</text>
  <style>
    .title { fill: #d2cdbf; font: 700 20px Arial, sans-serif; letter-spacing: 4px; }
    .footer { fill: #8f928e; font: 14px Arial, sans-serif; letter-spacing: 3px; }
    .state-label { fill: #ddd7c7; font: 700 16px Arial, sans-serif; text-anchor: middle; paint-order: stroke; stroke: #1c2227; stroke-width: 5px; }
    .country-label { fill: #e2ddcf; opacity: .65; font: 700 50px Arial, sans-serif; letter-spacing: 10px; text-anchor: middle; paint-order: stroke; stroke: #20272c; stroke-width: 8px; }
  </style>
</svg>
`);

const replacePaths = [
  "common/bookmarks", "common/national_focus", "history/countries", "history/states",
  "history/units", "map/strategicregions", "map/supplyareas",
].map((entry) => `replace_path="${entry}"`).join("\n");
const descriptor = `name="The First Schism"
version="0.2.0"
tags={
\t"Alternative History"
\t"Map"
\t"National Focuses"
\t"Events"
}
supported_version="1.19.*"
${replacePaths}
`;
writeText("descriptor.mod", descriptor);
writeText("The First Schism.mod", descriptor.replace('supported_version="1.19.*"', 'supported_version="1.19.*"\npath="mod/The First Schism"'));
writeText("common/bookmarks/first_schism.txt", `bookmarks = {
\tbookmark = {
\t\tname = FIRST_SCHISM
\t\tdesc = FIRST_SCHISM_DESC
\t\tdate = 1962.1.1
\t\tpicture = GFX_select_date_1936
\t\tdefault_country = VOR
\t\tselectable_countries = { VOR OGO }
\t}
}
`);
writeText("common/defines/first_schism.lua", `NGame = {
\tSTART_DATE = "1962.1.1"
\tEND_DATE = "1975.1.1"
}
`);

const stateLocEn = STATE_DEFS.map((state) => ` STATE_${state.id}:0 "${state.en}"`).join("\n");
const stateLocRu = STATE_DEFS.map((state) => ` STATE_${state.id}:0 "${state.ru}"`).join("\n");
const vpLocEn = STATE_DEFS.map((state) => ` VICTORY_POINTS_${state.capitalProvince}:0 "${state.vpEn}"`).join("\n");
const vpLocRu = STATE_DEFS.map((state) => ` VICTORY_POINTS_${state.capitalProvince}:0 "${state.vpRu}"`).join("\n");
writeText("localisation/english/first_schism_l_english.yml", `\uFEFFl_english:
 FIRST_SCHISM:0 "The First Schism"
 FIRST_SCHISM_DESC:0 "The old friendship is dead. Across the Northern March, Vortex and Ogorod prepare to turn a community dispute into the first clan war."
 CONTINENT_1:0 "Northern March"
 STRATEGICREGION_1:0 "The Northern March"
 SUPPLYAREA_1:0 "Northern March Supply District"
 VOR:0 "Vortex"
 VOR_DEF:0 "Vortex"
 VOR_ADJ:0 "Vortex"
 OGO:0 "Ogorod"
 OGO_DEF:0 "Ogorod"
 OGO_ADJ:0 "Ogorod"
${stateLocEn}
${vpLocEn}
`);
writeText("localisation/russian/first_schism_l_russian.yml", `\uFEFFl_russian:
 FIRST_SCHISM:0 "Первый раскол"
 FIRST_SCHISM_DESC:0 "Прежняя дружба мертва. На Северном Рубеже Вихрь и Огород готовятся превратить внутренний спор в первую клановую войну."
 CONTINENT_1:0 "Северный Рубеж"
 STRATEGICREGION_1:0 "Северный Рубеж"
 SUPPLYAREA_1:0 "Район снабжения Северного Рубежа"
 VOR:0 "Вихрь"
 VOR_DEF:0 "Вихрь"
 VOR_ADJ:0 "Вихревой"
 OGO:0 "Огород"
 OGO_DEF:0 "Огород"
 OGO_ADJ:0 "Огородный"
${stateLocRu}
${vpLocRu}
`);
console.log(`Generated ${landProvinces.length} land provinces, ${SEA_COUNT} sea provinces, ${STATE_DEFS.length} states, and ${WIDTH}x${HEIGHT} maps.`);
