#!/usr/bin/env node
'use strict';

// Independent JavaScript verifier for the three explicit coloring witnesses.
// It shares no graph-construction code with verify.py.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const N = 11;
const K = 4;
const witness = JSON.parse(fs.readFileSync(path.join(__dirname, 'witness.json'), 'utf8'));

function popcount(x) {
  let c = 0;
  while (x !== 0) { x &= x - 1; c++; }
  return c;
}
function distance(a, b) { return popcount(a ^ b); }
function encode(items) { return items.reduce((x, i) => x | (1 << i), 0); }
function bitstring(x) { return x.toString(2).padStart(N, '0'); }

function combinations(arr, k) {
  const out = [];
  function rec(start, chosen) {
    if (chosen.length === k) { out.push(chosen.slice()); return; }
    for (let i = start; i <= arr.length - (k - chosen.length); i++) {
      chosen.push(arr[i]); rec(i + 1, chosen); chosen.pop();
    }
  }
  rec(0, []);
  return out;
}

function evenBall2() {
  const out = [];
  for (let x = 0; x < (1 << N); x++) {
    const w = popcount(x);
    if (w === 0 || w === 2) out.push(x);
  }
  return out;
}
function triangleCover() {
  const centers = [0, encode([0,1,2,3]), encode([0,1,4,5])];
  const out = [];
  for (let x = 0; x < (1 << N); x++) {
    if ((popcount(x) & 1) !== 0) continue;
    if (centers.every(c => distance(x,c) <= K)) out.push(x);
  }
  return out;
}
function starCover() {
  const s = new Set(evenBall2());
  for (let j = 3; j < N; j++) s.add(encode([0,1,2,j]));
  return [...s].sort((a,b) => a-b);
}
function topCover() {
  const s = new Set(evenBall2());
  for (const c of combinations([0,1,2,3,4], 4)) s.add(encode(c));
  return [...s].sort((a,b) => a-b);
}

function verify(name, vertices) {
  const raw = witness.colorings[name];
  const colors = new Map(Object.entries(raw).map(([v,c]) => [parseInt(v,2), Number(c)]));
  if (colors.size !== vertices.length) throw new Error(`${name}: vertex count mismatch`);
  for (const v of vertices) if (!colors.has(v)) throw new Error(`${name}: missing ${bitstring(v)}`);
  let edgeCount = 0;
  const hash = crypto.createHash('sha256');
  for (let i = 0; i < vertices.length; i++) {
    for (let j = i + 1; j < vertices.length; j++) {
      const u = vertices[i], v = vertices[j];
      if (distance(u,v) === K) {
        edgeCount++;
        hash.update(`${bitstring(u)} ${bitstring(v)}\n`, 'ascii');
        if (colors.get(u) === colors.get(v)) {
          throw new Error(`${name}: monochromatic edge ${bitstring(u)}--${bitstring(v)}`);
        }
      }
    }
  }
  const distinct = new Set(colors.values()).size;
  if (distinct > 12) throw new Error(`${name}: uses ${distinct} colors`);
  return {vertices: vertices.length, edges: edgeCount, colors: distinct, edge_list_sha256: hash.digest('hex')};
}

const result = {
  triangle_trim_even: verify('triangle_trim_even', triangleCover()),
  star_plus_even_ball: verify('star_plus_even_ball', starCover()),
  top_plus_even_ball: verify('top_plus_even_ball', topCover()),
};
console.log(JSON.stringify(result, null, 2));
