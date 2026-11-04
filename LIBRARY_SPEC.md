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

The native dark/cyan interface adds Library as a secondary destination while
preserving Home / Chat, Projects, History and all original workspaces. It provides
metadata/FTS search, category/format/collection filters, sorting, bounded catalogue
pages, complete-source reading windows, PDF/image pages, archive contents, chapter
navigation, search, zoom/text size, saved positions and bookmarks. Custom manual
sections have arbitrary titles/nesting and an explicit complete-revision save.
The desktop save limit is 60 KiB; larger originals remain supported through the
existing file intake. Imported originals are never edited.

`vector-desktop --library` explicitly starts without inference. The additive
`vector-install-desktop --library` command creates VECTOR Library in the local
application menu without replacing an existing customized VECTOR launcher.

Backend batch A passed 364 complete source tests (901.961 seconds, no skips).
Desktop integration batch B passed 369 complete source tests (1120.129 seconds,
no skips), including actual isolated PDF page 1000, archive safety, source
preservation, durable reading/collection state, portable restore and real Tk
reading controls. An earlier terminated batch B run is incomplete, not a pass.
Read-only current inventory verified all 4,588 distinct original streams and
accounted for 4,722 event entries, including 134 duplicates; no missing original
or orphan indexed source was found. Installed acceptance and final preservation
are recorded separately below.

Corpus inspection identified nine archived `.prt` files with the NCBI ASN.1
text header. These receive a bounded inert source-text view, explicitly without
3D rendering. A `.prt` extension alone is insufficient: binary/unknown CAD files
remain unsupported. This small follow-up passed all 19 reader/native-Library
tests (25.493 seconds).

## Installed delivery and measured limits

The final installed package matched all 53 frozen source modules. Its complete
copied regression suite ran 370 tests in 856.121 seconds: 369 passed, no failures
or errors, one existing encrypted-roundtrip test skipped because the installed
interpreter lacks optional `cryptography`. The missing-crypto fail-closed test
passed. The complete source suite had exercised encryption with the dependency
available. No dependency was installed or security fallback enabled.

Actual installed Tk acceptance used a complete independent corpus copy. It
verified all populated categories, metadata and indexed search, original book
windows, chapter navigation (including two body chapters beyond the contents),
search, process restart, font/scroll state, bookmarks, collections and immutable
manual revisions. All 20 standalone PDFs rendered their actual first and last
pages. The 243-page scanned Standard Atmosphere original was read without OCR.
Both archives supplied real PDF, NXML, JPEG and TXT; the molecular source view
was tested with actual NCBI content. All 119 archive member streams were hashed;
116 static member entries are supported. One Flash animation and two QuickTime
movies remain enumerated and inert. Their complete parent archives exported
byte-for-byte. Video/Flash playback, molecular 3D, automatic external-reader
launch and individual unsupported-member export are not implemented. EPUB is
synthetic-test qualified only because no real EPUB exists in this corpus.

Measured interface/backend peak RSS was 56.59 / 73.39 MiB. The isolated renderer
peaked at 83.72 MiB kernel-accounted memory with zero swap or OOM events. Startup
was 2.334 seconds in the measured warm run, not a cold-start guarantee. Actual
renderer and frontend offline/namespace/filesystem/resource probes and cleanup
passed. A separate installed Chat check displayed two genuine local model-A
responses; no model/profile/default change or simulated inference was used.

The host Ollama daemon stayed running because noninteractive stop required a
local password; the owner was advised stopping it is unnecessary. Literal
daemon-stopped acceptance is unverified, while actual no-inference Library
operation passed. The screensaver prevented an unobscured whole-window visual
review; actual Tk controls, compact bounds and document rendering were tested.
These limits are not claims of production-release readiness.

Final rehash verified the complete active SQLite file and all 4,587 stored
original files, including unchanged size/mtime/inode. Active database SHA-256:
`9ca15c36e033f1df3403eb62cec580198f2d56e474defbaf502c03ec7d81fcf2`.
All 4,588 original streams passed integrity; the catalogue accounts for 4,722
events / 134 duplicates and retains all 1,288,804 literary passages. Settings,
laws, old launcher, conversations and knowledge remained unchanged. No SQLite
DDL, reimport or index rebuild occurred; the previous incomplete full structural
scan is not relabeled as passing.

The full completion, coverage, operator-error diagnoses, exact evidence and
code-only rollback instructions are preserved in the Codex workspace folder
`outputs/vector-library-implementation-20261103`. Two operator reporting issues
(pre-resize scroll expectation and skipped-TestCase JSON serialization) were
corrected with their failed evidence retained; no application checks were
weakened. Verified data/package/Git backups remain available there.
