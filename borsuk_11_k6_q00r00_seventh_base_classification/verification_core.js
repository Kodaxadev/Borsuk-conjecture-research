#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const N = 11;
const K = 6;
const COLORS = 12;
const CLAUSES_PER_VERTEX_RAW = 67;
const CLAUSES_PER_EDGE_RAW = 12;
const CLAIM_ID = 'n11-k6-q00r00-seventh-base-classification';
const SOURCE_MANIFEST_SHA256 = '559f83e4eb245902b9ec1808812248694c7931a535213c45b50d7a89a461e5fa';

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) out[args[i].replace(/^--/, '')] = args[i + 1];
  if (!out['trim-root'] || !out.generated || !out.output) {
    throw new Error('usage: verify_independent.js --trim-root DIR --generated DIR --output FILE');
  }
  return out;
}

function sha256Buffer(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}
function sha256File(file) { return sha256Buffer(fs.readFileSync(file)); }
function popcount(value) {
  let count = 0;
  let x = value >>> 0;
  while (x) { x &= x - 1; count += 1; }
  return count;
}
function distance(a, b) { return popcount(a ^ b); }
function allowed(vertex, base) {
  return popcount(vertex) % 2 === 0 && base.every(point => distance(vertex, point) <= K);
}
function permuteBits(vertex, q) {
  let result = 0;
  for (let output = 0; output < N; output += 1) {
    if ((vertex >> q[output]) & 1) result |= (1 << output);
  }
  return result;
}
function applyTransform(vertex, transform) {
  return permuteBits(vertex, transform.q) ^ transform.t;
}
function compose(left, right) {
  return {
    t: permuteBits(right.t, left.q) ^ left.t,
    q: left.q.map(input => right.q[input]),
  };
}
function transformKey(transform) { return `${transform.t}|${transform.q.join(',')}`; }
function compareArrays(a, b) {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i += 1) if (a[i] !== b[i]) return a[i] - b[i];
  return a.length - b.length;
}
function compareTransforms(a, b) { return a.t - b.t || compareArrays(a.q, b.q); }

function* permutations(values) {
  if (values.length <= 1) { yield values.slice(); return; }
  for (let i = 0; i < values.length; i += 1) {
    const rest = values.slice(0, i).concat(values.slice(i + 1));
    for (const tail of permutations(rest)) yield [values[i], ...tail];
  }
}

function coordinateGroups(base) {
  const groups = new Map();
  for (let coordinate = 0; coordinate < N; coordinate += 1) {
    let pattern = 0;
    for (let i = 0; i < base.length; i += 1) pattern |= (((base[i] >> coordinate) & 1) << i);
    if (!groups.has(pattern)) groups.set(pattern, []);
    groups.get(pattern).push(coordinate);
  }
  return groups;
}
function profile(groups) {
  return [...groups.entries()].sort((a, b) => a[0] - b[0]).map(([key, values]) => [key, values.length]);
}
function equalProfiles(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

function setwiseStabilizer(base) {
  if (base[0] !== 0 || new Set(base).size !== base.length) throw new Error('bad base');
  const baseSet = new Set(base);
  const sourceGroups = coordinateGroups(base);
  const sourceProfile = profile(sourceGroups);
  const dedup = new Map();
  const indices = [...base.keys()];

  for (const sigma of permutations(indices)) {
    const translation = base[sigma[0]];
    const targets = sigma.map(index => base[index] ^ translation);
    const targetGroups = coordinateGroups(targets);
    if (!equalProfiles(sourceProfile, profile(targetGroups))) continue;
    const patterns = [...sourceGroups.keys()].sort((a, b) => a - b);
    const options = patterns.map(pattern => {
      const targetCoordinates = targetGroups.get(pattern);
      return [...permutations(sourceGroups.get(pattern))].map(sourceOrder => ({ targetCoordinates, sourceOrder }));
    });
    const recurse = (depth, q) => {
      if (depth === options.length) {
        const transform = { t: translation, q: q.slice() };
        const images = new Set(base.map(vertex => applyTransform(vertex, transform)));
        if (images.size !== baseSet.size || [...images].some(vertex => !baseSet.has(vertex))) throw new Error('invalid transform');
        dedup.set(transformKey(transform), transform);
        return;
      }
      for (const choice of options[depth]) {
        const next = q.slice();
        choice.targetCoordinates.forEach((target, i) => { next[target] = choice.sourceOrder[i]; });
        recurse(depth + 1, next);
      }
    };
    recurse(0, Array(N).fill(-1));
  }
  const transforms = [...dedup.values()].sort(compareTransforms);
  const keys = new Set(transforms.map(transformKey));
  if (!keys.has(transformKey({ t: 0, q: [...Array(N).keys()] }))) throw new Error('identity missing');
  for (const left of transforms) for (const right of transforms) {
    if (!keys.has(transformKey(compose(left, right)))) throw new Error('group closure failed');
  }
  return transforms;
}
function inducedBasePermutation(base, transform) {
  const index = new Map(base.map((vertex, i) => [vertex, i]));
  return base.map(vertex => index.get(applyTransform(vertex, transform)));
}
function partition(candidates, group) {
  const candidateSet = new Set(candidates);
  const unseen = new Set(candidates);
  const orbits = [];
  while (unseen.size) {
    const representative = Math.min(...unseen);
    const members = [...new Set(group.map(transform => applyTransform(representative, transform)))].sort((a, b) => a - b);
    for (const member of members) {
      if (!candidateSet.has(member)) throw new Error('orbit left candidates');
      unseen.delete(member);
    }
    orbits.push(members);
  }
  const flat = orbits.flat().slice().sort((a, b) => a - b);
  if (JSON.stringify(flat) !== JSON.stringify(candidates)) throw new Error('partition mismatch');
  return orbits;
}
function graphStats(vertices) {
  const vertexHash = crypto.createHash('sha256');
  for (const vertex of vertices) vertexHash.update(vertex.toString(16).padStart(3, '0') + '\n', 'ascii');
  let edges = 0;
  let incompatible = 0;
  for (let i = 0; i < vertices.length; i += 1) {
    for (let j = i + 1; j < vertices.length; j += 1) {
      const d = distance(vertices[i], vertices[j]);
      if (d === K) edges += 1;
      else if (d > K) incompatible += 1;
    }
  }
  return { vertices: vertices.length, vertices_sha256: vertexHash.digest('hex'), distance6_edges: edges, incompatible_pairs: incompatible };
}
function complexityTier(clauses) {
  if (clauses <= 100000) return 'PILOT';
  if (clauses <= 150000) return 'SMALL';
  if (clauses <= 200000) return 'MEDIUM';
  return 'LARGE';
}
function stableStringify(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(stableStringify).join(',') + ']';
  const keys = Object.keys(value).sort();
  return '{' + keys.map(key => JSON.stringify(key) + ':' + stableStringify(value[key])).join(',') + '}';
}
function readVertices(file) {
  const text = fs.readFileSync(file, 'ascii');
  if (text && !text.endsWith('\n')) throw new Error(`noncanonical vertex file ${file}`);
  const values = text.trim() ? text.trimEnd().split('\n').map(line => parseInt(line, 16)) : [];
  const sorted = [...new Set(values)].sort((a, b) => a - b);
  if (JSON.stringify(values) !== JSON.stringify(sorted)) throw new Error('vertex order mismatch');
  return values;
}


module.exports = {
  fs, path, crypto, N, K, COLORS, CLAUSES_PER_VERTEX_RAW, CLAUSES_PER_EDGE_RAW,
  CLAIM_ID, SOURCE_MANIFEST_SHA256, parseArgs, sha256File, distance, allowed,
  applyTransform, setwiseStabilizer, inducedBasePermutation, partition, graphStats,
  complexityTier, stableStringify, readVertices,
};
