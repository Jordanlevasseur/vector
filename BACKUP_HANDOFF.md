# Current flash-drive preservation handoff

The current software checkpoint passed 309 source tests and 308 installed tests,
with one installed optional-encryption test skipped. See
[DUAL_MODEL_RUNTIME_REPORT.md](DUAL_MODEL_RUNTIME_REPORT.md) for actual results.
Real 2B inference remains pressure-blocked and complete real Both mode was not
run. Backup preparation does not establish release or reasoning readiness.

The owner requested a flash-drive-ready preservation package. Its staging root is
`/home/mint/Documents/Codex/VECTOR-flash-ready/2026-11-02`.
Use the generated package's README and verification receipt for its actual
completion, size, contents and copy instructions; a staging directory alone is
not proof of a completed backup.

Scope: the current repository/installed environment, consistent SQLite snapshot
and remaining current data files, both external model stores, VECTOR settings,
installed Ollama binary/library files and the current evaluation evidence. The
existing independent backup at
`/home/mint/Documents/Codex/VECTOR-safety-backups/phase1a-20261030/attempt02`
remains separately preserved; its 8.17 GB payload is not duplicated in this new
current-state package. It can be copied separately to larger media if desired.

The package is an inert preservation archive, not a bootable OS image or a newly
qualified VECTOR portable export. Python/system libraries and trusted root-owned
runtime installation remain restoration prerequisites. The known large-library
portable export/restore qualification limitation in PORTABILITY.md is retained.
No hash, schema, isolation or restore validator is bypassed. Recovered data should
remain in a new private location until the normal validation requirements pass.

No existing files, backups, models or defaults are moved/deleted to make the
package. No flash drive is formatted or overwritten automatically.
