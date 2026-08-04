#!/usr/bin/env node
'use strict';

const crypto = require('crypto');

const N = 11;
const K = 6;
const A = 63;
const B_CASES = {a1b1: 65, a2b0: 3, a2b2: 195, a3b1: 71, a3b3: 455};
const EXPECTED_POINTWISE = {a1b1: 24, a2b0: 19, a2b2: 36, a3b1: 35, a3b3: 35};
const EXPECTED_SETWISE = {a1b1: 19, a2b0: 19, a2b2: 26, a3b1: 23, a3b3: 14};
const EXPECTED_RAW_CSV_SHA256 = 'e60f5f81120e42c8c7eae2da299105e802266f6e92629cd6ac6ee24bcef9db19';
const EXPECTED_CANONICAL_CSV_SHA256 = '08913feaddbc0f930b6ef90a1677fbc4577cb23dcb6f4dac8987e37056d34742';

function popcount(value) {
  let count = 0;
  let x = value;
  while (x !== 0) {
    x &= x - 1;
    count += 1;
  }
  return count;
}

function distance(left, right) {
  return popcount(left ^ right);
}

function allowed(mask, bases) {
  return popcount(mask) % 2 === 0 && bases.every((base) => distance(mask, base) <= K);
}

function permutations(values) {
  if (values.length === 0) return [[]];
  const output = [];
  for (let index = 0; index < values.length; index += 1) {
    const rest = values.slice(0, index).concat(values.slice(index + 1));
    for (const tail of permutations(rest)) output.push([values[index], ...tail]);
  }
  return output;
}

function blocksFor(b) {
  const mapping = new Map();
  for (let coordinate = 0; coordinate < N; coordinate += 1) {
    const signature = `${(A >> coordinate) & 1}${(b >> coordinate) & 1}`;
    if (!mapping.has(signature)) mapping.set(signature, []);
    mapping.get(signature).push(coordinate);
  }
  return [...mapping.entries()].sort((left, right) => left[0].localeCompare(right[0]));
}

function keyFor(mask, blocks) {
  return blocks.map(([, positions]) => positions.reduce(
    (sum, coordinate) => sum + ((mask >> coordinate) & 1),
    0,
  ));
}

function keyString(key) {
  return key.join(',');
}

function representative(key, blocks) {
  let mask = 0;
  key.forEach((count, blockIndex) => {
    for (let index = 0; index < count; index += 1) {
      mask |= 1 << blocks[blockIndex][1][index];
    }
  });
  return mask;
}

function makeIsometry(b, sigma) {
  const base = [0, A, b];
  const translation = base[sigma[0]];
  const source = new Map();
  const target = new Map();

  for (let coordinate = 0; coordinate < N; coordinate += 1) {
    const signature = `${(A >> coordinate) & 1}${(b >> coordinate) & 1}`;
    if (!source.has(signature)) source.set(signature, []);
    source.get(signature).push(coordinate);
  }
  for (let coordinate = 0; coordinate < N; coordinate += 1) {
    const first = ((base[sigma[1]] >> coordinate) & 1) ^ ((translation >> coordinate) & 1);
    const second = ((base[sigma[2]] >> coordinate) & 1) ^ ((translation >> coordinate) & 1);
    const signature = `${first}${second}`;
    if (!target.has(signature)) target.set(signature, []);
    target.get(signature).push(coordinate);
  }

  for (const [signature, positions] of source.entries()) {
    if (!target.has(signature) || target.get(signature).length !== positions.length) return null;
  }

  const coordinateMap = [];
  for (const [signature, positions] of source.entries()) {
    positions.forEach((oldCoordinate, index) => {
      coordinateMap.push([oldCoordinate, target.get(signature)[index]]);
    });
  }

  return (mask) => {
    let image = translation;
    for (const [oldCoordinate, newCoordinate] of coordinateMap) {
      if ((mask >> oldCoordinate) & 1) image ^= 1 << newCoordinate;
    }
    return image;
  };
}

function vertexHash(vertices) {
  const text = vertices.map((vertex) => vertex.toString(16).padStart(3, '0')).join('\n') + '\n';
  return crypto.createHash('sha256').update(text, 'ascii').digest('hex');
}

function trimStats(base) {
  const vertices = [];
  for (let mask = 0; mask < (1 << N); mask += 1) {
    if (allowed(mask, base)) vertices.push(mask);
  }
  let exactDistanceEdges = 0;
  let incompatiblePairs = 0;
  for (let index = 0; index < vertices.length; index += 1) {
    for (let next = index + 1; next < vertices.length; next += 1) {
      const d = distance(vertices[index], vertices[next]);
      if (d === K) exactDistanceEdges += 1;
      else if (d > K) incompatiblePairs += 1;
    }
  }
  return {
    vertices: vertices.length,
    exact_distance_edges: exactDistanceEdges,
    incompatible_pairs: incompatiblePairs,
    vertex_sha256: vertexHash(vertices),
  };
}

const rows = ['id,family,B,C,vertices,exact_distance_edges,incompatible_pairs,vertex_sha256'];
const rawCases = [];
let totalPointwise = 0;
let totalSetwise = 0;
let minTrim = Number.MAX_SAFE_INTEGER;
let maxTrim = 0;

for (const [family, b] of Object.entries(B_CASES)) {
  const base3 = [0, A, b];
  const blocks = blocksFor(b);
  const groups = new Map();
  for (let c = 0; c < (1 << N); c += 1) {
    if (base3.includes(c) || !allowed(c, base3)) continue;
    const key = keyFor(c, blocks);
    groups.set(keyString(key), key);
  }
  if (groups.size !== EXPECTED_POINTWISE[family]) {
    throw new Error(`${family}: pointwise count ${groups.size}`);
  }

  const isometries = [];
  for (const sigma of permutations([0, 1, 2])) {
    let valid = true;
    for (let left = 0; left < 3; left += 1) {
      for (let right = 0; right < 3; right += 1) {
        if (distance(base3[left], base3[right]) !== distance(base3[sigma[left]], base3[sigma[right]])) valid = false;
      }
    }
    if (valid) {
      const transform = makeIsometry(b, sigma);
      if (transform === null) throw new Error(`${family}: missing isometry`);
      isometries.push(transform);
    }
  }

  const unseen = new Set(groups.keys());
  let caseIndex = 0;
  while (unseen.size > 0) {
    const seedString = [...unseen].sort()[0];
    const seed = groups.get(seedString);
    const orbit = new Map([[seedString, seed]]);
    const queue = [seed];
    while (queue.length > 0) {
      const key = queue.pop();
      const c = representative(key, blocks);
      for (const transform of isometries) {
        const imageKey = keyFor(transform(c), blocks);
        const serialized = keyString(imageKey);
        if (!groups.has(serialized)) throw new Error(`${family}: orbit escaped`);
        if (!orbit.has(serialized)) {
          orbit.set(serialized, imageKey);
          queue.push(imageKey);
        }
      }
    }
    for (const serialized of orbit.keys()) unseen.delete(serialized);

    const representativeKey = [...orbit.values()].sort((left, right) => keyString(left).localeCompare(keyString(right)))[0];
    const c = representative(representativeKey, blocks);
    const id = `${family}_${String(caseIndex).padStart(2, '0')}`;
    const actual = {B: b, C: c, ...trimStats([0, A, b, c])};
    rawCases.push({id, family, ...actual});
    rows.push([id, family, actual.B, actual.C, actual.vertices, actual.exact_distance_edges, actual.incompatible_pairs, actual.vertex_sha256].join(','));
    minTrim = Math.min(minTrim, actual.vertices);
    maxTrim = Math.max(maxTrim, actual.vertices);
    caseIndex += 1;
  }

  if (caseIndex !== EXPECTED_SETWISE[family]) throw new Error(`${family}: setwise count ${caseIndex}`);
  totalPointwise += groups.size;
  totalSetwise += caseIndex;
  console.log(`${family} ${groups.size} ${caseIndex}`);
}

function canonicalBaseSignature(points) {
  let best = null;
  for (let originIndex = 0; originIndex < points.length; originIndex += 1) {
    const origin = points[originIndex];
    const translated = points.filter((_, index) => index !== originIndex).map((point) => point ^ origin);
    for (const permutation of permutations(translated)) {
      const counts = Array(8).fill(0);
      for (let coordinate = 0; coordinate < N; coordinate += 1) {
        let signature = 0;
        for (let index = 0; index < 3; index += 1) {
          signature += ((permutation[index] >> coordinate) & 1) << index;
        }
        counts[signature] += 1;
      }
      const serialized = counts.map((value) => String(value).padStart(2, '0')).join(',');
      if (best === null || serialized < best.serialized) best = {counts, serialized};
    }
  }
  return best.counts;
}

const rawCsv = rows.join('\n') + '\n';
const rawHash = crypto.createHash('sha256').update(rawCsv, 'ascii').digest('hex');
if (totalPointwise !== 149 || totalSetwise !== 101) throw new Error(`raw totals ${totalPointwise} ${totalSetwise}`);
if (rawHash !== EXPECTED_RAW_CSV_SHA256) throw new Error(`raw case-list hash ${rawHash}`);

const grouped = new Map();
for (const record of rawCases) {
  const signature = canonicalBaseSignature([0, A, record.B, record.C]);
  const key = signature.join('-');
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(record);
}
const canonicalRows = ['id,representative_case,members,member_count,B,C,vertices,exact_distance_edges,incompatible_pairs,vertex_sha256,base_signature'];
let canonicalIndex = 0;
for (const key of [...grouped.keys()].sort((left, right) => {
  const l = left.split('-').map(Number);
  const r = right.split('-').map(Number);
  for (let i = 0; i < l.length; i += 1) {
    if (l[i] !== r[i]) return l[i] - r[i];
  }
  return 0;
})) {
  const members = grouped.get(key).sort((left, right) => left.id.localeCompare(right.id));
  const representative = members[0];
  for (const member of members) {
    for (const field of ['vertices', 'exact_distance_edges', 'incompatible_pairs']) {
      if (member[field] !== representative[field]) throw new Error(`${key}: inconsistent ${field}`);
    }
  }
  canonicalRows.push([
    `q${String(canonicalIndex).padStart(2, '0')}`,
    representative.id,
    members.map((member) => member.id).join(';'),
    members.length,
    representative.B,
    representative.C,
    representative.vertices,
    representative.exact_distance_edges,
    representative.incompatible_pairs,
    representative.vertex_sha256,
    key,
  ].join(','));
  canonicalIndex += 1;
}
const canonicalCsv = canonicalRows.join('\n') + '\n';
const canonicalHash = crypto.createHash('sha256').update(canonicalCsv, 'ascii').digest('hex');
if (canonicalIndex !== 58 || minTrim !== 436 || maxTrim !== 612) {
  throw new Error(`canonical totals ${canonicalIndex} ${minTrim} ${maxTrim}`);
}
if (canonicalHash !== EXPECTED_CANONICAL_CSV_SHA256) throw new Error(`canonical case-list hash ${canonicalHash}`);
console.log(`PASS pointwise=${totalPointwise} intermediate=${totalSetwise} canonical=${canonicalIndex} trim_range=${minTrim}-${maxTrim} csv_sha256=${canonicalHash}`);
