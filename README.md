# VECTOR
Independent offline permanent-memory and evidence-system foundation. Development
build, not J.A.R.V.I.S., not a qualified reasoning system and not dependent on HELIX.

Python 3.12+, SQLite and Linux libseccomp are required. No model is required.
From this checkout: `PYTHONPATH=src python3 -m vector_core --data-dir /absolute/private/vector-data health`.
The selected data directory must be new/empty or already owned by VECTOR.
Local install: `python3 -m pip --isolated install --no-cache-dir --no-index --no-deps --no-build-isolation .`.
Do not fetch missing tools. Run tests with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
See SECURITY.md, ARCHITECTURE.md, ROADMAP.md and ACCEPTANCE.md for actual scope.

## Current installed entry point
The independent local environment is `.venv` (no system-site packages). Run
`/home/mint/VECTOR/vector/.venv/bin/vector health` or use its `vector` console
entry point in that environment. Default private data: `~/.local/share/vector`.
`config.example.toml` shows the optional independent settings format.

Commands include `add --file PATH` (or `--text TEXT`), `list`, `show EVENT --text`,
`export EVENT NEW_PATH`, `search TERMS`, `verify`, `rebuild`, `backup` and
`restore BACKUP_DIRECTORY` with a new `--data-dir`. Export/restore never replace
existing files/data. Global options precede commands. Extraction failures preserve
original events and are reported explicitly.

`learn --file PATH --scope NAME --exclusive` handles explicit pipe statements.
`conflicts` displays supported disagreements, `claim ID` displays source evidence,
and `override ID --scope NAME --value VALUE --reason REASON --approve` records an
explicit operating assumption without rewriting evidence. Ordinary prose is stored
and searched but is not automatically understood or certified as factual.

The previous Stage 4 checkpoint passed 43 source and 43 installed tests.
Stage 4.5 adds portable repositories, streamed storage and managed inert assets;
see PORTABILITY.md and the latest PROGRESS.md results. See PROGRESS.md/BENCHMARKS.md for measured scope. No graphical interface or
model inference is enabled yet; no broad release/J.A.R.V.I.S. capability is claimed.
Your supplied master directive is preserved verbatim in DIRECTIVE.md and archived
as a distinct source event in the private default database. This is retained source
material, not verified truth or neural/model learning.

Complete portable backups use `export-vector`, `verify-export` and `restore-vector`.
Database-only `backup` refuses managed assets. Storage diagnostics, paging and
verified `move-data` are available through the CLI; desktop actions remain pending.

Stage 4.5 final Lenovo results: 67/67 source tests passed; independent installed
suite passed 66 with one optional-encryption test skipped (cryptography absent in
.venv). Host encryption tests passed. The real default original was migrated and
actually restored byte-identically. See PROGRESS.md for the exact qualification
boundary and BENCHMARKS.md for measured 50,000-event growth.
