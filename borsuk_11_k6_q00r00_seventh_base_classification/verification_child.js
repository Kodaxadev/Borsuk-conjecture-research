#!/usr/bin/env node
'use strict';

const {
  fs, path, crypto, N, K, COLORS, CLAUSES_PER_VERTEX_RAW, CLAUSES_PER_EDGE_RAW,
  CLAIM_ID, sha256File, distance, allowed, applyTransform, setwiseStabilizer,
  inducedBasePermutation, partition, graphStats, complexityTier, readVertices,
} = require('./verification_core');

function classifyChild(child, trimRoot) {
  const childId = child.child_id;
  const base = child.base.map(Number);
  const verticesPath = path.join(trimRoot, child.files.vertices.path);
  if (sha256File(verticesPath) !== child.files.vertices.sha256) throw new Error(`vertex hash mismatch ${childId}`);
  const vertices = readVertices(verticesPath);
  const reconstructed = [...Array(1 << N).keys()].filter(vertex => allowed(vertex, base));
  if (JSON.stringify(vertices) !== JSON.stringify(reconstructed)) throw new Error(`trim mismatch ${childId}`);
  const transforms = setwiseStabilizer(base);
  const encoded = transforms.map((transform, id) => ({
    id,
    translation: transform.t,
    translation_hex: transform.t.toString(16).padStart(3, '0'),
    output_to_input: transform.q,
    induced_base_permutation: inducedBasePermutation(base, transform),
  }));
  const identityBase = [...base.keys()];
  const pointwiseIds = encoded.filter(record => JSON.stringify(record.induced_base_permutation) === JSON.stringify(identityBase)).map(record => record.id);
  const pointwise = pointwiseIds.map(id => transforms[id]);
  const baseSet = new Set(base);
  const candidates = vertices.filter(vertex => !baseSet.has(vertex));
  const setwiseOrbits = partition(candidates, transforms);
  const pointwiseOrbits = partition(candidates, pointwise);
  const orbits = setwiseOrbits.map((members, orbitIndex) => {
    const representative = members[0];
    const mappings = members.map(member => {
      const ids = transforms.map((transform, id) => applyTransform(representative, transform) === member ? id : null).filter(id => id !== null);
      if (!ids.length) throw new Error('missing mapping');
      return { member, transform_id: Math.min(...ids) };
    });
    const repStabilizer = transforms.filter(transform => applyTransform(representative, transform) === representative).length;
    if (members.length * repStabilizer !== transforms.length) throw new Error('orbit stabilizer mismatch');
    const sevenBase = [...base, representative];
    const grandchildVertices = vertices.filter(vertex => distance(vertex, representative) <= K);
    const reconstructedGrandchild = [...Array(1 << N).keys()].filter(vertex => allowed(vertex, sevenBase));
    if (JSON.stringify(grandchildVertices) !== JSON.stringify(reconstructedGrandchild)) throw new Error('grandchild mismatch');
    const graph = graphStats(grandchildVertices);
    const rawVariables = COLORS * graph.vertices;
    const rawClauses = CLAUSES_PER_VERTEX_RAW * graph.vertices + CLAUSES_PER_EDGE_RAW * graph.distance6_edges;
    return {
      grandchild_id: `${childId}-t${String(orbitIndex).padStart(3, '0')}`,
      status: 'UNKNOWN',
      representative,
      representative_hex: representative.toString(16).padStart(3, '0'),
      members,
      orbit_size: members.length,
      representative_stabilizer_order: repStabilizer,
      member_mappings: mappings,
      base: sevenBase,
      graph,
      raw_12color_cnf_proxy: {
        variables: rawVariables,
        clauses: rawClauses,
        tier: complexityTier(rawClauses),
        interpretation: 'scheduling proxy only; no SAT or UNSAT inference',
      },
    };
  });
  const candidateHash = crypto.createHash('sha256');
  for (const vertex of candidates) candidateHash.update(vertex.toString(16).padStart(3, '0') + '\n', 'ascii');
  return {
    schema: 'borsuk-q00r00-seventh-base-child-classification-v1',
    claim_id: CLAIM_ID,
    child_id: childId,
    child_status: 'UNKNOWN',
    refinement_reason: 'incomplete_sixth_base_screen_not_certified_obstruction',
    base,
    source_trim: {
      vertices: vertices.length,
      vertices_sha256: child.files.vertices.sha256,
      distance6_edges: child.counts.distance6_edges,
      incompatible_pairs: child.counts.incompatible_pairs,
    },
    candidate_count: candidates.length,
    candidates,
    candidates_sha256: candidateHash.digest('hex'),
    setwise_stabilizer_order: transforms.length,
    pointwise_stabilizer_order: pointwise.length,
    setwise_stabilizer: encoded,
    setwise_orbit_count: orbits.length,
    pointwise_orbit_count_negative_control: pointwiseOrbits.length,
    orbits,
  };
}


module.exports = { classifyChild };
