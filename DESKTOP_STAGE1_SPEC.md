# Native futuristic desktop, Stage 1

Presentation redesign over the existing Tk application and protected backend.
`desktop_theme` defines local color/font/spacing tokens, a bounded Canvas core,
a multiline input adapter and scrollable detailed workspaces. `desktop_shell`
provides navigation and presentation. Existing `desktop` operation handlers,
original-source links, approvals, learning/library, tools, projects and settings
remain connected to the shared application. No framework, schema, model default,
cognition, authority, inference qualification or network-policy migration.

Primary navigation is exactly Home / Chat, Projects, History, selected using the
upper-left three-line hamburger. Knowledge, Memory, Investigations, Settings and
Advanced are secondary entries below a divider. No permanent sidebar or root
Notebook is created. Six legacy component frames are retained internally so
existing integrations continue to work; they are not top navigation tabs.
Library subwindows retain their existing specialized tabs. Menu toggle, Escape,
outside click, arrows and normal Tab/Enter activation work with keyboard focus.

Home uses one bubble-free text stream, a fixed bottom multiline command area,
Enter to send and Shift+Enter for a line break. Drafts and widget/scroll state
survive view changes. Appends follow the bottom only when already there;
otherwise the current top text index is retained and Latest becomes available.
Opening a different conversation explicitly resets its stream; unrelated sessions
are not silently concatenated. Original backend records remain complete.

The original Canvas identity uses segmented rings, a geometric V, illuminated
nodes and circuit paths. It fills the empty conversation area, then contracts
above active text. Idle animation is one frame/second, actual pending operations
four; hidden views stop their timer and minimized windows skip drawing. No GPU,
blur, video, external artwork or remote font is used. Shutdown cancels the timer.
Backend loss stops the activity visual and disables sending rather than implying
continued processing. Model availability is distinct from local core readiness.

Settings can persist a reduced-motion boolean through the existing registered
preferences contract; invalid fields/types are rejected, including portable
imports. No appearance record is created automatically. `VECTOR_REDUCED_MOTION=1`
is honored at startup without requiring a desktop-settings service or new socket.
The preference affects only rendering and is included in existing portable backup.

Projects reuse existing creation, opening, linking, item revision, archive,
conversation and source/history handlers. History uses paginated real saved turns,
showing original timestamps and project context; original record/session identities
remain inspectable. The only browse query change adds existing created/id fields.
Investigations show persisted status/objectives and expose actual plans, findings,
checkpoints and planned-chat controls. Unknown/unplanned histories remain accessible
through the original controller and checked-result views. Experimental controls
are progressively disclosed and remain disabled by default. Checked arithmetic
presentation omits low-level dimension vectors but retains expression, value,
qualifications and dependent-result status; the full unchanged verified document
is available for inspection. Source, uncertainty and simulation labels are kept.

Knowledge retains source search, claims, provenance, filters, memory categories,
relationships, assessments and exact exports. It also opens existing Learning and
Literary workspaces. Memory reuses the same actual memory recall controls instead
of creating a separate store. Advanced retains calculations, storage, integrity,
logs/diagnostics, recovery and backup actions with their original approvals.
Detailed workspaces scroll horizontally/vertically when controls exceed the
laptop's width. Raw record inspection remains a technical secondary view.

Qualification requires real local X11 interaction, menu open/closed screenshots,
short/long conversations, upward scrolling, draft navigation, actual saved project
and history reopening, model-unavailable operation, offline syscall denial,
reduced motion, cleanup, source/installed regressions, performance and preservation.
Fixture text in UI acceptance is explicitly authored test data, not neural output.
No GUI test establishes neural reasoning quality, human usability, native Wayland,
screen-reader compliance or broad international-script layout quality.
