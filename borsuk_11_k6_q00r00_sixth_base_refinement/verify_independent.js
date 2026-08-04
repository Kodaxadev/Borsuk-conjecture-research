#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const N = 11;
const K = 6;
const BASE = [0, 63, 455, 1611, 732];
const IDENTITY_MAP = Array.from({length: N}, (_, i) => i);
const IDENTITY_BASE_PERM = [0, 1, 2, 3, 4];
const SCHEMA = 'borsuk-q00r00-sixth-base-classification-v1';
const CLAIM_ID = 'n11-k6-q00r00-sixth-base-classification';

function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function sortedObject(value) {
  if (Array.isArray(value)) return value.map(sortedObject);
  if (value !== null && typeof value === 'object') {
    const output = {};
    for (const key of Object.keys(value).sort()) output[key] = sortedObject(value[key]);
    return output;
  }
  return value;
}

function canonicalJson(value) {
  return Buffer.from(JSON.stringify(sortedObject(value), null, 2) + '\n', 'utf8');
}

function popcount(x) {
  let count = 0;
  while (x) {
    x &= x - 1;
    count += 1;
  }
  return count;
}

function distance(a, b) {
  return popcount(a ^ b);
}

function compatible(v) {
  return !BASE.includes(v) && popcount(v) % 2 === 0 && BASE.every(b => distance(v, b) <= K);
}

function linearApply(v, coordinateMap) {
  let image = 0;
  for (let old = 0; old < N; old += 1) {
    if ((v >>> old) & 1) image |= 1 << coordinateMap[old];
  }
  return image;
}

function applyAuto(v, auto) {
  return linearApply(v, auto.coordinateMap) ^ auto.translation;
}

function autoKey(auto) {
  return `${auto.translation}|${auto.coordinateMap.join(',')}`;
}

function compareArrays(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return a.length - b.length;
}

function compareAutos(a, b) {
  if (a.translation !== b.translation) return a.translation - b.translation;
  return compareArrays(a.coordinateMap, b.coordinateMap);
}

function compose(left, right) {
  const coordinateMap = right.coordinateMap.map(index => left.coordinateMap[index]);
  const translation = left.translation ^ linearApply(right.translation, left.coordinateMap);
  return {translation, coordinateMap};
}

function inverse(auto) {
  const inverseMap = Array(N).fill(0);
  for (let old = 0; old < N; old += 1) inverseMap[auto.coordinateMap[old]] = old;
  return {translation: linearApply(auto.translation, inverseMap), coordinateMap: inverseMap};
}

function subgroupClosure(generators) {
  const identity = {translation: 0, coordinateMap: IDENTITY_MAP.slice()};
  const moves = generators.concat(generators.map(inverse));
  const found = new Map([[autoKey(identity), identity]]);
  const queue = [identity];
  for (let cursor = 0; cursor < queue.length; cursor += 1) {
    const current = queue[cursor];
    for (const move of moves) {
      const image = compose(move, current);
      const key = autoKey(image);
      if (!found.has(key)) {
        found.set(key, image);
        queue.push(image);
      }
    }
  }
  return found;
}

function permutations(values) {
  const output = [];
  const used = Array(values.length).fill(false);
  const current = [];
  function visit() {
    if (current.length === values.length) {
      output.push(current.slice());
      return;
    }
    for (let i = 0; i < values.length; i += 1) {
      if (used[i]) continue;
      used[i] = true;
      current.push(values[i]);
      visit();
      current.pop();
      used[i] = false;
    }
  }
  visit();
  return output;
}

function pattern(points, coordinate) {
  let value = 0;
  for (let i = 0; i < points.length; i += 1) value |= ((points[i] >>> coordinate) & 1) << i;
  return value;
}

function groupCoordinates(points) {
  const groups = new Map();
  for (let coordinate = 0; coordinate < N; coordinate += 1) {
    const key = pattern(points, coordinate);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(coordinate);
  }
  return groups;
}

function sameShape(left, right) {
  const keys = Array.from(new Set([...left.keys(), ...right.keys()])).sort((a, b) => a - b);
  return keys.every(key => (left.get(key) || []).length === (right.get(key) || []).length);
}

function enumerateStabilizer() {
  // Independent reconstruction: enumerate proposed base actions, then solve the
  // coordinate equations by recursive matching of equal four-bit columns.
  const sourceGroups = groupCoordinates(BASE.slice(1));
  const basePermutations = permutations([0, 1, 2, 3, 4]);
  const elements = new Map();

  for (const induced of basePermutations) {
    const translation = BASE[induced[0]];
    const targetPoints = induced.slice(1).map(index => BASE[index] ^ translation);
    const targetGroups = groupCoordinates(targetPoints);
    if (!sameShape(sourceGroups, targetGroups)) continue;

    const patternKeys = Array.from(sourceGroups.keys()).sort((a, b) => a - b);
    const coordinateMap = Array(N).fill(-1);

    function assignPattern(patternIndex) {
      if (patternIndex === patternKeys.length) {
        const auto = {translation, coordinateMap: coordinateMap.slice()};
        const images = BASE.map(point => applyAuto(point, auto));
        const expected = induced.map(index => BASE[index]);
        if (compareArrays(images, expected) !== 0) throw new Error('constructed base action mismatch');
        const key = autoKey(auto);
        const old = elements.get(key);
        if (old && compareArrays(old.induced, induced) !== 0) throw new Error('ambiguous base action');
        elements.set(key, {auto, induced: induced.slice()});
        return;
      }
      const key = patternKeys[patternIndex];
      const source = sourceGroups.get(key);
      const targetOrders = permutations(targetGroups.get(key));
      for (const order of targetOrders) {
        for (let i = 0; i < source.length; i += 1) coordinateMap[source[i]] = order[i];
        assignPattern(patternIndex + 1);
      }
    }
    assignPattern(0);
  }

  const ordered = Array.from(elements.values()).sort((a, b) => compareAutos(a.auto, b.auto));
  return ordered;
}

function combinations(values, size) {
  const output = [];
  const current = [];
  function visit(start) {
    if (current.length === size) {
      output.push(current.slice());
      return;
    }
    for (let i = start; i <= values.length - (size - current.length); i += 1) {
      current.push(values[i]);
      visit(i + 1);
      current.pop();
    }
  }
  visit(0);
  return output;
}

function minimalGenerators(elements) {
  const targetKeys = new Set(elements.map(entry => autoKey(entry.auto)));
  for (let size = 1; size <= elements.length; size += 1) {
    for (const combo of combinations(elements, size)) {
      const closure = subgroupClosure(combo.map(entry => entry.auto));
      if (closure.size === targetKeys.size && [...targetKeys].every(key => closure.has(key))) return combo;
    }
  }
  throw new Error('failed to generate stabilizer');
}

function autoRecord(entry) {
  return {
    coordinate_map_old_to_new: entry.auto.coordinateMap.slice(),
    induced_base_permutation: entry.induced.slice(),
    translation: entry.auto.translation,
    translation_hex: entry.auto.translation.toString(16).padStart(3, '0'),
  };
}

function candidateBytes(candidates) {
  return Buffer.from(candidates.map(v => v.toString(16).padStart(3, '0')).join('\n') + '\n', 'ascii');
}

function manifestBytes(orbits) {
  const header = 'id,representative,representative_hex,orbit_size,stabilizer_size,status\n';
  const rows = orbits.map(orbit => [
    orbit.id,
    orbit.representative,
    orbit.representative_hex,
    orbit.orbit_size,
    orbit.stabilizer_size,
    'UNKNOWN',
  ].join(',') + '\n').join('');
  return Buffer.from(header + rows, 'ascii');
}

function classify() {
  const candidates = [];
  for (let v = 0; v < 1 << N; v += 1) if (compatible(v)) candidates.push(v);
  const candidateSet = new Set(candidates);
  const candidatesOut = candidateBytes(candidates);

  const entries = enumerateStabilizer();
  const elementByKey = new Map(entries.map(entry => [autoKey(entry.auto), entry]));
  const elements = entries.map(entry => entry.auto);
  const elementKeys = new Set(elements.map(autoKey));
  const identityKey = autoKey({translation: 0, coordinateMap: IDENTITY_MAP});
  if (!elementKeys.has(identityKey)) throw new Error('missing identity');

  for (const entry of entries) {
    if (!elementKeys.has(autoKey(inverse(entry.auto)))) throw new Error('not inverse closed');
    const baseImages = new Set(BASE.map(point => applyAuto(point, entry.auto)));
    if (baseImages.size !== BASE.length || !BASE.every(point => baseImages.has(point))) throw new Error('base not preserved');
    if (candidates.some(vertex => !candidateSet.has(applyAuto(vertex, entry.auto)))) throw new Error('candidate action not invariant');
  }
  for (const left of elements) for (const right of elements) {
    if (!elementKeys.has(autoKey(compose(left, right)))) throw new Error('not composition closed');
  }

  const generatorEntries = minimalGenerators(entries);
  const generatorClosure = subgroupClosure(generatorEntries.map(entry => entry.auto));
  if (generatorClosure.size !== elements.length) throw new Error('generator closure mismatch');

  const inducedMap = new Map();
  for (const entry of entries) inducedMap.set(entry.induced.join(','), entry.induced);
  const inducedPermutations = Array.from(inducedMap.values()).sort(compareArrays);
  const pointwiseEntries = entries.filter(entry => compareArrays(entry.induced, IDENTITY_BASE_PERM) === 0);

  const elementRecords = entries.map(autoRecord);
  const elementRecordsBytes = canonicalJson(elementRecords);
  const inducedBytes = canonicalJson(inducedPermutations);
  const stabilizerDocument = {
    action: 'g(x)=P(x) xor t; coordinate_map_old_to_new[i] is the image coordinate of input coordinate i',
    base: BASE.slice(),
    element_count: entries.length,
    elements: elementRecords,
    elements_sha256: sha256(elementRecordsBytes),
    generator_count: generatorEntries.length,
    generators: generatorEntries.map(autoRecord),
    induced_base_permutation_count: inducedPermutations.length,
    induced_base_permutations: inducedPermutations,
    induced_base_permutations_sha256: sha256(inducedBytes),
    order: entries.length,
    pointwise_element_count: pointwiseEntries.length,
    pointwise_elements: pointwiseEntries.map(autoRecord),
    pointwise_order: pointwiseEntries.length,
    schema: 'borsuk-affine-cube-set-stabilizer-v1',
  };
  const stabilizerOut = canonicalJson(stabilizerDocument);

  const unseen = new Set(candidates);
  const orbitRecords = [];
  const coverage = new Map();
  while (unseen.size) {
    const representative = Math.min(...unseen);
    const memberSet = new Set(elements.map(auto => applyAuto(representative, auto)));
    const members = Array.from(memberSet).sort((a, b) => a - b);
    if (members.some(member => !candidateSet.has(member))) throw new Error('orbit contains noncandidate');
    const stabilizerSize = elements.filter(auto => applyAuto(representative, auto) === representative).length;
    if (members.length * stabilizerSize !== elements.length) throw new Error('orbit-stabilizer mismatch');

    const mappings = members.map(member => {
      const mappingEntries = entries.filter(entry => applyAuto(representative, entry.auto) === member).sort((a, b) => compareAutos(a.auto, b.auto));
      if (!mappingEntries.length) throw new Error('missing orbit map');
      const chosen = mappingEntries[0];
      if (applyAuto(representative, chosen.auto) !== member) throw new Error('invalid orbit map');
      return {
        automorphism: autoRecord(chosen),
        member,
        member_hex: member.toString(16).padStart(3, '0'),
      };
    });

    const orbitIndex = orbitRecords.length;
    orbitRecords.push({
      id: `q00r00-s${String(orbitIndex).padStart(3, '0')}`,
      mappings_from_representative: mappings,
      members,
      members_hex: members.map(member => member.toString(16).padStart(3, '0')),
      orbit_size: members.length,
      representative,
      representative_hex: representative.toString(16).padStart(3, '0'),
      stabilizer_size: stabilizerSize,
      status: 'UNKNOWN',
    });
    for (const member of members) {
      coverage.set(member, (coverage.get(member) || 0) + 1);
      unseen.delete(member);
    }
  }

  if (coverage.size !== candidateSet.size || candidates.some(v => coverage.get(v) !== 1)) throw new Error('bad orbit partition');

  const orbitsDocument = {
    base: BASE.slice(),
    candidate_count: candidates.length,
    orbit_count: orbitRecords.length,
    orbits: orbitRecords,
    schema: 'borsuk-q00r00-sixth-base-orbits-v1',
    stabilizer_order: entries.length,
  };
  const orbitsOut = canonicalJson(orbitsDocument);
  const manifestOut = manifestBytes(orbitRecords);

  let pointwiseOrbitCount = 0;
  const pointwiseUnseen = new Set(candidates);
  while (pointwiseUnseen.size) {
    const representative = Math.min(...pointwiseUnseen);
    for (const entry of pointwiseEntries) pointwiseUnseen.delete(applyAuto(representative, entry.auto));
    pointwiseOrbitCount += 1;
  }

  const histogram = {};
  for (const orbit of orbitRecords) histogram[String(orbit.orbit_size)] = (histogram[String(orbit.orbit_size)] || 0) + 1;
  const sortedHistogram = Object.keys(histogram).map(Number).sort((a, b) => a - b).map(orbitSize => ({orbit_size: orbitSize, count: histogram[String(orbitSize)]}));

  const outputHashes = {
    child_manifest_csv_sha256: sha256(manifestOut),
    compatible_candidates_sha256: sha256(candidatesOut),
    orbits_json_sha256: sha256(orbitsOut),
    stabilizer_json_sha256: sha256(stabilizerOut),
  };
  const report = {
    base: BASE.slice(),
    candidate_count: candidates.length,
    candidate_encoding: 'ascending lowercase three-hex-digit vertices, one per LF-terminated line',
    checks: {
      all_listed_candidates_compatible: candidates.every(compatible),
      all_orbit_mappings_valid: true,
      candidate_scan_exhaustive: candidates.length === [...Array(1 << N).keys()].filter(compatible).length,
      generator_closure_equals_stabilizer: generatorClosure.size === entries.length,
      no_incompatible_vertex_listed: candidates.every(compatible),
      orbit_stabilizer_identity: orbitRecords.every(orbit => orbit.orbit_size * orbit.stabilizer_size === entries.length),
      orbits_disjoint: candidates.every(v => coverage.get(v) === 1),
      orbits_union_candidate_set: coverage.size === candidateSet.size,
      unordered_and_pointwise_actions_distinct: entries.length !== pointwiseEntries.length,
    },
    claim_id: CLAIM_ID,
    compatibility_predicate: 'v not in B; wt(v) is even; and d_H(v,b) <= 6 for every b in B',
    induced_base_permutation_count: inducedPermutations.length,
    k: K,
    n: N,
    orbit_count: orbitRecords.length,
    orbit_size_histogram: sortedHistogram,
    output_hashes: outputHashes,
    pointwise_orbit_count_negative_control: pointwiseOrbitCount,
    pointwise_stabilizer_order: pointwiseEntries.length,
    schema: SCHEMA,
    stabilizer_generator_count: generatorEntries.length,
    stabilizer_order: entries.length,
    status: 'PASS',
  };
  const reportOut = canonicalJson(report);

  return {
    'child_manifest.csv': manifestOut,
    'classification.json': reportOut,
    'compatible_candidates.txt': candidatesOut,
    'orbits.json': orbitsOut,
    'stabilizer.json': stabilizerOut,
  };
}

function main() {
  const outputIndex = process.argv.indexOf('--output-dir');
  if (outputIndex < 0 || !process.argv[outputIndex + 1]) throw new Error('usage: verify_independent.js --output-dir DIR');
  const outputDir = process.argv[outputIndex + 1];
  fs.mkdirSync(outputDir, {recursive: true});
  const outputs = classify();
  for (const [name, content] of Object.entries(outputs)) fs.writeFileSync(path.join(outputDir, name), content);
  const sums = Object.keys(outputs).sort().map(name => `${sha256(outputs[name])}  ${name}\n`).join('');
  fs.writeFileSync(path.join(outputDir, 'SHA256SUMS'), sums, 'ascii');
  const report = JSON.parse(outputs['classification.json'].toString('utf8'));
  console.log(`PASS candidates=${report.candidate_count} stabilizer=${report.stabilizer_order} pointwise=${report.pointwise_stabilizer_order} orbits=${report.orbit_count} pointwise_orbits=${report.pointwise_orbit_count_negative_control}`);
}

main();
