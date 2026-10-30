# Architecture
Python 3.12+, standard library, SQLite/FTS5, Linux libseccomp. No runtime Python
dependencies, external services or HELIX imports. `cli` installs mandatory kernel
policy before config/data operations. `config` owns an independent private data
scope; `intake` reads explicitly selected regular files through no-follow directory
handles; `database` owns transactional migrations and durability. `maintenance`
owns local logs and consistent non-overwriting backups. Memory, retrieval and
knowledge are separate layers built over authoritative originals. Models never
own memory or control authorization. Early stages expose a bounded CLI; a minimal
desktop can follow verified persistence/retrieval. No speculative services.
