# Library browsing repair

The existing Library opens directly in All Books. It uses Resources.list's
`bookshelf` presentation over existing original events and edition/manual records;
there is no separate catalogue database or importer. Registered editions and manuals,
botanical originals, other original documents and retained attachments are included.
Extracted pages, rights records and unacknowledged raw objects remain available in
More → All stored records and Coverage, rather than masquerading as complete books.

An empty metadata query lists resources. Browsing does not need an AI adapter. The
first 40 rows load on entry; reaching the bottom/top loads adjacent pages. A maximum
of five pages (200 rows) is rendered. Page-boundary history supports reverse traversal
without losing short, byte-bounded pages. Returning from an original retains the
browse window and scroll position. A browse sequence freezes recent-order sorting
until the next search so opening a book cannot cause duplicate/skipped pages.

Search is optional and updates after typing; clearing it restores the current
category's full collection. Category and collection options come only from actual
nonempty stored metadata, with counts. Five sorts cover title ascending/descending,
author, addition date and reading history. Reading indicators use stored locations,
not invented percentages. A shared local book icon is used when no cover is registered;
archives and full originals are not decoded merely to decorate the catalogue.

Advanced search, collection editing, manuals, source details, export, inventory and
Botanical research remain in More. Existing main destinations and readers are retained.
Normal browsing does not scan full-text payloads or stat every original. Detail/open
still checks original file descriptors, and the existing open/export SHA-256 and
protected reader checks remain mandatory. Full inventory retains explicit location
checks. Additive migration10 indexes the existing events.parent_id relationship; it changes no original, passage, bookmark, setting, model or law. Installation requires a verified schema9 recovery checkpoint.

Loading is explicit. A successful response sets loaded state; errors remain inline
with retry guidance. Stale responses cannot replace newer filters. A dead backend
reports its technical failure and restart requirement, rather than an endless blank
or pretend retry. No security qualification or network denial is relaxed.

Source and actual installed acceptance evidence, preservation measurements and the
final checkpoint are recorded in outputs/vector-bookshelf-repair-20261109 in the
Codex workspace. This document describes behavior, not a substitute for test results.
