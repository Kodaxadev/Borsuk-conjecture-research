#!/usr/bin/env node
'use strict';

const crypto = require('crypto');

const N = 11;
const A = (1 << 6) - 1;
const EXPECTED = {
  vertexCount: 692,
  g6EdgeCount: 104606,
  incompatibilityEdgeCount: 37470,
  vertexSha256: 'ece78553536e8cbac3404fb77db0096352024b1dbf15ea4f129d782a1755590d',
  g6EdgeSha256: '28aeb05060799feae42e3af33d51a66f852f0e6308cb737f0326bcda0af17c3f',
  incompatibilityEdgeSha256: 'cc2059f512d2210f1c654c0ae7cbc1f00db22e29cc7fa6d1279e6b77a2f68828',
};

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

function hex(mask) {
  return mask.toString(16).padStart(3, '0');
}

function digest(text) {
  return crypto.createHash('sha256').update(text, 'ascii').digest('hex');
}

const vertices = [];
for (let mask = 0; mask < (1 << N); mask += 1) {
  const w = popcount(mask);
  if (w % 2 === 0 && w <= 6 && distance(mask, A) <= 6) {
    vertices.push(mask);
  }
}

let vertexText = '';
for (const mask of vertices) vertexText += `${hex(mask)}\n`;

let g6Text = '';
let incompatibilityText = '';
let g6EdgeCount = 0;
let incompatibilityEdgeCount = 0;
for (let i = 0; i < vertices.length; i += 1) {
  for (let j = i + 1; j < vertices.length; j += 1) {
    const left = vertices[i];
    const right = vertices[j];
    const d = distance(left, right);
    if (d === 6) {
      g6EdgeCount += 1;
      g6Text += `${hex(left)},${hex(right)}\n`;
    } else if (d > 6) {
      incompatibilityEdgeCount += 1;
      incompatibilityText += `${hex(left)},${hex(right)}\n`;
    }
  }
}

const actual = {
  vertexCount: vertices.length,
  g6EdgeCount,
  incompatibilityEdgeCount,
  vertexSha256: digest(vertexText),
  g6EdgeSha256: digest(g6Text),
  incompatibilityEdgeSha256: digest(incompatibilityText),
};

for (const [field, expected] of Object.entries(EXPECTED)) {
  if (actual[field] !== expected) {
    throw new Error(`${field}: expected ${expected}, got ${actual[field]}`);
  }
}

console.log(JSON.stringify(actual, null, 2));
