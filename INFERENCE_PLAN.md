# Next milestone: separately secured inference and bounded evidence contracts

Current runtime denies every socket family and new processes. That boundary is
qualified for memory/retrieval/knowledge without a model. Do not relax it to reach
an existing unqualified inference daemon. Its network restrictions are unverified,
and changing shared services could interfere with other applications.

Before enabling Stage 5, prepare a dedicated VECTOR inference service, independent
from HELIX, with verified OS external-egress denial and fixed authorized model
storage. Prefer a dedicated network namespace plus a narrowly exposed local IPC
broker. Do not grant VECTOR unrestricted Unix sockets or TCP because either could
reach a forwarding service. Never change global sysctls, reuse a shared daemon as
if qualified, download models or start resource-heavy inference without checking
RAM/disk. No service was started or host-wide policy changed in this milestone.

The client contract should include replaceable adapter/capability profiles,
explicit context/output budgets, evidence IDs/hashes and bounded source excerpts,
strict response validation, no model-issued commands, and separate uncertainty and
source/citation checks. Qualify model behavior on independent multi-source tasks;
retain deterministic retrieval when the model/service is absent. A larger local
model is not itself proof of reasoning quality.

Enabling this profile/service is a separate security and host-configuration step,
not routine archive use. Its concrete files/host policy must be reviewed and tested
before activation. Stage 5 acceptance has not passed; subsequent dependent reasoning,
tool and release milestones cannot be reported complete. A minimal desktop may be
built earlier, but needs a separately tested display/IPC policy: the current strict
Unix-socket denial deliberately does not permit X11/Tk connections.
