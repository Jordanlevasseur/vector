# Scientific knowledge library: controlled pilot

Scientific publications use the existing permanent Memory/events/managed-object
store, versioned persistence contracts and original-verified FTS5 retrieval.
There is no second knowledge database, downloader in the runtime, model change,
neural training, fact promotion or modification of literary passage indexes.

Acquisition and PDF/HTML extraction are trusted operator staging jobs outside the
network-denied core. A reviewed `vector-scientific-pack-v1` manifest identifies
complete originals, hashed rights evidence, authors, edition/dates, subjects,
U.S. jurisdiction, explicit pilot-use permissions and extraction manifests.
This pilot excludes noncommercial licenses and sources with AI-use restrictions.
Public readability or government hosting alone is not sufficient rights evidence.
All future training requires separate source-specific review. Medical references
retain dates and are explicitly historical or dated references, never silently
current clinical guidance.

`scientific_editions` and `scientific_runs` are validated portable records in the
existing SQLite database. The full original and rights documents are archived
before any scientific text pages are acknowledged. Streaming intake can compare
an expected SHA-256 before acknowledging an event. Unacknowledged content may
remain preserved after a failure; it is never an accepted publication.

Extraction manifests bind every UTF-8 page to the complete original hash and a
source locator. Pages are separately preserved derivatives linked to the original
event, not representations that replace PDF, HTML, images or archive bytes.
Equations, tables, figures, external assets and text completeness always have
explicit extraction status. A completed indexing checkpoint means all supplied
text pages were committed, not lossless mathematical/visual understanding.

Each page commits before the durable resume cursor. A crash between those commits
reuses the existing verified page event. Modified manifests, corrupt/missing
pages, invented original links and unreviewed rights fail closed. Resume cursors
cannot acknowledge missing pages. Reimporting the same reviewed edition is
idempotent; changed metadata requires explicit revision review.

From this checkout, using a new reviewed local package:

```bash
PYTHONPATH=src python3 -m vector_core --data-dir /absolute/vector-data science import \
  --package /absolute/science-pack --limit 1 --approve
PYTHONPATH=src python3 -m vector_core --data-dir /absolute/vector-data science index \
  --package /absolute/science-pack --edition EDITION_ID --limit 10 --approve
PYTHONPATH=src python3 -m vector_core --data-dir /absolute/vector-data science search \
  --query 'specific heat' --limit 10
```

Repeat bounded index slices until `status=complete` or `deferred`. Import responses
provide `next_cursor` and `manifest_sha256`; resume with both `--offset` and
`--manifest-sha256`. The bounded pack/slice sizes are operating safeguards, not
permanent corpus limits. Existing service dispatch also exposes `science_import`,
`science_index` and `science_editions`; no model output dispatches these operations.

Normal search and assistant context include scientific provenance, original
container SHA, locator, license, dates, medical status and extraction limitations.
The quoted text hash is the stored derived-text hash; the original publication
hash is separate. Both remain available and validated. No source assertion becomes
an independently established scientific fact merely by entering the index.
