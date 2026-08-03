# q00 crosswalk artifact trust boundary

The differential implementation and its crosswalk execute only in the read-only workflow `.github/workflows/verify-q00-five-base-crosswalk.yml`.

That workflow:

- receives `contents: read` only;
- checks out the exact event commit with `persist-credentials: false`;
- executes the governed and differential implementations;
- confirms the governed boundary hashes are unchanged;
- binds the canonical result to the successful push run and exact head SHA;
- uploads one immutable JSON artifact;
- never commits or pushes repository content.

The write-enabled recorder is `.github/workflows/record-q00-five-base-crosswalk.yml` on the repository default branch. It is triggered through `workflow_run` and does not check out the feature branch, execute repository code, restore caches, or install packages.

Before writing, the recorder obtains authoritative identity through the workflow-run event and GitHub API and requires:

- the fixed upstream workflow ID, name, and path;
- a successful push event;
- the expected repository, head repository, branch, and exact head SHA;
- exactly one non-expired artifact associated with that run and commit;
- a matching SHA-256 artifact digest;
- exactly one regular JSON member with the fixed filename;
- the fixed result schema, governed hashes, complete 12-class bijection, and unchanged-status flags;
- the feature branch still pointing to the verified head immediately before the write.

The recorder then uses GitHub's contents API to replace only:

`borsuk_11_k6_q00_five_base_reduction/differential/crosswalk-result.json`

It supplies the existing blob SHA and refuses to derive the destination, branch, workflow identity, or authoritative commit identity from the artifact. The artifact's embedded run metadata is only cross-checked against the trusted event and API values.

The recorder does not rerun the crosswalk implementation. Its commit contains the exact canonical bytes downloaded from the verified artifact.
