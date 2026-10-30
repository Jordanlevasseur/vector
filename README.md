# VECTOR
Independent offline permanent-memory and evidence-system foundation. Development
build, not J.A.R.V.I.S., not a qualified reasoning system and not dependent on HELIX.

Python 3.12+, SQLite and Linux libseccomp are required. No model is required.
From this checkout: `PYTHONPATH=src python3 -m vector_core --data-dir /absolute/private/vector-data health`.
The selected data directory must be new/empty or already owned by VECTOR.
Local install: `python3 -m pip --isolated install --no-cache-dir --no-index --no-deps --no-build-isolation .`.
Do not fetch missing tools. Run tests with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
See SECURITY.md, ARCHITECTURE.md, ROADMAP.md and ACCEPTANCE.md for actual scope.
