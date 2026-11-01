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

## Verified Lenovo pilot, 2026-10-31

The controlled first batch preserved 22 complete publication files / volume
editions (approximately 14 title families), totaling 75,110,309 original bytes.
All 2,631 supplied text segments were committed for 21 publications. U.S. Standard
Atmosphere (1976) is preserved as an original only: garbled scan/OCR text was
explicitly deferred. Full originals retain figures, tables and equations; linear
text extraction is not certified semantic mathematics or structured table data.

Accepted sources: 15 DOE handbook volumes across mathematics, classical physics,
heat transfer/fluid flow, electrical/mechanical science, chemistry and materials;
NIST AI RMF 1.0, SSDF 1.1 and measurement-uncertainty TN 1900; two NASA references;
and NCBI's Blood Groups and Red Cell Antigens (2005) and Genetic Landscape of
Diabetes (2004). Both medical books are explicitly historical. DOE dates come from
1992/1993 covers, not 2026 upload timestamps. All approved rights classifications
are U.S.-only government/public-domain determinations with source-specific evidence.

The owner excluded all noncommercial restrictions. OpenStax, two OpenRN nursing
archives with embedded NC assignments, and works with unresolved IEEE, GE,
Australia Post/Royal Society or other third-party components were withheld.
Staging evidence is not an approved corpus import. No worldwide reuse or future
training clearance is inferred. Calculus, comprehensive anatomy/pharmacology,
civil engineering, modern astronomy and general algorithms remain coverage gaps.

Actual production import took 1,065.308 seconds. Fresh-process verification took
135.977 seconds with event counts unchanged at 4,722. Every original was rehashed;
all supplied segment hashes/parents and 21 independent literal retrieval queries
with exact stored spans and original attribution were checked. No model inference
was used. Import controls were verified at 512 MiB RAM, zero swap, 32 tasks and one
CPU quota; sampled peak cgroup memory was 258,363,392 bytes with zero swap/OOM kills.

The unchanged 1,000 literary-edition and 1,288,804 passage tables retained their full
fingerprints. All 2,002 old managed-object files and their metadata, old immutable
records, preferences, model-store inventory and existing safety-backup inventory
matched the pre-ingestion checkpoint. Quick-check and foreign-key checks passed.
Observed active-data growth was 93,844,848 bytes, including indexes and metadata.
The scoped pre-ingestion SQLite/object checkpoint is not a new full-system restore
qualification. All 21 recorded operator scopes were independently verified removed.
The unchanged production integrity validator also passed in 489.790 seconds:
4,587 managed objects, 4,588 blobs and 4,722 events, with no errors and without
extending its 900-second deadline.

Implementation checkpoint: `bdfe5e900ca3ab72f1e69aac65b97d6a872c66e6`.
Regression: 146 baseline tests passed; 158 source tests passed after implementation;
installed environment passed 157 with one optional encryption roundtrip skipped
because cryptography is absent there. The skip is not a passing encryption test.
All 44 installed modules match committed source; Foundational Laws are unchanged.

Operator receipts, exact source/rights metadata, original hashes, extraction
manifests, timings and acceptance reports are retained under
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-science-phase1`.
The reviewed pack manifest SHA-256 is
`98b4a8221187402a1fd10ff6b6d07f9820c1e0d4cc7eb58dd881d45c1d749542`.
Those operator paths are evidence locations, not runtime dependencies. Originals,
evidence and registered scientific records remain in VECTOR's existing portable
store. No release-readiness, neural learning or general reasoning claim follows.
