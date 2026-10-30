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


## Offline desktop and assistant
After local wheel installation, run `.venv/bin/vector-install-desktop` once to add
VECTOR to the Linux application menu. The ordinary launcher needs no model.
Menu actions also open an explicitly selected local Ollama models folder, use
managed imported models, or choose another private VECTOR data folder.
Run `.venv/bin/vector-desktop` directly if desired. Only local X11/XWayland is
supported; remote displays and unqualified inference workers fail closed.

Assistant uses original-linked evidence. Model responses are unverified inferences,
never automatic facts. Without a model it displays matching source excerpts rather
than fabricated generated answers. Knowledge/learning/projects/tools/storage actions
use functioning subsystems; supported deterministic tools are available without AI.
Settings exposes model budgets, storage, verified backup/restore, relocation and
separate recovery keys. Optional encryption needs locally installed cryptography;
the isolated .venv reports its absence rather than falling back to plaintext.

CLI additions: `models`, `ask QUESTION --model NAME --models-directory PATH` or
`ask QUESTION --model NAME --managed`, and
`calculate arithmetic '{"expression":"2+2"}' --approve`.
Global data/config options precede commands. Inference uses verified private
namespaces/cgroup limits and explicit pipes, never the shared Ollama endpoint.
Selecting external weights blocks complete exports; import assets through Settings,
then relaunch Managed Models for portable runtime selection. Runtime binaries are
separate platform dependencies. See DESKTOP_SPEC.md and INTELLIGENCE_SPEC.md.

A reproducible actual-model check is available with
`PYTHONPATH=src python3 -m vector_core.model_qualification --models-directory PATH --model NAME --timeout 240`.
Add `--roundtrip` to import real local assets, export and restore them before the
trial. These are bounded temporary-data acceptance runs, not simulated answers,
not large-model downloads and not proof of general reasoning or release readiness.


Lenovo qualification (2026-10-30): 95 source tests passed; installed tests 94
passed and one optional encryption test skipped (dependency absent). Real Qwen
0.5B scored 0/3 on the independent two-source verbatim task despite valid citations.
The tested model profile is context 4096/output 512/timeout 240 seconds; the
short default deadline may be insufficient for cold model loading on this Lenovo.
Set budgets explicitly in Settings rather than assuming inference is fast.
Current desktop/archive/search/manual tools are experimental usable foundations;
reliable general AI assistance and release readiness have not been established.
See ACCEPTANCE.md and ROADMAP.md for remaining gates.

## Memory and project organization
Open VECTOR from the application menu. In Projects, enter a name and click Create
project. The project opens immediately; subsequent Learning imports are associated
with it. Select an existing Knowledge source and choose Link selected source in
Projects to reuse it without copying original data. Sources, History and Archive /
restore inspect durable associations and status; leaving a project preserves all
its knowledge and returns to global work.

Use the item form for goals, requirements, notes, decisions, tasks, milestones,
questions and hypotheses. Save revision records the text/status and selected source
as evidence. Click Items for the next page, select an item to edit, and save its new
revision. New item clears editing. All earlier versions remain in History.

Knowledge's memory selector provides episodic, semantic, procedural, project and
working views. Recall memories uses the text query and optional explicit-zone ISO
Since/Until dates, project/source filters. Global search remains available across
projects. Compare / versions shows exact duplicates, literal overlap candidates and
source ancestry. Relationships and assessment controls retain evidence/uncertainty.
Learning's deferred queue does not require a model. Reconcile selected evidence
compares explicit claims and requests review rather than silently choosing truth.

Assistant's saved-session browser resumes older conversations; Load saved
conversation pages complete saved turns. Short follow-ups can use prior user
questions for literal retrieval. Originals are allocated before project notes in
bounded contexts. Model-generated answers remain unverified and cannot approve
knowledge or run tools. See MEMORY_INTELLIGENCE_SPEC.md for precise limits.

You may multi-select up to 64 Knowledge sources per Link selected source operation.
The batch commits atomically; invalid references or interruption cannot acknowledge
partial links. Repeat batches to organize larger collections; total project size
has no application count cap.
