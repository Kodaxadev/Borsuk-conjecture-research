#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const N = 11;
const K = 6;
const COLORS = 12;

function fail(message) { throw new Error(message); }
function sha256File(file) { return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function bitCount(value) { let count = 0; while (value) { value &= value - 1; count++; } return count; }
function distance(a, b) { return bitCount(a ^ b); }
function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) out[args[i].replace(/^--/, '')] = args[i + 1];
  if (!out['trim-root'] || !out.instances) fail('usage: verify_instances.js --trim-root DIR --instances DIR');
  return out;
}
function parseVertices(file) {
  const text = fs.readFileSync(file, 'ascii');
  if (text && !text.endsWith('\n')) fail(`missing final newline: ${file}`);
  const lines = text.split('\n').filter(Boolean);
  const vertices = lines.map(line => parseInt(line, 16));
  lines.forEach((line, i) => { if (vertices[i].toString(16).padStart(3, '0') !== line) fail(`noncanonical vertex: ${file}`); });
  const sorted = [...new Set(vertices)].sort((a, b) => a - b);
  if (JSON.stringify(vertices) !== JSON.stringify(sorted)) fail(`noncanonical vertex order: ${file}`);
  return vertices;
}
function parseEdges(file) {
  const lines = fs.readFileSync(file, 'ascii').trimEnd().split('\n');
  if (lines.shift() !== 'left,right') fail(`bad edge header: ${file}`);
  const edges = lines.filter(Boolean).map(line => {
    const parts = line.split(',');
    if (parts.length !== 2) fail(`bad edge row: ${file}`);
    const left = parseInt(parts[0], 16), right = parseInt(parts[1], 16);
    if (left >= right || left.toString(16).padStart(3, '0') !== parts[0] || right.toString(16).padStart(3, '0') !== parts[1]) fail(`noncanonical edge row: ${file}`);
    return [left, right];
  });
  for (let i = 1; i < edges.length; i++) {
    if (edges[i - 1][0] > edges[i][0] || (edges[i - 1][0] === edges[i][0] && edges[i - 1][1] >= edges[i][1])) fail(`edge order failure: ${file}`);
  }
  return edges;
}
function deterministicClique(vertices, edges) {
  const degree = new Map(vertices.map(v => [v, 0]));
  edges.forEach(([a, b]) => { degree.set(a, degree.get(a) + 1); degree.set(b, degree.get(b) + 1); });
  const ordered = [...vertices].sort((a, b) => degree.get(b) - degree.get(a) || a - b);
  const clique = [];
  for (const vertex of ordered) {
    if (clique.every(other => distance(vertex, other) === K)) clique.push(vertex);
    if (clique.length === COLORS) break;
  }
  if (!clique.length) fail('empty deterministic clique');
  return clique;
}
function domainsFor(vertices, clique) {
  const fixed = new Map(clique.map((vertex, color) => [vertex, color]));
  const domains = new Map();
  for (const vertex of vertices) {
    let domain;
    if (fixed.has(vertex)) domain = [fixed.get(vertex)];
    else {
      domain = [];
      for (let color = 0; color < COLORS; color++) {
        if (color >= clique.length || distance(vertex, clique[color]) !== K) domain.push(color);
      }
    }
    if (!domain.length) fail(`empty domain: ${vertex}`);
    domains.set(vertex, domain);
  }
  return domains;
}
function variableMaps(vertices, domains) {
  const forward = new Map();
  const reverse = [];
  let variable = 1;
  for (const vertex of vertices) {
    for (const color of domains.get(vertex)) {
      forward.set(`${vertex}:${color}`, variable);
      reverse.push({ variable, vertex, color });
      variable++;
    }
  }
  return { forward, reverse };
}
function domainMask(domain) { return domain.reduce((mask, color) => mask | (1 << color), 0); }
function expectedCnfHash(caseId, vertices, edges, clique, domains) {
  const { forward, reverse } = variableMaps(vertices, domains);
  let clauses = 0;
  for (const vertex of vertices) {
    const size = domains.get(vertex).length;
    clauses += 1 + (size * (size - 1)) / 2;
  }
  const masks = new Map(vertices.map(v => [v, domainMask(domains.get(v))]));
  for (const [left, right] of edges) clauses += bitCount(masks.get(left) & masks.get(right));
  const hash = crypto.createHash('sha256');
  const add = line => hash.update(line, 'ascii');
  add(`c ${caseId} canonical compact 12-color CNF\n`);
  add('c Variables are ordered by ascending vertex then ascending allowed color.\n');
  add('c Greedy clique order is descending degree then ascending vertex.\n');
  add(`p cnf ${reverse.length} ${clauses}\n`);
  for (const vertex of vertices) {
    const ids = domains.get(vertex).map(color => forward.get(`${vertex}:${color}`));
    add(`${ids.join(' ')} 0\n`);
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) add(`-${ids[i]} -${ids[j]} 0\n`);
  }
  for (const [left, right] of edges) {
    let common = masks.get(left) & masks.get(right);
    while (common) {
      const bit = common & -common;
      const color = Math.log2(bit);
      common -= bit;
      add(`-${forward.get(`${left}:${color}`)} -${forward.get(`${right}:${color}`)} 0\n`);
    }
  }
  return { hash: hash.digest('hex'), variables: reverse.length, clauses, reverse };
}

function main() {
  const args = parseArgs();
  const trimRoot = path.resolve(args['trim-root']);
  const instancesRoot = path.resolve(args.instances);
  const manifest = JSON.parse(fs.readFileSync(path.join(trimRoot, 'manifest.json'), 'utf8'));
  const aggregate = JSON.parse(fs.readFileSync(path.join(instancesRoot, 'instances.json'), 'utf8'));
  if (manifest.children.length !== 36 || aggregate.cases.length !== 36) fail('case count mismatch');
  let totalVariables = 0, totalClauses = 0;
  for (let index = 0; index < 36; index++) {
    const caseId = `q00r00-s${String(index).padStart(3, '0')}`;
    const source = path.join(trimRoot, 'children', caseId);
    const generated = path.join(instancesRoot, 'cases', caseId);
    const vertices = parseVertices(path.join(source, 'vertices.txt'));
    const edges = parseEdges(path.join(source, 'distance6_edges.csv'));
    const vertexSet = new Set(vertices);
    for (const [left, right] of edges) if (!vertexSet.has(left) || !vertexSet.has(right) || distance(left, right) !== K) fail(`invalid source edge: ${caseId}`);
    const clique = deterministicClique(vertices, edges);
    const domains = domainsFor(vertices, clique);
    const cnf = expectedCnfHash(caseId, vertices, edges, clique, domains);
    const metadata = JSON.parse(fs.readFileSync(path.join(generated, `${caseId}_metadata.json`), 'utf8'));
    const mapping = JSON.parse(fs.readFileSync(path.join(generated, `${caseId}_variable_map.json`), 'utf8'));
    if (metadata.cnf_sha256 !== cnf.hash || sha256File(path.join(generated, `${caseId}_12color.cnf`)) !== cnf.hash) fail(`CNF mismatch: ${caseId}`);
    if (metadata.variables !== cnf.variables || metadata.clauses !== cnf.clauses) fail(`CNF count mismatch: ${caseId}`);
    if (JSON.stringify(metadata.fixed_clique) !== JSON.stringify(clique) || JSON.stringify(mapping.fixed_clique) !== JSON.stringify(clique)) fail(`clique mismatch: ${caseId}`);
    if (mapping.variables !== cnf.variables || mapping.clauses !== cnf.clauses) fail(`map count mismatch: ${caseId}`);
    for (const vertex of vertices) {
      if (JSON.stringify(mapping.allowed_colors[String(vertex)]) !== JSON.stringify(domains.get(vertex))) fail(`domain mismatch: ${caseId}/${vertex}`);
    }
    if (mapping.variable_order.length !== cnf.reverse.length) fail(`variable order length mismatch: ${caseId}`);
    for (let i = 0; i < cnf.reverse.length; i++) {
      const actual = mapping.variable_order[i], expected = cnf.reverse[i];
      if (actual.variable !== expected.variable || actual.vertex !== expected.vertex || actual.color !== expected.color) fail(`variable order mismatch: ${caseId}/${i}`);
    }
    if (metadata.variable_map_sha256 !== sha256File(path.join(generated, `${caseId}_variable_map.json`))) fail(`map hash mismatch: ${caseId}`);
    totalVariables += cnf.variables;
    totalClauses += cnf.clauses;
  }
  if (aggregate.totals.variables_across_cases !== totalVariables || aggregate.totals.clauses_across_cases !== totalClauses) fail('aggregate count mismatch');
  console.log(JSON.stringify({ status: 'PASS', case_count: 36, total_variables: totalVariables, total_clauses: totalClauses }, null, 2));
}

try { main(); } catch (error) { console.error(error.stack || error.message); process.exit(1); }
