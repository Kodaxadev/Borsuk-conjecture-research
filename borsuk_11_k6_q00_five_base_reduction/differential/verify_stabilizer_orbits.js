#!/usr/bin/env node
'use strict';

const crypto = require('crypto');

const N = 11;
const K = 6;
const BASE = [0, 63, 455, 1611];
const EXPECTED_STABILIZER = 384;
const EXPECTED_ORBITS = 12;
const EXPECTED_HASH = '01b3ee2e629788037f1ccd6906140302abddd1ae1c077aa8cf7e8f619adb807a';
const FIELDS = ['id','D','orbit_size','weight','distances_to_q00_base','vertices','exact_distance_edges','incompatible_pairs','vertex_sha256','base5_signature'];

function popcount(value) {
  let count = 0;
  while (value) { value &= value - 1; count++; }
  return count;
}
function distance(a, b) { return popcount(a ^ b); }
function allowed(mask, bases) {
  return popcount(mask) % 2 === 0 && bases.every(base => distance(mask, base) <= K);
}
function permutations(values) {
  if (values.length <= 1) return [values.slice()];
  const output = [];
  for (let i = 0; i < values.length; i++) {
    const rest = values.slice(0, i).concat(values.slice(i + 1));
    for (const tail of permutations(rest)) output.push([values[i]].concat(tail));
  }
  return output;
}
function cartesian(arrays, index = 0, prefix = [], output = []) {
  if (index === arrays.length) { output.push(prefix.slice()); return output; }
  for (const value of arrays[index]) {
    prefix.push(value);
    cartesian(arrays, index + 1, prefix, output);
    prefix.pop();
  }
  return output;
}
function signatures(points) {
  const origin = points[0];
  const result = [];
  for (let coordinate = 0; coordinate < N; coordinate++) {
    const bits = [];
    for (let index = 1; index < points.length; index++) {
      bits.push(((points[index] ^ origin) >> coordinate) & 1);
    }
    result.push(bits.join(''));
  }
  return result;
}
function groupedPositions(values) {
  const groups = new Map();
  values.forEach((value, index) => {
    if (!groups.has(value)) groups.set(value, []);
    groups.get(value).push(index);
  });
  return groups;
}
function multisetKey(values) {
  const counts = new Map();
  values.forEach(value => counts.set(value, (counts.get(value) || 0) + 1));
  return [...counts.entries()].sort().map(([key, count]) => `${key}:${count}`).join('|');
}
function buildStabilizer() {
  const sourceSignatures = signatures(BASE);
  const sourceGroups = groupedPositions(sourceSignatures);
  const keys = [...sourceGroups.keys()].sort();
  const maps = new Map();
  for (const sigma of permutations([0,1,2,3])) {
    const target = sigma.map(index => BASE[index]);
    const targetSignatures = signatures(target);
    if (multisetKey(sourceSignatures) !== multisetKey(targetSignatures)) continue;
    const targetGroups = groupedPositions(targetSignatures);
    const choices = keys.map(key => permutations(targetGroups.get(key)));
    for (const selection of cartesian(choices)) {
      const coordinateMap = new Array(N);
      keys.forEach((key, groupIndex) => {
        sourceGroups.get(key).forEach((oldCoordinate, itemIndex) => {
          coordinateMap[oldCoordinate] = selection[groupIndex][itemIndex];
        });
      });
      const translation = BASE[sigma[0]];
      const transform = mask => {
        let image = translation;
        for (let oldCoordinate = 0; oldCoordinate < N; oldCoordinate++) {
          if ((mask >> oldCoordinate) & 1) image ^= 1 << coordinateMap[oldCoordinate];
        }
        return image;
      };
      const baseImage = BASE.map(transform);
      if (baseImage.some((value, index) => value !== target[index])) throw new Error('bad affine stabilizer map');
      const key = [transform(0), ...Array.from({length:N}, (_, c) => transform(1 << c))].join(',');
      maps.set(key, transform);
    }
  }
  const output = [...maps.values()];
  if (output.length !== EXPECTED_STABILIZER) throw new Error(`stabilizer ${output.length}`);
  return output;
}
function compareArrays(left, right) {
  for (let index = 0; index < left.length; index++) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return 0;
}
function canonicalPointSignature(points) {
  let best = null;
  for (let originIndex = 0; originIndex < points.length; originIndex++) {
    const origin = points[originIndex];
    const translated = points.filter((_, index) => index !== originIndex).map(point => point ^ origin);
    for (const order of permutations(translated)) {
      const counts = new Array(1 << (points.length - 1)).fill(0);
      for (let coordinate = 0; coordinate < N; coordinate++) {
        let signature = 0;
        order.forEach((mask, index) => { signature |= (((mask >> coordinate) & 1) << index); });
        counts[signature]++;
      }
      if (best === null || compareArrays(counts, best) < 0) best = counts;
    }
  }
  return best.join('-');
}
function vertexHash(vertices) {
  const text = vertices.map(vertex => vertex.toString(16).padStart(3,'0') + '\n').join('');
  return crypto.createHash('sha256').update(text, 'ascii').digest('hex');
}
function childStats(d) {
  const bases = BASE.concat([d]);
  const vertices = [];
  for (let mask = 0; mask < (1 << N); mask++) if (allowed(mask, bases)) vertices.push(mask);
  let exact = 0, incompatible = 0;
  for (let i = 0; i < vertices.length; i++) {
    for (let j = i + 1; j < vertices.length; j++) {
      const separation = distance(vertices[i], vertices[j]);
      if (separation === K) exact++;
      else if (separation > K) incompatible++;
    }
  }
  return {vertices: vertices.length, exact, incompatible, hash: vertexHash(vertices)};
}
function generateRows() {
  const transforms = buildStabilizer();
  const parent = [];
  for (let mask = 0; mask < (1 << N); mask++) if (allowed(mask, BASE)) parent.push(mask);
  if (parent.length !== 436) throw new Error(`parent size ${parent.length}`);
  const baseSet = new Set(BASE);
  const candidates = new Set(parent.filter(value => !baseSet.has(value)));
  const unseen = new Set(candidates);
  const orbits = [];
  while (unseen.size) {
    const seed = Math.min(...unseen);
    const orbit = [...new Set(transforms.map(transform => transform(seed)))].sort((a,b) => a-b);
    orbit.forEach(value => {
      if (!candidates.has(value)) throw new Error('orbit escaped');
      unseen.delete(value);
    });
    orbits.push(orbit);
  }
  orbits.sort((left,right) => left[0]-right[0]);
  if (orbits.length !== EXPECTED_ORBITS || orbits.reduce((sum, orbit) => sum + orbit.length, 0) !== 432) {
    throw new Error('orbit partition mismatch');
  }
  return orbits.map((orbit, index) => {
    const d = orbit[0];
    const stat = childStats(d);
    return {
      id: `f${String(index).padStart(2,'0')}`,
      D: d,
      orbit_size: orbit.length,
      weight: popcount(d),
      distances_to_q00_base: BASE.map(base => distance(d, base)).join('-'),
      vertices: stat.vertices,
      exact_distance_edges: stat.exact,
      incompatible_pairs: stat.incompatible,
      vertex_sha256: stat.hash,
      base5_signature: canonicalPointSignature(BASE.concat([d])),
    };
  });
}
function csvEscape(value) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g,'""')}"` : text;
}
function renderCsv(rows) {
  return FIELDS.join(',') + '\n' + rows.map(row => FIELDS.map(field => csvEscape(row[field])).join(',')).join('\n') + '\n';
}

const rows = generateRows();
const csv = renderCsv(rows);
const digest = crypto.createHash('sha256').update(csv, 'ascii').digest('hex');
if (digest !== EXPECTED_HASH) throw new Error(`CSV hash ${digest}`);
console.log(JSON.stringify({
  status:'PASS',
  role:'differential verifier only',
  stabilizer_order:EXPECTED_STABILIZER,
  candidates:432,
  orbits:rows.length,
  child_range:[Math.min(...rows.map(r=>r.vertices)),Math.max(...rows.map(r=>r.vertices))],
  csv_sha256:digest,
  claim_status_changed:false,
  child_status_changed:false,
  theorem_status_changed:false
}, null, 2));
