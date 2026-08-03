#!/usr/bin/env node
"use strict";

/*
Verifier 2: independently enumerate every unordered pair of canonical
vertices and test popcount(a XOR b) === 8. It does not use the Python
verifier's XOR-mask edge-generation method.
*/
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ROOT = __dirname;
const witness = JSON.parse(fs.readFileSync(path.join(ROOT, "witness.json"), "utf8"));
const colors = new Map(Object.entries(witness.colors).map(([v, c]) => [Number(v), c]));

function popcount(x) {
  let n = x >>> 0;
  let c = 0;
  while (n !== 0) {
    n &= n - 1;
    c++;
  }
  return c;
}

const vertices = [];
for (let x = 0; x < (1 << 11); x++) {
  const w = popcount(x);
  if ((w % 2) === 0 && w <= 8) vertices.push(x);
}
if (vertices.length !== 1013) throw new Error(`vertex count ${vertices.length}`);
if (colors.size !== vertices.length) throw new Error("witness size mismatch");
for (const v of vertices) {
  if (!colors.has(v)) throw new Error(`missing vertex ${v}`);
  const c = colors.get(v);
  if (!Number.isInteger(c) || c < 0 || c >= 12) throw new Error(`bad color at ${v}`);
}

const edges = [];
let monochromatic = 0;
for (let i = 0; i < vertices.length; i++) {
  const a = vertices[i];
  for (let j = i + 1; j < vertices.length; j++) {
    const b = vertices[j];
    if (popcount(a ^ b) === 8) {
      edges.push([a, b]);
      if (colors.get(a) === colors.get(b)) monochromatic++;
    }
  }
}
if (edges.length !== 82665) throw new Error(`edge count ${edges.length}`);
if (monochromatic !== 0) throw new Error(`${monochromatic} monochromatic edges`);

const edgeText = edges.map(([a, b]) => `${a},${b}\n`).join("");
const digest = crypto.createHash("sha256").update(edgeText, "utf8").digest("hex");
if (digest !== witness.expected.graph_sha256) {
  throw new Error(`graph hash mismatch ${digest}`);
}

// Separate color-class pair scan.
const classes = new Map();
for (const [v, c] of colors.entries()) {
  if (!classes.has(c)) classes.set(c, []);
  classes.get(c).push(v);
}
for (const [c, cls] of classes.entries()) {
  for (let i = 0; i < cls.length; i++) {
    for (let j = i + 1; j < cls.length; j++) {
      if (popcount(cls[i] ^ cls[j]) === 8) {
        throw new Error(`class ${c} contains distance-8 pair ${cls[i]},${cls[j]}`);
      }
    }
  }
}

console.log(JSON.stringify({
  status: "PASS",
  dimension: 11,
  diameter: 8,
  vertices: vertices.length,
  edges: edges.length,
  colors_used: new Set(colors.values()).size,
  monochromatic_edges: monochromatic,
  graph_sha256: digest,
  method: "all unordered vertex pairs plus color-class pair scan"
}, null, 2));
