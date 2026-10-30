# Retrieval specification
SQLite exact IDs/content hashes plus metadata/source/time filters and FTS5 text
ranking precede optional embeddings. Results retain event/source/hash attribution.
Derived text/search indexes can be rebuilt from authoritative blobs and events.
Incremental updates should commit consistently with originals; no full archive scan
per ordinary query. Queries, results and text snippets are bounded and parameterized.
Literal user queries must not become SQL or unchecked FTS query programs. Unicode
and malformed query behavior require tests. Entities/relationships belong to the
knowledge layer. Embeddings and semantic similarity are optional future adapters.

## Implemented Stage 3
Contentless FTS5 stores postings only; excerpts come from original-validated text,
not another authoritative content copy. A transaction commits original events,
UTF-8 representation and postings together. Query tokens are quoted literal AND
terms, max 16 terms/512 characters; results max 100 (default 20). Search supports
source identity, explicit-zone time ranges and up to four typed scalar metadata
filters through the Python interface. Exact event/hash lookup uses SQLite indexes.
Rebuild re-extracts originals and replaces derived text/postings atomically; original
hash failure aborts without partial index commit. No embeddings/entity graph yet.

Stage 4.5 large originals are retained and exported using bounded streams. Originals
above the configured text-extraction budget have explicit deferred-index status;
index rebuilding verifies their bytes and retains that status. This is not full
lexical indexing of arbitrarily large files. Exact original retrieval and portable
restoration remain available independently of derived full-text coverage.

Project/category filters use registered indexed associations; source/time filters
remain explicit. Excerpts retain exact offsets around a literal hit, including late
in a file. Context prioritizes original coverage, then derived state; bounded exact-
entity/one-hop and comparable-claim expansion can include related source evidence.
Default project contexts prefer associated sources while retaining global matches.
Explicit project-only recall is available without changing global originals.
MEMORY_INTELLIGENCE_SPEC.md records limits and benchmark acceptance scope.
