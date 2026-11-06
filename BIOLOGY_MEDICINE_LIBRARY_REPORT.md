# VECTOR Biology and Medicine & Anatomy Library completion report

Completed dataset: **40 new complete references**, 20 Biology and 20 Medicine & Anatomy. All requested primary-subtopic counts are met. All **1,144 previous editions** remain preserved; the accepted/previous reference inventory is **1,184**. Stored edition records total **1,185**, including one additional retained scan that failed source-legibility review and is excluded from the target. Supporting rights files, page extractions, original streams, catalogue entries and editions are different counts.

Evidence directory: `/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-biology-medicine-expansion-20261105`. All relative artifact and recovery names in this report refer to that directory; authoritative originals also persist independently in VECTOR's existing portable data store.

## Collection and coverage

| Discipline | New stored edition records | Accepted references | Accepted original-reader verified | Accepted indexed pages |
|---|---:|---:|---:|---:|
| Biology | 20 | 20 | 20 | 4,893 |
| Medicine & Anatomy | 21 | 20 | 20 | 5,723 |

Accepted complete originals: 1,441,763,661 bytes (1.442 GB), all PDF, 10,616 physical pages. All 10,616 supplied page-text segments reached the existing importer's complete cursor; this certifies processing completion, not accurate extraction of every scientific symbol or image. Including the retained failed scan, the 41 stored originals total 1,468,069,329 bytes and 11,120 supplied indexed page segments. The additional 504 pages and original are excluded from the 40-reference target.

### Biology

- molecular biology and gene regulation: 3
- genetics and genomics: 3
- evolutionary biology and population genetics: 3
- microbiology, bacteriology, and virology: 3
- cell biology and cellular signaling: 2
- biochemistry and structural biology: 2
- developmental biology: 2
- systems biology, bioinformatics, or computational biology: 2

### Medicine & Anatomy

- gross human anatomy: 3
- human physiology: 3
- general and systemic pathology: 3
- pharmacology and pharmacodynamics: 3
- immunology and immune disorders: 2
- histology and microscopic anatomy: 2
- clinical medicine, diagnostics, and evidence-based medicine: 2
- neuroscience and neuroanatomy: 2

The collection emphasizes complete edited research references and specialist monographs alongside textbooks and professional handbooks. Complete Frontiers ebooks count once each, not once per article. They do not provide comprehensive textbook coverage of every organ, disease or technique. The FDA Bad Bug Book is accurately classified as a professional foundational handbook with an explicitly abbreviated scope. The 1900 Stöhr histology book and 1909 Sobotta Volume II are historical references; Volume II is a separately published complete volume, not the entire multivolume atlas. A previously imported 1914 Volume I scan has a severely faded PDF page 25. Independent colour and grayscale renders confirmed the problem, and all three inspected atlas files matched the official archive’s independent whole-file identities and lengths (SOURCE_SCAN_HASH_BINDINGS.json). The source-provided PDFs retain the fading; its physical-capture or processing cause is not established. Nonempty rendering did not qualify it as readable. That original and all 504 indexed pages remain in the separately labelled Reader-limited originals collection, excluded from the 40 accepted references. The replacement is a different complete volume, not an altered or reconstructed copy. Coverage remains uneven: the historical normal-histology text and modern computational pathology reference do not replace a contemporary comprehensive normal-histology textbook; the physiology selections emphasize quantitative and musculoskeletal methods, and the clinical selections emphasize imaging and epidemiology rather than current general treatment guidelines. The complete Bergtrom LibreTexts web edition is preserved, but its underlying print edition/year could not be independently established and are not invented.

## Acquisition and rights

94 distinct work/edition candidates are recorded (41 Biology; 53 Medicine & Anatomy). Exactly 40 selected editions were acquired and accepted. In total 41 scientific edition records/originals were imported: the 40 accepted references plus the retained failed scan. The grayscale diagnostic variant was staged only, not imported or counted. Rejected, pending and uncompleted-review alternatives are not counted as successful resources. The complete decision list distinguishes identified candidates from fully reviewed editions and HTTP requests.

Candidate decision counts: 40 accepted/backend-verified; 1 retained source-quality failure; 15 rejected; 18 screened but not imported; 15 pending; 4 unfinished reviews; 1 identified but not selected. Pending/unfinished records are not represented as fully rights-reviewed works.

Rights evidence is edition-specific and preserved in the existing data store with source URLs, attribution, full original notices and file hashes. Current publisher notices were not retroactively applied to older ebooks. Older Frontiers compilations that restricted resale, NC/ND editions, unresolved third-party permission-only illustrations and incomplete previews were excluded. The selected Frontiers copyright pages explicitly license the whole ebook as well as its articles under CC BY 4.0. Attribution, article creators, illustration credits and source notices remain in each complete original.

Root-licence counts: CC-BY-4.0: 35, CC-BY-3.0: 1, US-PUBLIC-DOMAIN: 2, US-GOV-PUBLIC-DOMAIN: 2. The Human Anatomy Lab Manual also contains explicitly credited public-domain, CC BY 3.0/4.0 and CC BY-SA 4.0 components. Its unchanged original and image-credit appendix are preserved; any later adaptation of an SA illustration must retain the corresponding SA terms. Aggregation does not relicense the application. U.S. public-domain findings are U.S.-scoped, including specific government-work evidence rather than assuming that every government-hosted file is unrestricted. No worldwide or neural-training permission is asserted.

Acquisition ran only in the separate Codex staging operator, with exact-host HTTPS checks, allowed access methods, bounded files, deadlines and resource limits. No authentication, paywall, robots restriction or challenge was bypassed. When an official source rejected automation, alternatives were used or the source was held. CDC material came from its separately permitted official archive, with the specific Stacks edition rights reviewed independently. Downloads were treated as data; no downloaded code, macro or PDF action was executed.

## Existing architecture and installed changes

The existing ScientificLibrary, Memory store, resource catalogue, SQLite/FTS search, source references and protected PDF renderer are reused. Only the two unambiguous collection destinations were added in `src/vector_core/resources.py`; the existing category regression in `tests/test_resource_library.py` was extended. No database schema migration, new dependency, duplicate knowledge index, model change, inference rewrite or new permission was introduced. Schema remains 8. The metadata correction that moved the new Chest/Breast/Heart/Vessels reference from pathology to clinical medicine is an explicit append-only revision; prior approval, original, index and evidence remain retained.

Tested executable-code checkpoint: `b34ef79`, installed from the local wheel. All 56 source, installed and regression-bound module hashes match. Final documentation/install checkpoint is recorded separately in `FINAL_CHECKPOINT.json`. Baseline rollback code is `677d70b`. No original books or private user records are embedded in application source or Git.

Exact repository files changed: `src/vector_core/resources.py`, `tests/test_resource_library.py`, `BIOLOGY_MEDICINE_LIBRARY_EXPANSION.md`, `BIOLOGY_MEDICINE_LIBRARY_REPORT.md`, `BIOLOGY_MEDICINE_RESOURCE_CATALOGUE.md`, `BIOLOGY_MEDICINE_RESOURCE_MANIFEST.json`, and `PROGRESS.md`. Acquisition/import/QA operators and private evidence remain in the dated workspace, outside application modules.

## Actual installed verification

The real installed Tk desktop and existing data directory were exercised for **all 40 accepted** originals: 39 retain their full initial-run evidence with identical original hashes; the replacement Volume II passed a separate actual installed run, which also checked the 20/20 category counts and visibility of the failed-scan warning/quarantine collection. Each passed title and author search, complete-PDF page count, first/page-25/last-page rendering, indexed-hit handoff to the original physical page, literal in-original search, bookmark creation, and close/reopen reading-position persistence. Embedded outlines were followed where available; an absent outline is not claimed as chapter navigation. Original rendered PNGs and per-resource results are retained. This is sampled-page testing of every original, not visual inspection of all 10,616 pages.

Previous literary and scientific originals and mathematics indexed search were also checked. Existing reading-position values were restored after the acceptance test; new test bookmarks and genuine Chat acceptance records are retained as additive evidence. The standalone Library ran with inference disabled and required no Ollama request. The independently running Ollama service was not administratively stopped, so no service-stopped claim is made.

Real Chat/AUTO generated and displayed a nonempty genuine response using qwen2.5-coder:0.5b; 1 request(s), simulated=false. No routine approval, owner override, default-model change or accuracy gate was used. This is a functionality check, not a reasoning benchmark or a fresh 2B/Both-mode qualification.

| Test scope | Passed | Skipped / unverified | Failures / errors |
|---|---:|---|---:|
| Complete native source regression, 412 tests | 411 | 1 optional cryptography roundtrip | 0 / 0 |
| Complete native installed regression, 412 tests | 411 | 1 optional cryptography roundtrip | 0 / 0 |
| Actual installed accepted-original reader acceptance | 40 | None | 0 |
| Retained 1914 Volume I scan | Excluded from successful count | Source legibility failed; original preserved | 1 identified visual-source failure |
| Original integrity and existing-data preservation | Passed | No scientific-content accuracy certification | 0 |

The optional authenticated-encryption roundtrip is unverified because that interpreter lacks the optional cryptography dependency. It is not reported as passing. Initial tests in Codex’s different process namespace were blocked by trusted-owner/isolation qualification; native Lenovo reruns passed without weakening those checks. A premature extraction launch and an operator pack-building path typo failed before any affected import; failures and corrected reruns are retained. Network/DNS/download failures and rejected range responses remain in the acquisition logs rather than being represented as complete files.

## Integrity, isolation and resources

The final post-replacement read-only comparison independently verified all 36,719 previous physical objects against their original inode/mtime/size/hash and recovery copy; all 36,721 previous raw original-content streams; all 1,288,804 literary units and their FTS structures; all previous immutable records; preferences, inference profile, data identity and Foundational Laws. All 41 newly stored original SHA-256/lengths and effective bibliographic/rights/medical metadata matched, including the excluded scan. All 40 accepted references remain separately counted. Database quick_check and foreign keys passed. No pre-existing edition was moved, deleted or replaced.

Imports retained a verified 512 MiB cgroup memory cap, zero scope swap, 32 tasks and one-CPU quota. Maximum observed import charged memory was 512.0 MiB; no observed import OOM/kill events occurred. Charged memory includes cache and can reach the enforced cap without an OOM. Renderer-scope peak was 228.3 MiB. Frontend/backend RSS high-water peaks across the reader runs were 79.3/138.9 MiB. Existing host swap is recorded separately in final-validation.json; these are not a simultaneous-memory sum and scope swap zero is not a claim that the host used no swap. All successful import scopes were removed.

Actual frontend/core IPv4, IPv6 and Unix-socket denial checks passed; protected reader controls retained network namespaces, seccomp, filesystem isolation and process/memory limits. The permitted local inference transport remains separately qualified. No VECTOR or HELIX egress, remote model source, telemetry or cloud fallback was enabled.

Final measured available filesystem space: **53.06 GB / 49.41 GiB**, above the 20 GiB reserve. Current complete data-directory file total: 5.615 GB. Managed-object storage grew by 1.293 GB and allocated database pages by 0.155 GB; those measured deltas include supporting rights, extraction and acceptance records, not just original PDFs. Staging and the retained recovery copy are separate from the new-original byte count. Slow bounded indexing and disk I/O were allowed to finish; no concurrent inference workload was used during import.

Catalogue cold refresh remains slow on this HDD. A read-only EXPLAIN of the unchanged baseline schema confirms correlated scans over external_originals.object_digest and managed_refs.digest without lookup indexes (`catalogue-query-plan.json`). This predates the expansion and scales with the growing object catalogue. Cached browsing and page rendering were tested separately; no security limit or timeout was silently relaxed. A focused future additive-index/cache improvement is recommended, with a fresh current-data backup and migration/regression tests. This expansion did not change schema to conceal the performance limitation.

## Recovery and deliverables

Preserved rollback: `before-data` is the independent original-object copy plus consistent SQLite backup; `preservation-before.json` binds its hashes; `rollback` retains the matching old wheel; `before-installed` retains baseline modules. Do not restore the old database blindly after new owner activity: recovery must first preserve the current state. No backup was deleted or overwritten.

- `RESOURCE_CATALOGUE.md`: all 40 titles, creators, publishers/institutions, editions, dates, levels, subtopics, rights basis, notices, original hashes, stored identifiers and indexing/reader status.
- `RESOURCE_MANIFEST.json`: machine-readable resource metadata and actual search/reader proofs.
- `ACQUISITION_DECISIONS.md` and `CANDIDATES.json`: per-candidate decisions and exact limitations.
- `final-validation.json`: aggregate acceptance, module hashes, controls and measurements.
- `desktop-final.json` and `desktop-replacement.json`, with their installed-reader-pages directories: actual reader outcomes and original-page PNGs; the initial failed-source visual finding remains explicit.
- `chat-auto-final/result.json` and `chat-auto-replacement/result.json`: private genuine Chat evidence before/after the corrective batch.
- `preservation-after-replacement.json`: final read-only comparison after the corrective batch; the deliberately superseded intermediate scan is retained as incomplete in AUDIT_SUPERSESSION.json and the initial queue/logs. It is not counted as passing; all checks are required in the final post-correction audit.

This completes the 20/20 dataset and installed-functionality acceptance when the above evidence is passed. It does not certify current medical recommendations, perfect scientific extraction, model learning, neural accuracy, or production release readiness.
