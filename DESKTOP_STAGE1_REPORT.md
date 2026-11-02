# VECTOR futuristic desktop — Stage 1 measured report

Implemented and installed from clean baseline 3bbb37f270160782cfb0d7a7327fa6b9aef5dd9f.
Implementation commit: 7bcb138f1d08e9faac68123ea6829e2fbd2f24d2. The report-only final HEAD and clean
main/checkout/package verification are recorded in [FINAL.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/FINAL.json).
This is native desktop Stage 1 acceptance, not HELIX/VECTOR release qualification.

## Audit and reuse

The existing desktop is Python/Tk with a separately kernel-protected backend and
bounded identity-checked pipe messages. The original six workspaces were Assistant,
Knowledge, Learning, Projects, Tools and Settings. They supplied actual Ask,
source/claim/provenance lookup, memory recall, library/learning review, projects,
calculations, model configuration and storage/backup/recovery. Investigation and
saved-session access already existed through shared service handlers. Production
was clean at 3bbb37f; all existing knowledge and preferences were inspected through
repository reports, snapshots and runtime checks. Existing handlers are retained.

New modules: desktop_theme.py (native tokens, widgets and Canvas identity) and
desktop_shell.py (presentation/navigation). desktop.py retains operation handlers.
service.py adds existing timestamps/IDs to read-only history browse, returns
appearance metadata and stores only a strictly checked reduced-motion boolean.
projects.py validates that preference during writes/restores. Existing registered
preferences are reused; no schema or duplicate memory/controller is added.
New tests/test_desktop_stage1.py, tools/evaluate_desktop_stage1.py and
DESKTOP_STAGE1_SPEC.md accompany updated ARCHITECTURE.md and DESKTOP_SPEC.md.
README points to this measured report. Cognitive, model, verification, security,
authority and Foundational Law modules listed in the final integrity gate are
unchanged. Six legacy frames remain internal components, not navigation tabs.

## Interface and real capabilities

- Upper-left three-line hamburger, hidden by default, with exactly Home / Chat,
  Projects and History above a divider. Knowledge, Memory, Investigations,
  Settings and Advanced are secondary. Toggle/Escape/outside dismissal, arrows
  and keyboard activation work; there is no permanent sidebar or root Notebook.
- Dark graphite/midnight surfaces, cyan/ice highlights, thin circuit paths and an
  original segmented circular V core. No remote assets, browser, GPU renderer or
  downloaded fonts. The empty core is central, and contracts above active text.
- One open conversational text stream with no bubbles. New content appends;
  scrolling upward retains the actual reading index. Latest returns to the end.
  The bottom multiline composer stays visible; Enter submits, Shift+Enter adds
  a line. Navigation preserves the widget draft and existing stream position.
- Investigation/evidence controls use progressive disclosure. Planning and
  connected evidence remain disabled by default. Checked arithmetic shows real
  expressions/results/qualifications, with full original records inspectable.
  Source, uncertainty, conflict, hypothesis and simulation labels are retained.
- Projects reuse actual creation/opening, source links, notes/objectives/items,
  revisions, archives and histories. History displays real saved turns with
  original timestamps and identities, reopens their actual conversation/project,
  and retains paging rather than limiting stored history to one screen.
- Investigations list persisted objectives/status, expose plans/checkpoints and
  findings, and support explicit pause/cancel/resume through existing controls.
  Resume uses 16 local steps/zero model calls/30s; an active backend operation is
  interrupted using the existing top Cancel control. No model-issued commands.
- Knowledge retains originals/search/claims/provenance and opens Learning and
  the literary workspace. Memory reuses actual category/filter/recall controls.
  Advanced keeps calculations, storage/integrity, backups, recovery and diagnostics
  with original approvals. Settings contains existing model controls plus portable
  reduced motion. Detailed workspaces scroll on smaller screens.
- Activity is tied to actual pending client operations; backend loss stops it.
  Model-unavailable mode remains usable for sources and checked calculations.
  The core's idle identity animation does not imply neural processing.

No voice, attachment simulation, decorative investigation completion or fake
intelligence metrics were added. Buttons connect to real existing operations.

## Actual runtime evidence and performance

Ten screenshots show actual protected X11 windows, not mockups or model responses:
[Home](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/01-home-idle.png),
[open menu](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/02-menu-open.png),
[Projects](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/03-projects.png),
[checked conversation](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/04-checked-conversation.png),
[History](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/05-history.png),
[Investigations](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/06-investigations.png),
[Settings](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/07-settings.png),
[Advanced](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/08-advanced.png),
[820×600 layout](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/09-small-screen.png),
[reading older content](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/10-reading-history.png).

The isolated acceptance database contains explicitly authored UI fixture records:
a real saved project/item and a checked 40→5 dependent calculation. They are not
production knowledge, simulated neural output or claims about model capability.
Actual Enter/Shift+Enter, menu states, drafts, long scrolling, project/history
reopening, investigation pause/resume, reduced motion and network denial passed.
The installed GUI also opened actual preserved production knowledge,
investigations and all 1,000 literary editions/1,288,804 passages read-only;
preferences, event count and authoritative record count were unchanged.

Measured on the Lenovo at 1060×700 and 820×600:

| Measure | Actual result |
|---|---:|
| Frontend peak RSS | 31.34MiB |
| Backend sampled RSS | 27.30MiB |
| Animated idle CPU,15s | 1.16% of one CPU core |
| Reduced-motion idle CPU,15s | 0.77% of one CPU core |
| Idle core redraws, animated/reduced | 14 / 0 |
| Cached presentation navigation median/max | 6.76 / 17.00ms |
| Neural calls | 0 |

Navigation timings cover native view/layout changes, not database/model latency.
RSS values are separate process measurements, not a simultaneous summed peak.
The 15s idle samples are limited measurements, not a long-duration thermal/battery
qualification. Animations use one frame/second idle and four for actual work;
hidden views stop their timer and minimized windows skip redraws. Reduced motion
persists in portable preferences and VECTOR_REDUCED_MOTION=1 is honored at startup.

## Tests and integrity

Unchanged production-checkout desktop baseline:5/5 passed in 23.560 s. Previous
clean3bbb37f full source evidence was226/226. An early226-test development run
and an expanded230-test run also passed; those ran against an evolving checkout
and are not represented as the final frozen regression result. Test harness
newline quoting errors were fixed without changing assertions. A concurrent-GUI
Escape check lost focus to another test window; explicit test-window focus and
serial final acceptance retain the original Escape assertion. Failed logs remain.

Final frozen source: **230 passed, zero skipped**, 784.339s.
Installed isolated runtime: **229 passed, one skipped**, 613.459s.
The skip is the positive encrypted roundtrip because optional cryptography is
absent from the isolated interpreter. Its positive source-host test passed;
installed encryption remains unverified and does not fall back to plaintext.
The original 52 model-disabled checked-answer cases and all existing controls are
retained. All 49 installed modules match the tested source/wheel exactly. Ordinary
new socket creation (IPv4,IPv6,Unix) is denied in the real redesigned GUI.

The initial full integrity attempt reached its 900-second deadline during SQLite
integrity checking; it is retained in preservation-after.log and is not counted
as passing. A separate read-only QA replay uses a 64 MiB connection-local cache
and 1,800-second validation budget, with identical complete checks. Application
cache defaults, validation logic and security/resource policies are unchanged.
A successful replay certifies preservation under that documented QA configuration;
it does not qualify the original 4 MiB/900 s cold-scan performance. Cache warmth may
also affect timing; no causal performance comparison is claimed. Large-database
verification performance remains a separate engineering issue.

A fresh consistent production database snapshot was certified before installation.
Previously independently verified original-object copies were retained, not
relabelled as newly copied. Final preservation passed in 1001.853 s,
including full portable database/source/provenance validation. All1,000 literary
editions, 1,288,804 passages, 22 scientific editions and 2,631 segments retain exact
fingerprints. All 4,587 original objects and their independent copies match;
all 18 prior history prefixes are unchanged. Preferences, both model inventories,
existing backup inventory, laws and schema 8 are unchanged. No corpus import,
model/default change, training, network relaxation or HELIX modification occurred.
The mandatory frontend/backend offline and qualified inference boundaries remain.

## Limitations and Stage 2

Native X11/XWayland remains required; native Wayland-only qualification is deferred.
Detailed library/learning and record-inspection dialogs retain established
technical controls, now themed and accessible through secondary navigation.
Memory shares the existing recall workspace, rather than introducing a new memory
engine. Draft and scroll retention cover live navigation; per-conversation draft
recovery across crashes is not claimed. History uses existing cursor browsing,
not newly invented semantic search. Full screen-reader, RTL/international-script,
high-DPI and human-usability acceptance are not claimed. No actual neural inference
was needed or attempted for this UI task; model-unavailable mode was qualified.

Stage 2 should prioritize human-readable expandable evidence/findings panels,
accessibility and international-layout testing, clearer end-of-history/search
controls, and durable per-conversation drafts. Richer effects remain optional;
they should preserve the measured lightweight profile. Experimental cognition
remains opt-in, and this UI does not establish general intelligence or release
readiness.

Full evidence: [source](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/final-source-suite.log),
[installed](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/installed-suite.log),
[visual/performance](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/visual-accepted/result.json),
[production GUI](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/production-ui.json),
[preservation](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/preservation-after.json),
[initial timed-out scan](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/preservation-after.log),
[extended QA replay](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-desktop-stage1/preservation-extended.log).
