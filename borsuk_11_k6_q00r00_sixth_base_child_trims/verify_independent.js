#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const N = 11;
const K = 6;
const FIXED_BASE = [0, 63, 455, 1611, 732];
const PACKAGE_CLAIM = "n11-k6-q00r00-sixth-base-child-trims";
const SCHEMA = "borsuk-q00r00-sixth-base-child-trims-v1";
const PREDICATE = "wt(v) even and d_H(v,b) <= 6 for every b in the six-point base";
const EXPECTED_CHILD_MANIFEST_SHA256 = "180e8398807c95478ac7cb62262758314a9c49270a487de0370f384dff39efb5";
const EXPECTED_PARENT_ARCHIVE_SHA256 = "0f45e952cda60a47f01fb0a415de07438cc9bc32f3d4811c8d17ce1cb2982a7d";
const EXPECTED_PARENT_SOURCE_COMMIT = "1cee54611bf414f7961cbdd43f5fc2b867b3230d";
const EXPECTED_PARENT_RUN_ID = 30842512224;
const EXPECTED_PARENT_JOB_ID = 91782782478;
const EXPECTED_PARENT_ARTIFACT_ID = 8867349456;

function fail(message) {
  throw new Error(message);
}

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function sha256File(filePath) {
  return sha256(fs.readFileSync(filePath));
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value !== null && typeof value === "object") {
    const output = {};
    for (const key of Object.keys(value).sort()) output[key] = canonicalize(value[key]);
    return output;
  }
  return value;
}

function canonicalJsonBytes(value) {
  return Buffer.from(JSON.stringify(canonicalize(value), null, 2) + "\n", "utf8");
}

function bitCount(value) {
  let count = 0;
  while (value) {
    value &= value - 1;
    count += 1;
  }
  return count;
}

function distance(left, right) {
  return bitCount(left ^ right);
}

function trimAllowed(vertex, base) {
  return bitCount(vertex) % 2 === 0 && base.every((point) => distance(vertex, point) <= K);
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function removeTree(target) {
  fs.rmSync(target, { recursive: true, force: true });
}

function posixRelative(root, filePath) {
  return path.relative(root, filePath).split(path.sep).join("/");
}

function fileRecord(root, filePath) {
  return {
    path: posixRelative(root, filePath),
    sha256: sha256File(filePath),
    size_bytes: fs.statSync(filePath).size,
  };
}

function readFrozenChildren(filePath) {
  const raw = fs.readFileSync(filePath);
  const actual = sha256(raw);
  if (actual !== EXPECTED_CHILD_MANIFEST_SHA256) fail(`classification child manifest hash mismatch: ${actual}`);
  const lines = raw.toString("ascii").split("\n");
  if (lines.at(-1) === "") lines.pop();
  const expectedHeader = "id,representative,representative_hex,orbit_size,stabilizer_size,status";
  if (lines.shift() !== expectedHeader) fail("unexpected child manifest columns");
  const children = lines.map((line, index) => {
    const fields = line.split(",");
    if (fields.length !== 6) fail(`malformed child row ${index}`);
    const child = {
      child_id: fields[0],
      representative: Number(fields[1]),
      representative_hex: fields[2],
      orbit_size: Number(fields[3]),
      stabilizer_size: Number(fields[4]),
      status: fields[5],
    };
    const expectedId = `q00r00-s${String(index).padStart(3, "0")}`;
    if (child.child_id !== expectedId) fail(`child ID sequence mismatch at ${index}`);
    if (child.representative_hex !== child.representative.toString(16).padStart(3, "0")) fail(`representative encoding mismatch for ${child.child_id}`);
    if (child.status !== "UNKNOWN") fail(`classification status changed for ${child.child_id}`);
    return child;
  });
  if (children.length !== 36) fail(`expected 36 frozen children, got ${children.length}`);
  if (new Set(children.map((child) => child.representative)).size !== children.length) fail("duplicate frozen representative");
  return children;
}

function validateParentBinding(filePath) {
  const binding = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const expectedState = ["COMPUTATIONAL", "CI_INDEPENDENTLY_REPRODUCED", "EXECUTION_BOUND", "WORKING"];
  const checks = {
    schema: binding.schema === "borsuk-q00r00-sixth-base-execution-binding-v1",
    status: binding.status === "PASS",
    claim: binding.claim_id === "n11-k6-q00r00-sixth-base-classification",
    evidence_state: JSON.stringify(binding.evidence_state) === JSON.stringify(expectedState),
    run: binding.workflow?.run_id === EXPECTED_PARENT_RUN_ID,
    job: binding.job?.id === EXPECTED_PARENT_JOB_ID,
    job_success: binding.job?.conclusion === "success",
    artifact: binding.artifact?.id === EXPECTED_PARENT_ARTIFACT_ID,
    archive: binding.artifact?.archive_sha256 === EXPECTED_PARENT_ARCHIVE_SHA256,
    source: binding.source?.commit === EXPECTED_PARENT_SOURCE_COMMIT,
    cases: binding.classification?.canonical_sixth_base_cases === 36,
    manifest_hash: binding.artifact?.members?.["child_manifest.csv"]?.sha256 === EXPECTED_CHILD_MANIFEST_SHA256,
    q00r00_unknown: binding.mathematical_status?.q00r00 === "UNKNOWN",
    q00_unknown: binding.mathematical_status?.q00 === "UNKNOWN",
    full_open: binding.mathematical_status?.["n11-k6-full"] === "Gate 2 / OPEN",
  };
  const failures = Object.entries(checks).filter(([, passed]) => !passed).map(([name]) => name);
  if (failures.length) fail(`parent execution binding mismatch: ${failures.join(",")}`);
  return binding;
}

function renderVertices(vertices) {
  return Buffer.from(vertices.map((vertex) => vertex.toString(16).padStart(3, "0") + "\n").join(""), "ascii");
}

function renderPairs(pairs) {
  let text = "left,right\n";
  for (const [left, right] of pairs) {
    text += `${left.toString(16).padStart(3, "0")},${right.toString(16).padStart(3, "0")}\n`;
  }
  return Buffer.from(text, "ascii");
}

function writeFile(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, data);
}

function walkFiles(root) {
  const output = [];
  function visit(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) output.push(full);
    }
  }
  visit(root);
  return output;
}

function renderSha256Sums(root) {
  const files = walkFiles(root)
    .filter((filePath) => !["SHA256SUMS", "generation.json"].includes(path.basename(filePath)))
    .sort((a, b) => posixRelative(root, a).localeCompare(posixRelative(root, b)));
  return Buffer.from(files.map((filePath) => `${sha256File(filePath)}  ${posixRelative(root, filePath)}\n`).join(""), "ascii");
}

function generateChild(root, frozen, parentBinding) {
  const base = [...FIXED_BASE, frozen.representative];
  if (new Set(base).size !== 6) fail(`repeated six-point base entry for ${frozen.child_id}`);
  if (!trimAllowed(frozen.representative, FIXED_BASE)) fail(`frozen representative is not compatible for ${frozen.child_id}`);

  const vertices = [];
  for (let vertex = 0; vertex < (1 << N); vertex += 1) if (trimAllowed(vertex, base)) vertices.push(vertex);
  for (const point of base) if (!vertices.includes(point)) fail(`six-point base is not contained in child trim ${frozen.child_id}`);

  const exactEdges = [];
  const incompatiblePairs = [];
  for (let i = 0; i < vertices.length; i += 1) {
    for (let j = i + 1; j < vertices.length; j += 1) {
      const left = vertices[i];
      const right = vertices[j];
      const separation = distance(left, right);
      if (separation === K) exactEdges.push([left, right]);
      else if (separation > K) incompatiblePairs.push([left, right]);
    }
  }

  const childDir = path.join(root, "children", frozen.child_id);
  const basePath = path.join(childDir, "base.json");
  const verticesPath = path.join(childDir, "vertices.txt");
  const edgesPath = path.join(childDir, "distance6_edges.csv");
  const incompatiblePath = path.join(childDir, "incompatible_pairs.csv");
  const parentMembers = parentBinding.artifact.members;
  const baseRecord = {
    base,
    base_hex: base.map((point) => point.toString(16).padStart(3, "0")),
    child_id: frozen.child_id,
    claim_id: `n11-k6-${frozen.child_id}-universal-trim`,
    dimension: N,
    diameter: K,
    parent_classification: {
      artifact_archive_sha256: EXPECTED_PARENT_ARCHIVE_SHA256,
      artifact_id: EXPECTED_PARENT_ARTIFACT_ID,
      child_manifest_sha256: EXPECTED_CHILD_MANIFEST_SHA256,
      classification_json_sha256: parentMembers["classification.json"].sha256,
      orbits_json_sha256: parentMembers["orbits.json"].sha256,
      source_commit: EXPECTED_PARENT_SOURCE_COMMIT,
      workflow_run_id: EXPECTED_PARENT_RUN_ID,
    },
    predicate: PREDICATE,
    representative: frozen.representative,
    representative_hex: frozen.representative_hex,
    status: "UNKNOWN",
  };
  writeFile(basePath, canonicalJsonBytes(baseRecord));
  writeFile(verticesPath, renderVertices(vertices));
  writeFile(edgesPath, renderPairs(exactEdges));
  writeFile(incompatiblePath, renderPairs(incompatiblePairs));

  const summaryRecord = {
    base: fileRecord(root, basePath),
    child_id: frozen.child_id,
    counts: {
      distance6_edges: exactEdges.length,
      incompatible_pairs: incompatiblePairs.length,
      vertices: vertices.length,
    },
    distance6_edges: fileRecord(root, edgesPath),
    incompatible_pairs: fileRecord(root, incompatiblePath),
    representative: frozen.representative,
    representative_hex: frozen.representative_hex,
    status: "UNKNOWN",
    vertices: fileRecord(root, verticesPath),
  };
  const summaryPath = path.join(childDir, "summary.json");
  writeFile(summaryPath, canonicalJsonBytes(summaryRecord));

  return {
    base,
    base_hex: base.map((point) => point.toString(16).padStart(3, "0")),
    child_id: frozen.child_id,
    counts: summaryRecord.counts,
    files: {
      base: fileRecord(root, basePath),
      distance6_edges: fileRecord(root, edgesPath),
      incompatible_pairs: fileRecord(root, incompatiblePath),
      summary: fileRecord(root, summaryPath),
      vertices: fileRecord(root, verticesPath),
    },
    orbit_size: frozen.orbit_size,
    representative: frozen.representative,
    representative_hex: frozen.representative_hex,
    stabilizer_size: frozen.stabilizer_size,
    status: "UNKNOWN",
  };
}

function generate(output, inputDir) {
  removeTree(output);
  ensureDir(output);
  const childManifestPath = path.join(inputDir, "classification_child_manifest.csv");
  const parentBindingPath = path.join(inputDir, "classification_execution_binding.json");
  const frozenChildren = readFrozenChildren(childManifestPath);
  const parentBinding = validateParentBinding(parentBindingPath);
  const children = frozenChildren.map((child) => generateChild(output, child, parentBinding));
  const expectedIds = Array.from({ length: 36 }, (_, i) => `q00r00-s${String(i).padStart(3, "0")}`);
  if (JSON.stringify(children.map((child) => child.child_id)) !== JSON.stringify(expectedIds)) fail("frozen representatives were not consumed exactly once");
  if (children.some((child) => child.status !== "UNKNOWN")) fail("child status changed");

  const vertexCounts = children.map((child) => child.counts.vertices);
  const edgeCounts = children.map((child) => child.counts.distance6_edges);
  const incompatibleCounts = children.map((child) => child.counts.incompatible_pairs);
  const sum = (values) => values.reduce((a, b) => a + b, 0);
  const manifest = {
    children,
    claim_id: PACKAGE_CLAIM,
    dimension: N,
    diameter: K,
    fixed_five_point_base: FIXED_BASE,
    fixed_five_point_base_hex: FIXED_BASE.map((point) => point.toString(16).padStart(3, "0")),
    parent_classification: {
      artifact_archive_sha256: EXPECTED_PARENT_ARCHIVE_SHA256,
      artifact_id: EXPECTED_PARENT_ARTIFACT_ID,
      child_manifest_sha256: EXPECTED_CHILD_MANIFEST_SHA256,
      execution_binding_input_sha256: sha256File(parentBindingPath),
      source_commit: EXPECTED_PARENT_SOURCE_COMMIT,
      workflow_job_id: EXPECTED_PARENT_JOB_ID,
      workflow_run_id: EXPECTED_PARENT_RUN_ID,
    },
    predicate: PREDICATE,
    schema: SCHEMA,
    status: "PASS",
    status_boundary: {
      children: "UNKNOWN",
      "n11-k6-full": "Gate 2 / OPEN",
      q00: "UNKNOWN",
      q00r00: "UNKNOWN",
    },
    summary: {
      child_count: children.length,
      distance6_edge_count_range: [Math.min(...edgeCounts), Math.max(...edgeCounts)],
      incompatible_pair_count_range: [Math.min(...incompatibleCounts), Math.max(...incompatibleCounts)],
      total_distance6_edges_across_children: sum(edgeCounts),
      total_incompatible_pairs_across_children: sum(incompatibleCounts),
      total_vertices_across_children: sum(vertexCounts),
      vertex_count_range: [Math.min(...vertexCounts), Math.max(...vertexCounts)],
    },
  };
  const manifestPath = path.join(output, "manifest.json");
  writeFile(manifestPath, canonicalJsonBytes(manifest));
  const sumsPath = path.join(output, "SHA256SUMS");
  writeFile(sumsPath, renderSha256Sums(output));
  const generation = {
    claim_id: PACKAGE_CLAIM,
    generated_file_count: walkFiles(output).length,
    manifest_sha256: sha256File(manifestPath),
    schema: "borsuk-q00r00-sixth-base-child-trims-generation-v1",
    sha256sums_sha256: sha256File(sumsPath),
    status: "PASS",
    summary: manifest.summary,
  };
  const generationPath = path.join(output, "generation.json");
  writeFile(generationPath, canonicalJsonBytes(generation));
  return {
    manifest_sha256: sha256File(manifestPath),
    sha256sums_sha256: sha256File(sumsPath),
    summary: manifest.summary,
  };
}

function parseArgs(argv) {
  let inputDir = path.join(__dirname, "input");
  let output = null;
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--input-dir") inputDir = argv[++i];
    else if (argv[i] === "--output") output = argv[++i];
    else fail(`unknown argument: ${argv[i]}`);
  }
  if (!output) fail("--output is required");
  return { inputDir, output };
}

const args = parseArgs(process.argv);
const result = generate(path.resolve(args.output), path.resolve(args.inputDir));
process.stdout.write(JSON.stringify(result) + "\n");
