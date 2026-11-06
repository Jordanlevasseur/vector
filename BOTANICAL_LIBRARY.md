# Botanical Library: source-attested research, not clinical certification

The existing Library now includes **Botanical research**. It opens without a model,
uses the existing dark/cyan native desktop, and retains Home/Chat, Projects and
History. Originals and photographs open through the existing local protected reader;
there is no browser, new service, image downloader, dependency or separate database.

## Authoritative state and preservation

Additive SQLite migration9 registers `botanical_records` and `botanical_batches` in
VECTOR's existing append-only persistent store. Two record lookup indexes and two
previously missing original-object lookup indexes are additive. Existing source
bytes, scientific/literary indexes and edition records are not rewritten.

`vector_core.botany.Botany` lists bounded pages, searches literal names/synonyms and
metadata, exposes source citations and geographic filters, publishes reviewed local
manifests, and rolls back publication without deleting originals or history.
Portable snapshot validation verifies complete manifest hashes/counts, active
references and exact original citation bytes before activation. A newer rolled-back
version reveals an earlier active version. Rollback that would strand active dependent
records is rejected; roll back dependent batches first.

Asset intake precedes publication: it is recoverable staging, not a nested atomic
SQL transaction. A crash may leave preserved, inactive originals. Final publication
of 1–1000 records is one transaction. Restart reuses the exact pack/assets; a changed
or rolled-back batch identity cannot silently reactivate or reimport. There is no
1000-record limit on total collection size. Larger collections use reviewed slices.

## Domain records

* Taxa: source-specific accepted name, authorship, rank, kingdom (including fungi),
  family/genus, typed regional/common/Chinese/traditional names and synonyms.
  Ambiguous genus/aggregate names are not automatically assigned a species.
* Evidence: each claim has one of the eight requested evidence categories, exact
  citations, subject identity/type, part/preparation/route/dose/population/condition,
  traditional/cultural context and mechanism status. Missing fields remain null.
  Domains include identification, habitat, season, food/parts/preparation, nutrition,
  clinical/traditional uses, mechanisms, toxicity, contraindications, interactions,
  pregnancy/breastfeeding/children, lookalikes and conventional comparisons.
* Distributions: explicit country/province/city/climate/habitat/elevation/season,
  origin, occurrence status, wild/outdoor/greenhouse/purchased availability and scope.
  Country or provincial records cannot verify a site. Irregular, excluded and
  unknown states are retained; a missing result is not evidence of absence.
* Formulas, practices, preparations and isolated compounds are distinct entities.
  Formula ingredients may remain unresolved labels; effects are never automatically
  transferred between formulas, ingredients, isolated chemicals or preparations.
* Images/documents reference existing event identities and SHA-256, not arbitrary
  paths. Creator, licence, attribution, modifications and identification provenance
  are retained. A contributor's taxon label is not independent specimen verification.
* Source registry: asset/edition-specific status, licence/version, exact rights
  evidence, commercial/modification/indexing findings, US jurisdiction, third-party
  exclusions, transformations and cultural permissions. A copyright grant cannot
  resolve restricted cultural permissions. Training requires separate review.

## Research and preferences

NATURAL-FIRST is the default, alongside BALANCED and CONVENTIONAL-FIRST. These
change exploration/display order only. Safety, negative/conflicting findings and
conventional comparisons remain visible and mandatory in research context. Selecting
an individual favourable record resolves to its subject's full safety context. If
essential evidence exceeds a qualified model's context, the source view remains
available and synthesis reports that exact limitation; evidence is not silently cut.
The fixed importer refuses food/self-treatment claims for taxa whose owner-defined
research scope is identification and safety only. Original historical documents are
retained as historical references, not modern preparations or clinical instructions.

The desktop offers cited evidence without inference and an explicit local-AI research
operation using the existing adapter, AUTO/model selection, strict answer JSON and
exact original SHA/span/quote validator. Inference remains unverified interpretation;
valid citations do not establish medical accuracy. Ordinary Chat is unchanged and
"Hi" does not trigger botanical retrieval. No autonomous clinical tool orchestration,
photo identification or clinical recommendation system is claimed.

## Local import boundary

`tools/botanical_import.py --data-dir ... --pack ... --review-sha256 ...` runs under
the existing kernel network-denial policy. A pack contains `manifest.json` and fixed
`objects/<sha256>` files. The manifest binds assets, records, source-specific approved
rights and a stable batch ID. Review SHA is the hash of the exact manifest file.
The importer accepts no URLs to fetch, scripts to execute, model permission tokens,
or arbitrary output paths. Symlinks, traversal, changed assets, incompatible licences,
missing sources, forged citations and inconsistent entity types fail closed.

The application dispatcher exposes bounded `botany_list`, `botany_detail`,
`botany_counts`, `botany_preferences_get/set` and `botany_research` operations.
Publication/import/rollback are trusted local maintenance APIs, never model tools.
Botanical source derivatives carry original hashes and locators through existing
full-text search. Unpublished/rolled-back botanical sources are excluded from AI
retrieval; preserved originals remain available for inspection.

## Scope of initial content

The installed-content and acceptance report is authoritative for actual counts.
Taxonomic/checklist records must not be counted as medically researched profiles;
source records, photographs, derived texts and complete editions are separate counts.
VASCAN is a Canadian regional checklist and explicitly disclaims universal taxonomic
or legal authority. USDA names do not prove local occurrence. Classical Chinese
transcriptions may contain unproofread or obsolete material, toxic substances and
historical units; no modern dose conversion or clinical endorsement is supplied.

No source is approved merely because NIH, GBIF, WHO, a government site, university,
Commons or another registry hosts it. NIH purchased photographs and unqualified
third-party assets are excluded. Conditional CC BY-SA texts retain attribution,
source revisions, modification notices and their licence; they do not become
unrestricted content or change VECTOR's software licence.
