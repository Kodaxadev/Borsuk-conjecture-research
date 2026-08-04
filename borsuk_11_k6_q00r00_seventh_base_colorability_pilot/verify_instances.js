#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const N = 11;
const K = 6;
const COLORS = 12;
const SOURCE_STREAM = '932c4ed2ffc689ce5b5fe5cea07eec9876734159186df70b598b6f3ec316f6de';
const PILOT_CASES = [
  'q00r00-s026-t066','q00r00-s028-t116','q00r00-s028-t144','q00r00-s028-t148','q00r00-s028-t154',
  'q00r00-s030-t084','q00r00-s030-t086','q00r00-s031-t041','q00r00-s033-t084','q00r00-s034-t025',
  'q00r00-s034-t028','q00r00-s034-t033','q00r00-s034-t034','q00r00-s034-t035','q00r00-s035-t008',
];

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!args[i].startsWith('--') || i + 1 >= args.length) throw new Error('bad arguments');
    out[args[i].slice(2)] = args[i + 1];
  }
  if (!out['classification-root'] || !out.instances) throw new Error('--classification-root and --instances are required');
  return out;
}

function sha256(data) { return crypto.createHash('sha256').update(data).digest('hex'); }
function sha256File(file) { return sha256(fs.readFileSync(file)); }
function distance(a, b) { let x = a ^ b, n = 0; while (x) { x &= x - 1; n++; } return n; }
function popcount(x) { let n = 0; while (x) { x &= x - 1; n++; } return n; }
function allowed(v, base) { return popcount(v) % 2 === 0 && base.every(p => distance(v, p) <= K); }

function stableObject(value) {
  if (Array.isArray(value)) return value.map(stableObject);
  if (value && typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = stableObject(value[key]);
    return out;
  }
  return value;
}

function reconstruct(base) {
  const vertices = [];
  for (let v = 0; v < (1 << N); v++) if (allowed(v, base)) vertices.push(v);
  const edges = [];
  let incompatible = 0;
  for (let i = 0; i < vertices.length; i++) {
    for (let j = i + 1; j < vertices.length; j++) {
      const d = distance(vertices[i], vertices[j]);
      if (d === K) edges.push([vertices[i], vertices[j]]);
      else if (d > K) incompatible++;
    }
  }
  return {vertices, edges, incompatible};
}

function deterministicClique(vertices, edges) {
  const degree = new Map(vertices.map(v => [v, 0]));
  for (const [a, b] of edges) { degree.set(a, degree.get(a) + 1); degree.set(b, degree.get(b) + 1); }
  const ordered = [...vertices].sort((a, b) => degree.get(b) - degree.get(a) || a - b);
  const clique = [];
  for (const v of ordered) {
    if (clique.every(u => distance(v, u) === K)) {
      clique.push(v);
      if (clique.length === COLORS) break;
    }
  }
  if (!clique.length) throw new Error('empty clique');
  return clique;
}

function domains(vertices, clique) {
  const fixed = new Map(clique.map((v, c) => [v, c]));
  const result = new Map();
  for (const v of vertices) {
    let d;
    if (fixed.has(v)) d = [fixed.get(v)];
    else {
      d = [];
      for (let c = 0; c < COLORS; c++) {
        if (c >= clique.length || distance(v, clique[c]) !== K) d.push(c);
      }
    }
    if (!d.length) throw new Error(`empty domain ${v}`);
    result.set(v, d);
  }
  return result;
}

function variableMaps(vertices, dom) {
  const forward = new Map();
  const reverse = [];
  let next = 1;
  for (const v of vertices) for (const c of dom.get(v)) {
    forward.set(`${v}:${c}`, next);
    reverse.push({variable: next, vertex: v, color: c});
    next++;
  }
  return {forward, reverse};
}

function formulaCounts(vertices, edges, dom) {
  let variables = 0, clauses = 0;
  const masks = new Map();
  for (const v of vertices) {
    const d = dom.get(v);
    variables += d.length;
    clauses += 1 + d.length * (d.length - 1) / 2;
    let mask = 0; for (const c of d) mask |= (1 << c); masks.set(v, mask);
  }
  for (const [a, b] of edges) clauses += popcount(masks.get(a) & masks.get(b));
  return {variables, clauses, masks};
}

function emitCnf(caseId, vertices, edges, dom) {
  const {forward} = variableMaps(vertices, dom);
  const {variables, clauses, masks} = formulaCounts(vertices, edges, dom);
  const lines = [
    `c ${caseId} canonical compact 12-color CNF`,
    'c Variables are ordered by ascending vertex then ascending allowed color.',
    'c Greedy clique order is descending degree then ascending vertex.',
    `p cnf ${variables} ${clauses}`,
  ];
  for (const v of vertices) {
    const ids = dom.get(v).map(c => forward.get(`${v}:${c}`));
    lines.push(ids.join(' ') + ' 0');
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) lines.push(`-${ids[i]} -${ids[j]} 0`);
  }
  for (const [a, b] of edges) {
    let common = masks.get(a) & masks.get(b);
    while (common) {
      const bit = common & -common;
      const c = Math.log2(bit);
      common -= bit;
      lines.push(`-${forward.get(`${a}:${c}`)} -${forward.get(`${b}:${c}`)} 0`);
    }
  }
  return Buffer.from(lines.join('\n') + '\n', 'ascii');
}

function verticesBytes(vertices) { return Buffer.from(vertices.map(v => v.toString(16).padStart(3, '0')).join('\n') + '\n', 'ascii'); }
function edgesBytes(edges) {
  const lines = ['left,right', ...edges.map(([a,b]) => `${a.toString(16).padStart(3,'0')},${b.toString(16).padStart(3,'0')}`)];
  return Buffer.from(lines.join('\n') + '\n', 'ascii');
}

function findOrbit(root, caseId) {
  const parent = caseId.replace(/-t\d+$/, '');
  const child = JSON.parse(fs.readFileSync(path.join(root, 'children', `${parent}.json`), 'utf8'));
  const matches = child.orbits.filter(x => x.grandchild_id === caseId);
  if (matches.length !== 1) throw new Error(`orbit lookup failed ${caseId}`);
  if (child.child_status !== 'UNKNOWN' || matches[0].status !== 'UNKNOWN' || matches[0].raw_12color_cnf_proxy.tier !== 'PILOT') throw new Error(`status/tier failure ${caseId}`);
  return matches[0];
}

function main() {
  const args = parseArgs();
  const sourceRoot = args['classification-root'];
  const instancesRoot = args.instances;
  const summary = JSON.parse(fs.readFileSync(path.join(sourceRoot, 'summary.json'), 'utf8'));
  if (summary.status !== 'PASS' || summary.classification_stream_sha256 !== SOURCE_STREAM) throw new Error('source classification mismatch');
  if (JSON.stringify(summary.pilot_cases) !== JSON.stringify(PILOT_CASES)) throw new Error('pilot list mismatch');
  const aggregate = JSON.parse(fs.readFileSync(path.join(instancesRoot, 'instances.json'), 'utf8'));
  if (aggregate.case_count !== 15 || JSON.stringify(aggregate.case_ids) !== JSON.stringify(PILOT_CASES)) throw new Error('aggregate case set mismatch');

  const caseResults = [];
  let totals = {vertices_across_cases:0, edges_across_cases:0, variables_across_cases:0, clauses_across_cases:0, incompatible_pairs_across_cases:0};
  for (const caseId of PILOT_CASES) {
    const orbit = findOrbit(sourceRoot, caseId);
    const base = orbit.base.map(Number);
    const {vertices, edges, incompatible} = reconstruct(base);
    const vd = sha256(verticesBytes(vertices));
    if (orbit.graph.vertices !== vertices.length || orbit.graph.distance6_edges !== edges.length || orbit.graph.incompatible_pairs !== incompatible || orbit.graph.vertices_sha256 !== vd) throw new Error(`graph mismatch ${caseId}`);
    const clique = deterministicClique(vertices, edges);
    const dom = domains(vertices, clique);
    const {variables, clauses} = formulaCounts(vertices, edges, dom);
    const {reverse} = variableMaps(vertices, dom);
    const dir = path.join(instancesRoot, 'cases', caseId);
    const metadata = JSON.parse(fs.readFileSync(path.join(dir, `${caseId}_metadata.json`), 'utf8'));
    const mapping = JSON.parse(fs.readFileSync(path.join(dir, `${caseId}_variable_map.json`), 'utf8'));
    const expectedMap = {
      schema:'borsuk-q00r00-seventh-base-pilot-color-map-v1', case_id:caseId, colors:COLORS,
      vertices, fixed_clique:clique, allowed_colors:Object.fromEntries(vertices.map(v => [String(v), dom.get(v)])),
      variables, clauses, variable_order:reverse,
    };
    if (JSON.stringify(stableObject(mapping)) !== JSON.stringify(stableObject(expectedMap))) throw new Error(`map structure mismatch ${caseId}`);
    if (!verticesBytes(vertices).equals(fs.readFileSync(path.join(dir, `${caseId}_vertices.txt`)))) throw new Error(`vertices bytes mismatch ${caseId}`);
    if (!edgesBytes(edges).equals(fs.readFileSync(path.join(dir, `${caseId}_distance6_edges.csv`)))) throw new Error(`edges bytes mismatch ${caseId}`);
    const cnf = emitCnf(caseId, vertices, edges, dom);
    if (!cnf.equals(fs.readFileSync(path.join(dir, `${caseId}_12color.cnf`)))) throw new Error(`CNF bytes mismatch ${caseId}`);
    const actualMapHash = sha256File(path.join(dir, `${caseId}_variable_map.json`));
    if (metadata.cnf_sha256 !== sha256(cnf) || metadata.variable_map_sha256 !== actualMapHash) throw new Error(`metadata hash mismatch ${caseId}`);
    if (metadata.vertices !== vertices.length || metadata.edges !== edges.length || metadata.incompatible_pairs !== incompatible || metadata.variables !== variables || metadata.clauses !== clauses) throw new Error(`metadata count mismatch ${caseId}`);
    totals.vertices_across_cases += vertices.length;
    totals.edges_across_cases += edges.length;
    totals.variables_across_cases += variables;
    totals.clauses_across_cases += clauses;
    totals.incompatible_pairs_across_cases += incompatible;
    caseResults.push({case_id:caseId, cnf_sha256:sha256(cnf), variable_map_sha256:actualMapHash, vertices:vertices.length, edges:edges.length, incompatible_pairs:incompatible, variables, clauses});
  }
  for (const [key, value] of Object.entries(totals)) if (aggregate.totals[key] !== value) throw new Error(`aggregate totals mismatch ${key}: ${value} != ${aggregate.totals[key]}`);
  const result = {schema:'borsuk-q00r00-seventh-base-pilot-independent-verification-v1', status:'PASS', case_count:15, cases:caseResults, totals, classification_stream_sha256:SOURCE_STREAM};
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}

try { main(); } catch (error) { console.error(error.stack || String(error)); process.exit(1); }
