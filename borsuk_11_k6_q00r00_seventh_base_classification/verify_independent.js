#!/usr/bin/env node
'use strict';

const { fs, path, crypto, SOURCE_MANIFEST_SHA256, parseArgs, sha256File, stableStringify } = require('./verification_core');
const { classifyChild } = require('./verification_child');

function main() {
  const args = parseArgs();
  const trimRoot = args['trim-root'];
  const generated = args.generated;
  const manifestPath = path.join(trimRoot, 'manifest.json');
  if (sha256File(manifestPath) !== SOURCE_MANIFEST_SHA256) throw new Error('manifest hash mismatch');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const expectedIds = [...Array(36).keys()].map(i => `q00r00-s${String(i).padStart(3, '0')}`);
  if (JSON.stringify(manifest.children.map(child => child.child_id)) !== JSON.stringify(expectedIds)) throw new Error('child coverage mismatch');
  const digest = crypto.createHash('sha256');
  let grandchildCount = 0;
  let candidateCount = 0;
  let pointwiseOrbitCount = 0;
  const childSummaries = [];
  for (const child of manifest.children) {
    const classification = classifyChild(child, trimRoot);
    digest.update(stableStringify(classification) + '\n', 'utf8');
    grandchildCount += classification.setwise_orbit_count;
    candidateCount += classification.candidate_count;
    pointwiseOrbitCount += classification.pointwise_orbit_count_negative_control;
    childSummaries.push({
      child_id: classification.child_id,
      stabilizer_order: classification.setwise_stabilizer_order,
      candidate_count: classification.candidate_count,
      orbit_count: classification.setwise_orbit_count,
      pointwise_orbit_count: classification.pointwise_orbit_count_negative_control,
    });
  }
  const observed = {
    schema: 'borsuk-q00r00-seventh-base-independent-verification-v1',
    status: 'PASS',
    implementation: 'JavaScript independent reconstruction',
    child_count: 36,
    grandchild_count: grandchildCount,
    candidate_count_total: candidateCount,
    pointwise_orbit_count_negative_control_total: pointwiseOrbitCount,
    classification_stream_sha256: digest.digest('hex'),
    child_summaries: childSummaries,
  };
  const primary = JSON.parse(fs.readFileSync(path.join(generated, 'summary.json'), 'utf8'));
  for (const key of ['grandchild_count', 'candidate_count_total', 'pointwise_orbit_count_negative_control_total', 'classification_stream_sha256']) {
    if (observed[key] !== primary[key]) throw new Error(`${key} mismatch: ${observed[key]} != ${primary[key]}`);
  }
  fs.writeFileSync(args.output, JSON.stringify(observed, null, 2) + '\n');
  process.stdout.write(JSON.stringify(observed, null, 2) + '\n');
}

main();
