#!/usr/bin/env node
"use strict";

const crypto = require("crypto");

const N = 11;
const K = 6;
const A = (1 << 6) - 1;
const Q00_BASE = [0, A, 455, 1611];
const EXPECTED_PARENT = { vertices: 436, edges: 39600, incompatible: 13104 };
const EXPECTED_FIFTH_CANDIDATES = 432;
const EXPECTED_TYPES = 12;
const EXPECTED_CASE_CSV_SHA256 = "d5b0825cd8645af2c595b3de3c851360e0b283d8ce61383482f76168e1ae9855";
const EXPECTED_ASSIGNMENT_SHA256 = "6c94923a260290d59727bdcad68293b7f1962a7c5377885dd536fefa5962ffc7";

function popcount(value) {
  let count = 0;
  while (value) {
    value &= value - 1;
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

function trimVertices(bases) {
  const vertices = [];
  for (let mask = 0; mask < 1 << N; mask += 1) {
    if (allowed(mask, bases)) vertices.push(mask);
  }
  return vertices;
}

function trimStats(bases) {
  const vertices = trimVertices(bases);
  let edges = 0;
  let incompatible = 0;
  for (let index = 0; index < vertices.length; index += 1) {
    for (let rightIndex = index + 1; rightIndex < vertices.length; rightIndex += 1) {
      const d = distance(vertices[index], vertices[rightIndex]);
      if (d === K) edges += 1;
      else if (d > K) incompatible += 1;
    }
  }
  return { vertices: vertices.length, edges, incompatible };
}

function permutations(values) {
  if (values.length === 0) return [[]];
  const output = [];
  for (let index = 0; index < values.length; index += 1) {
    const rest = values.slice(0, index).concat(values.slice(index + 1));
    for (const suffix of permutations(rest)) output.push([values[index], ...suffix]);
  }
  return output;
}

function compareArrays(left, right) {
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return 0;
}

function canonicalSignature(points) {
  let best = null;
  for (let originIndex = 0; originIndex < points.length; originIndex += 1) {
    const origin = points[originIndex];
    const translated = points.filter((_, index) => index !== originIndex).map((point) => point ^ origin);
    for (const permutation of permutations(translated)) {
      const counts = Array(1 << (points.length - 1)).fill(0);
      for (let coordinate = 0; coordinate < N; coordinate += 1) {
        let signature = 0;
        for (let index = 0; index < permutation.length; index += 1) {
          signature |= ((permutation[index] >> coordinate) & 1) << index;
        }
        counts[signature] += 1;
      }
      if (best === null || compareArrays(counts, best) < 0) best = counts;
    }
  }
  return best;
}

function sha256(text) {
  return crypto.createHash("sha256").update(text, "ascii").digest("hex");
}

const parentVertices = trimVertices(Q00_BASE);
const parentStats = trimStats(Q00_BASE);
if (JSON.stringify(parentStats) !== JSON.stringify(EXPECTED_PARENT)) {
  throw new Error(`q00 parent statistics mismatch: ${JSON.stringify(parentStats)}`);
}

const candidates = parentVertices.filter((vertex) => !Q00_BASE.includes(vertex));
if (candidates.length !== EXPECTED_FIFTH_CANDIDATES) {
  throw new Error(`expected ${EXPECTED_FIFTH_CANDIDATES} fifth vertices, got ${candidates.length}`);
}

const grouped = new Map();
for (const fifth of candidates) {
  const signature = canonicalSignature([...Q00_BASE, fifth]);
  const key = signature.join(",");
  if (!grouped.has(key)) grouped.set(key, { signature, members: [] });
  grouped.get(key).members.push(fifth);
}
if (grouped.size !== EXPECTED_TYPES) throw new Error(`expected ${EXPECTED_TYPES} types, got ${grouped.size}`);

const entries = [...grouped.values()].sort((left, right) => compareArrays(left.signature, right.signature));
const rows = [];
let assignmentText = "";
for (let index = 0; index < entries.length; index += 1) {
  const { signature, members } = entries[index];
  members.sort((left, right) => left - right);
  const caseId = `q00r${String(index).padStart(2, "0")}`;
  const representative = members[0];
  const stats = trimStats([...Q00_BASE, representative]);
  rows.push({
    id: caseId,
    D: representative,
    D_hex: representative.toString(16).padStart(3, "0"),
    member_count: members.length,
    vertices: stats.vertices,
    exact_distance_edges: stats.edges,
    incompatible_pairs: stats.incompatible,
    base_signature: signature.join("-"),
  });
  for (const member of members) assignmentText += `${member.toString(16).padStart(3, "0")},${caseId}\n`;
}

if (rows.reduce((total, row) => total + row.member_count, 0) !== EXPECTED_FIFTH_CANDIDATES) {
  throw new Error("five-base memberships do not cover all fifth vertices");
}

const fields = ["id", "D", "D_hex", "member_count", "vertices", "exact_distance_edges", "incompatible_pairs", "base_signature"];
let csv = `${fields.join(",")}\n`;
for (const row of rows) csv += `${fields.map((field) => row[field]).join(",")}\n`;

const csvHash = sha256(csv);
const assignmentHash = sha256(assignmentText);
if (csvHash !== EXPECTED_CASE_CSV_SHA256) throw new Error(`case-list hash mismatch: ${csvHash}`);
if (assignmentHash !== EXPECTED_ASSIGNMENT_SHA256) throw new Error(`assignment hash mismatch: ${assignmentHash}`);

const sizes = rows.map((row) => row.vertices);
console.log(JSON.stringify({
  status: "PASS",
  parent_vertices: parentStats.vertices,
  parent_edges: parentStats.edges,
  parent_incompatible_pairs: parentStats.incompatible,
  fifth_candidates: candidates.length,
  canonical_types: rows.length,
  trim_range: [Math.min(...sizes), Math.max(...sizes)],
  case_csv_sha256: csvHash,
  assignment_sha256: assignmentHash,
}, null, 2));
