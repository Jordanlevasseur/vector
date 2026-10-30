# Retrieval specification
SQLite exact IDs/content hashes plus metadata/source/time filters and FTS5 text
ranking precede optional embeddings. Results retain event/source/hash attribution.
Derived text/search indexes can be rebuilt from authoritative blobs and events.
Incremental updates should commit consistently with originals; no full archive scan
per ordinary query. Queries, results and text snippets are bounded and parameterized.
Literal user queries must not become SQL or unchecked FTS query programs. Unicode
and malformed query behavior require tests. Entities/relationships belong to the
knowledge layer. Embeddings and semantic similarity are optional future adapters.
