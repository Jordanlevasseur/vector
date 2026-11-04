# Unified native Library

The Library extends the existing original-event, managed-object, FTS and portable
state systems. It is not another knowledge database. Catalogue entries retain
event/source IDs and original SHA-256; duplicate submissions are distinct from
unique byte streams, bibliography and passage counts. Derived pages and evidence
attachments remain identifiable and lead back to their publication when known.

`resources.Resources` supplies bounded list/detail/search/reference/read/outline
operations. The native interface uses pages of metadata, not a million-passage GUI
list. Complete original text uses bounded character windows, not derived passages.
Original bytes are verified and materialized only in disposable private reader
storage. Archive members are copied as bytes to private files; archive paths,
links, executable assets and remote references are never executed or extracted
into the original store. Unsupported resources remain visible with explicit
reasons and an exact-original export path.

`reader_runtime` loads installed Poppler/Cairo/GdkPixbuf inside a separately
qualified Bubblewrap namespace and cgroup: no network, no nested user namespace,
no host home/original mounts, read-only input, no exec/fork, 512 MiB memory,
zero worker swap, 32 tasks and one CPU quota. Only selected pages are rendered.
Raster output stays in private bounded tmpfs and is transferred in bounded chunks;
the core verifies PNG framing, dimensions, size and hash before native display.
A file error does not terminate an otherwise healthy reader. Real worker failures
remain explicit and fail closed. Inference code and model selection are separate.

Reading state, bookmarks, collection membership and authored manuals use new
validated registered contracts in existing `persistent_records`. No SQLite DDL or
schema-version migration is required. Originals and previous metadata versions
remain immutable. An authored manual saves a complete immutable Markdown source
and a hash-bound structured revision; partial edits never replace its previous
published revision. Portable restore validates new record shapes/source bindings.

`read_tool` is the narrow future model-facing interface: only enumerated read
operations are permitted. It does not expose the full application dispatcher,
imports, approvals, index resets, state writes or commands. Native chat is not
modified to search automatically. Human browsing requires no model.

Implementation is staged. Backend/reader batch A passed 364 complete source tests
(901.961 seconds, no skips), including original preservation, actual isolated PDF
page 1000, archive safety, durable reading/collection state and portable restore.
Native UI integration, installed runtime acceptance, corpus coverage and final
preservation are separate required checks before claiming the Library delivered.
