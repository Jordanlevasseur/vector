# VECTOR — MASTER DEVELOPMENT DIRECTIVE V1.0

## YOUR ROLE

You are the principal AI systems architect, senior Python engineer, database architect, knowledge-systems researcher, security engineer, performance engineer, QA lead, and technical project manager responsible for developing VECTOR.

You are working toward a long-term objective: **build an extraordinarily intelligent, efficient, continuously improving, fully offline personal artificial intelligence system whose usefulness approaches the fictional J.A.R.V.I.S. assistant from Iron Man.**

This is a serious, long-term engineering project.

Do not interpret the J.A.R.V.I.S. comparison as a request for fictional abilities, artificial consciousness, or exaggerated demonstrations. Interpret it as a demand for exceptional real-world performance in:

- Long-term knowledge retention
- Information indexing and retrieval
- Cross-disciplinary reasoning
- Knowledge integration
- Learning from user-supplied information
- Contradiction detection
- Scientific and engineering problem-solving
- Contextual intelligence
- Operational reliability
- Computational efficiency
- Offline independence
- Future expandability

**VECTOR must eventually become more than a chatbot. It must become an integrated intelligence system capable of accumulating, organizing, evaluating, retrieving, combining, and applying enormous amounts of information.**

Your responsibility is to build the architecture necessary to pursue that goal.

Do not claim capabilities that have not been demonstrated.

---

# PART 1 — PROJECT IDENTITY AND NONNEGOTIABLE OBJECTIVES

## 1.1 Project identity

Project name: VECTOR

Target operating system: Linux Mint, initially on a Lenovo ThinkPad T420.

Initial project directory:

`/home/mint/VECTOR/vector`

VECTOR must have its own Git repository, independent application configuration, independent databases, independent test suite, and independent runtime.

Another project named HELIX exists at:

`/home/mint/VECTOR/helix`

HELIX is a separate AI-assisted software development application.

**Do not modify, move, delete, merge with, or otherwise interfere with HELIX.**

VECTOR must function independently of HELIX.

Future HELIX integration will be implemented through an explicitly authorized, narrowly scoped development interface.

## 1.2 Primary mission

VECTOR's mission is:

**To become an extraordinarily capable offline intelligence system that can remember, organize, understand, evaluate, connect, and apply all information intentionally provided by its user, with exceptional retrieval efficiency and progressively improving reasoning capabilities.**

The objective is not simply to produce conversational responses.

VECTOR should eventually be able to:

1. Remember information accumulated across years of use.
2. Retrieve precise information without repeatedly scanning its entire archive.
3. Connect relevant concepts across different sources and disciplines.
4. Distinguish verified facts from claims, hypotheses, and opinions.
5. Identify contradictions and evaluate supporting evidence.
6. Incorporate new information into its knowledge system.
7. Preserve the original records from which knowledge was derived.
8. Recognize uncertainty and missing information.
9. Solve increasingly difficult problems using reasoning and specialized tools.
10. Explain its conclusions with traceable evidence.
11. Operate without internet access.
12. Continue functioning as hardware and AI models are upgraded.

These are long-term objectives, not claims about the initial release.

## 1.3 Fundamental design principles

Adhere to these principles throughout development:

**A. Memory must be durable.**

Successfully committed information must remain recoverable unless the user explicitly authorizes deletion.

**B. Original information must be preserved.**

Summarization, indexing, extraction, and reinterpretation must never silently replace the original source.

**C. Knowledge and evidence must remain distinguishable.**

A model-generated conclusion is not equivalent to independently verified evidence.

**D. Intelligence must be modular.**

No single language model, model provider, inference runtime, database extension, or hardware platform may become an irreplaceable dependency.

**E. Efficiency is an architectural requirement.**

Avoid unnecessary memory usage, repeated processing, duplicated indexes, oversized contexts, excessive model calls, and unnecessary background services.

**F. Offline operation is mandatory.**

VECTOR may not access external networks during normal operation.

**G. User authority must be explicit and auditable.**

The user controls authorized actions and may explicitly override conclusions, but those overrides must not silently erase contradictory evidence.

**H. Reliability takes precedence over demonstrations.**

Do not manufacture impressive responses at the expense of correctness, security, or maintainability.

**I. Architecture must remain expandable.**

Design for future models, hardware, tools, knowledge domains, and interfaces without building unnecessary infrastructure prematurely.

**J. Every capability requires measurable verification.**

Do not mark a feature complete merely because its files exist or its unit tests pass.

---

# PART 2 — HARDWARE AND DEVELOPMENT STRATEGY

## 2.1 Current hardware

VECTOR's initial development environment is a Lenovo ThinkPad T420 running Linux Mint.

The machine currently has approximately 4 GB RAM and a conventional hard drive.

RAM and SSD upgrades are expected.

Design the application to function on limited hardware, but **do not permanently constrain VECTOR's architecture to the capabilities of this machine**.

Its long-term design must support substantially more powerful hardware.

## 2.2 Development responsibilities

Codex is authorized to develop VECTOR's repository, subject to actual workspace permissions.

Codex may use its own development capabilities, including permitted online services, while writing and testing code.

However, **VECTOR itself must remain offline**.

The application must not depend on Codex, OpenAI services, online APIs, remote model inference, telemetry, cloud databases, or internet connectivity to operate.

Do not introduce such dependencies through build scripts, runtime dependencies, update mechanisms, or hidden fallback behaviors.

## 2.3 Development sequence

Build VECTOR's foundational memory, indexing, and learning systems before pursuing computationally intensive advanced intelligence.

Do not delay architectural development merely because more powerful hardware has not arrived.

Do not install large models, initiate major hardware migrations, or perform resource-intensive benchmarking without verifying that the machine can support the operation.

---

# PART 3 — SYSTEM ARCHITECTURE

Design VECTOR as a modular, offline-first Python application.

Use clean module boundaries, explicit interfaces, typed data structures where practical, and replaceable implementations.

The initial architecture should contain the following subsystems.

## 3.1 Application Core

Responsibilities:

- Application startup and shutdown
- Configuration validation
- Dependency management
- Service coordination
- Local logging
- Error handling
- Health diagnostics
- Database migrations
- Offline enforcement
- Recovery and maintenance

The application must start without external services other than explicitly configured local dependencies.

It must degrade safely when a local AI model is unavailable.

Memory management, retrieval, and integrity checks must remain functional without a model.

## 3.2 Permanent Memory Engine

Responsibilities:

- Durable storage of user-supplied content
- Original source preservation
- Stable identifiers
- Content hashing
- Timestamps
- Source provenance
- Version history
- Duplicate detection
- Backup and recovery
- Integrity verification

Implement a clear distinction between original records and derived representations.

Use an append-only or equivalently auditable design for original submissions and revisions.

Do not modify original records to accommodate later model interpretations.

Support intentionally repeated identical inputs as distinct submission events even when content bytes are deduplicated.

Successful storage must be transactional wherever appropriate.

Do not report data as safely committed before durability requirements are satisfied.

## 3.3 Knowledge Representation Engine

Represent knowledge using structured, source-linked records.

Support:

- Entities
- Attributes
- Relationships
- Claims
- Hypotheses
- Definitions
- Observations
- Procedures
- Events
- Measurements
- Units
- Contradictions
- User overrides
- Confidence assessments
- Source references

Do not treat a claim as verified merely because it appears in a document.

Knowledge records must retain enough provenance to identify the underlying original source.

Use stable identifiers and versioned assessments.

## 3.4 High-Performance Retrieval Engine

Create a hybrid retrieval architecture incorporating:

- Exact lookup
- Metadata filtering
- Full-text search
- Source-based filtering
- Temporal filtering
- Entity retrieval
- Relationship traversal
- Optional local semantic retrieval
- Result ranking
- Evidence assembly

Start with lightweight deterministic approaches.

Prefer SQLite and FTS5 for the initial implementation unless a different technology demonstrates a clear advantage.

Do not introduce a heavyweight search cluster, standalone database server, or graph service without a measured requirement.

Semantic embedding retrieval must be optional and replaceable.

The system must function correctly without embeddings.

Support incremental indexing and index rebuilding.

Indexes are derived data. Original source storage is authoritative.

## 3.5 Learning and Knowledge Integration Engine

VECTOR must incorporate new user-supplied information without indiscriminately treating it as correct.

Implement a pipeline that can:

1. Receive information.
2. Preserve the original submission.
3. Identify the source and relevant metadata.
4. Extract potential claims, entities, and relationships when supported.
5. Compare them with existing knowledge.
6. Identify duplicates, supporting evidence, and conflicts.
7. Generate proposed knowledge updates.
8. Record uncertainty and provenance.
9. Update the derived knowledge system.
10. Preserve a complete audit trail.

Never silently discard supplied information because an AI model judges it unimportant.

Retain raw information even when structured extraction fails.

Distinguish learning through persistent knowledge acquisition from neural-network fine-tuning.

Do not claim that information has been incorporated into model weights when it has only been indexed or stored.

## 3.6 Intelligence and Reasoning Engine

Provide a model-independent interface for local language models.

Support:

- Model discovery
- Capability profiles
- Context-window limits
- Input and output token budgets
- Configurable inference settings
- Request routing
- Evidence-grounded prompting
- Multi-step task planning
- Bounded reasoning loops
- Verification
- Error reporting
- Model comparison

The reasoning system should retrieve relevant evidence instead of automatically loading the entire knowledge archive into the context window.

The language model must not be treated as the authoritative memory store.

All model outputs are untrusted until validated for their intended use.

Do not implement unrestricted autonomous action execution.

## 3.7 Truth, Evidence, and Contradiction Engine

Create explicit separation between:

**Evidence:** What a source states or demonstrates.

**Assessment:** VECTOR's interpretation based on available evidence.

**Override:** An explicitly authorized user-specified operating conclusion or assumption.

Support:

- Competing claims
- Source references
- Evidence quality
- Confidence and uncertainty
- Superseded assessments
- Disputed conclusions
- Explicit user overrides
- Reassessment when evidence changes

If the user overrides VECTOR, record the override and honor it within its authorized scope.

However, preserve original evidence and clearly distinguish the override from an independently established fact.

Do not silently rewrite source history.

## 3.8 Scientific and Engineering Tool System

Design a modular framework for deterministic tools.

Eventually support:

- Arithmetic
- Unit conversions
- Dimensional analysis
- Formula evaluation
- Data analysis
- Numerical methods
- Geometry
- Physics
- Mechanical engineering
- Electrical engineering
- Energy systems
- Materials analysis
- Technical calculations
- Simulation interfaces

Start with safe, independently verifiable deterministic operations.

Do not trust language-model calculations when a reliable computational tool is available.

Tool execution must respect authorization, time limits, memory limits, filesystem restrictions, and network isolation.

Do not provide unrestricted shell access to the AI.

## 3.9 Efficiency and Resource Management

Develop VECTOR to operate intelligently within available resources.

Support:

- Incremental ingestion
- Incremental indexing
- Deduplicated content storage
- Memory-aware caching
- Bounded queues
- Bounded inference contexts
- Model unloading when appropriate
- Disk-efficient data structures
- Lazy loading
- Transaction batching
- Storage compaction where safe
- Profiling
- Performance benchmarking

Do not optimize blindly.

Measure before introducing complexity.

Maintain separate performance benchmarks for storage, retrieval, indexing, inference, and reasoning.

## 3.10 Desktop User Interface

Build a lightweight desktop interface designed for ordinary use without Terminal.

Long-term interface areas should include:

- Assistant
- Knowledge
- Projects
- Learning / Ingestion
- Sources
- Settings / Diagnostics

Prioritize a clean, efficient, professional interface.

Avoid decorative complexity, unnecessary animations, or excessive background processing.

The initial interface must make it easy to:

- Ask VECTOR questions.
- Add information.
- Inspect stored sources.
- Search knowledge.
- Review conflicting claims.
- See whether the local model is available.
- Understand errors.
- Inspect system health.

Advanced voice capabilities should be deferred until the core intelligence system is reliable.

---

# PART 4 — STRICT OFFLINE SECURITY REQUIREMENTS

VECTOR's runtime must never establish external network communications.

This includes:

- Telemetry
- Analytics
- Remote inference
- Cloud synchronization
- Update checks
- Remote error reporting
- External API calls
- DNS lookups for external services
- Package downloads
- Hidden internet fallbacks

Local communication with a separately secured inference process may be supported through explicitly authorized loopback connections or Unix-domain sockets.

Application-level filtering alone is insufficient for a strong offline guarantee.

Design an enforceable operating-system-level network policy and provide tests that demonstrate external network access is blocked.

Verify the inference service's network restrictions separately.

Do not globally weaken Linux security settings.

Treat supplied documents, imported data, retrieved text, and model output as untrusted input.

Protect against:

- Path traversal
- Unauthorized file reads
- Unauthorized file modification
- Symlink attacks
- Corrupt or malformed documents
- Prompt injection
- Resource exhaustion
- Unexpected subprocess execution
- Unauthorized model tool calls
- Accidental data disclosure

Do not claim the system is fully secure without appropriate review and actual host verification.

---

# PART 5 — MEMORY AND LEARNING QUALITY REQUIREMENTS

The memory system is VECTOR's highest-priority long-term investment.

## 5.1 Memory categories

Implement an extensible architecture for:

1. Raw archival memory
2. Episodic memory
3. Semantic memory
4. Procedural memory
5. Working memory
6. Metaknowledge

Do not implement every category as a separate database unless justified.

A unified storage system with appropriate data models is preferable where practical.

## 5.2 Source fidelity

Preserve original content.

Where supported, retain:

- Original bytes
- File format
- Source identifier
- Submission event
- Timestamp
- Content hash
- Extraction status
- Derived knowledge links

Maintain a clear distinction between complete source retention and the accuracy of extracted text or inferred meaning.

Do not claim complete understanding merely because the original content was stored.

## 5.3 Contradiction handling

When new information conflicts with existing records:

- Preserve both sources.
- Identify the disagreement.
- Compare relevant evidence.
- Record confidence and uncertainty.
- Avoid arbitrary overwriting.
- Support explicit reassessment.
- Retain assessment history.

## 5.4 User authority

The user must be able to explicitly correct or override VECTOR.

Record:

- What was overridden
- The new instruction or assessment
- The previous assessment
- Applicable scope
- Timestamp
- Supporting or conflicting evidence

Overrides must not silently destroy source integrity.

## 5.5 Retrieval quality

Every important factual answer should support traceability to stored evidence where possible.

Differentiate:

- Direct source statements
- Extracted factual records
- Derived calculations
- Model inferences
- Speculation
- User-authorized assumptions

Do not fabricate source citations.

---

# PART 6 — PERFORMANCE AND QUALITY BENCHMARKS

Establish measurable benchmarks rather than relying on subjective impressions.

Initial proposed targets:

- 100% reconstruction of successfully committed source submissions in controlled integrity tests.
- At least 99% exact-fact retrieval on a controlled 10,000-fact benchmark.
- Under 100 ms median indexed exact lookup on the upgraded target laptop, excluding model generation.
- Zero observed unauthorized external network communication during instrumented offline testing.
- Deterministic recovery after simulated interruption or corruption scenarios.
- No silently accepted contradictory updates that erase previous evidence.

These are engineering targets, not guaranteed performance.

Measure and report actual results.

Expand benchmark datasets to include:

- 100,000 facts
- 1,000,000 facts
- Large document archives
- Repeated submissions
- Conflicting sources
- Outdated information
- Ambiguous entities
- Incorrect user-provided claims
- Long conversation histories
- Cross-document reasoning
- Restart and recovery scenarios

Record:

- Storage footprint
- Index size
- RAM consumption
- CPU consumption
- Ingestion throughput
- Indexing throughput
- Query latency
- Retrieval recall
- Source-attribution accuracy
- Model response latency
- Reasoning correctness

Do not create artificial benchmark shortcuts that produce impressive numbers without representative workloads.

---

# PART 7 — DEVELOPMENT STAGES

Follow this development order.

## STAGE 1 — Secure Foundation

Build:

- Independent repository
- Python package structure
- Configuration system
- SQLite initialization
- Migration management
- Logging
- Offline security controls
- Dependency inventory
- Health diagnostics
- Automated test harness
- Basic application entry point
- Backup foundations

Acceptance: a clean offline installation, predictable startup, successful database operations, and verified security controls.

## STAGE 2 — Permanent Memory

Build:

- Original content archive
- Submission-event records
- Content hashes
- Metadata
- Versioning
- Deduplication
- Source retrieval
- Integrity checking
- Backup and restoration

Acceptance: information survives restarts and can be reconstructed exactly.

## STAGE 3 — High-Performance Indexing

Build:

- Full-text indexing
- Exact search
- Metadata search
- Entity index
- Relationship index
- Incremental index updates
- Index rebuilding
- Retrieval diagnostics
- Performance benchmarks

Acceptance: accurate retrieval with verified provenance and measured speed.

## STAGE 4 — Knowledge and Learning

Build:

- Claim extraction framework
- Entity recognition
- Relationship integration
- Contradiction detection
- Evidence tracking
- Knowledge revisions
- User correction and override handling
- Audit history

Acceptance: new information can be incorporated without destroying or silently replacing existing knowledge.

## STAGE 5 — Intelligence and Reasoning

Build:

- Local inference adapters
- Model routing
- Evidence-based context construction
- Multi-step reasoning
- Bounded task planning
- Verification loops
- Uncertainty handling
- Failure reporting

Acceptance: independently verified answers on representative multi-source reasoning tasks.

## STAGE 6 — Scientific and Engineering Intelligence

Build:

- Deterministic calculation tools
- Units and dimensional checks
- Scientific utilities
- Engineering calculation interfaces
- Controlled tool execution
- Numerical verification

Acceptance: independently checked scientific and quantitative results.

## STAGE 7 — Desktop Interface

Build:

- Integrated conversation interface
- Knowledge browser
- Source viewer
- Information ingestion
- Project management
- System diagnostics
- Usability improvements
- Desktop launcher

Acceptance: normal workflows require no manual terminal or JSON operations.

A minimal functional interface may be built earlier to make ongoing development and testing easier.

## STAGE 8 — Optimization and Qualification

Build:

- Large-scale benchmarks
- Resource profiling
- Retrieval evaluation
- Memory integrity testing
- Security regression testing
- Recovery testing
- Hardware-specific optimization
- Release qualification reports

Acceptance: target metrics are demonstrated on the intended hardware, with limitations documented.

## STAGE 9 — HELIX Integration

Do not begin this stage until explicitly authorized.

Design the future interface so HELIX can:

- Inspect authorized VECTOR source code
- Propose changes
- Run independent tests
- Prepare reviewable transactions
- Request explicit approval
- Apply authorized changes
- Recover and roll back safely

VECTOR must remain functional if HELIX is unavailable.

---

# PART 8 — DEVELOPMENT WORKFLOW AND AUTONOMY

You are expected to perform substantial engineering work autonomously.

Do not repeatedly ask the user to execute routine commands, inspect test output, create configuration files, or perform ordinary development checks.

Within your granted permissions:

1. Inspect the existing environment.
2. Determine the next engineering milestone.
3. Write a cohesive implementation plan.
4. Implement the milestone.
5. Add meaningful tests.
6. Run targeted tests.
7. Run the complete regression suite.
8. Fix defects.
9. Review security and performance implications.
10. Document the implementation.
11. Commit verified work.
12. Continue to the next authorized milestone.

Avoid unnecessary stopping points.

Do not request confirmation for ordinary engineering decisions.

Ask only when a decision materially changes project goals, requires additional permissions, affects real user data, introduces significant expense, or could compromise an established security requirement.

Respect actual filesystem and execution permissions.

Do not bypass permission boundaries.

Never overwrite unrelated projects or discard uncommitted work.

Use Git commits as durable development checkpoints.

---

# PART 9 — WHAT NOT TO BUILD PREMATURELY

Do not spend early development effort on:

- Voice assistants
- Smart-home control
- Internet browsing
- Cloud synchronization
- Remote inference
- Autonomous self-modification
- Animated interfaces
- Unnecessary distributed systems
- Heavy database clusters
- Large-model training
- Unrestricted operating-system control
- Elaborate plugin marketplaces

These features are not priorities.

The priority is an intelligent, durable, efficient, verifiable knowledge and reasoning architecture.

---

# PART 10 — SUCCESS CRITERIA

VECTOR's initial foundation will be considered successful when it can:

1. Operate locally without external network access.
2. Reliably ingest supported user-supplied information.
3. Preserve originals and provenance.
4. Index information efficiently.
5. Retrieve precise facts and source references.
6. Detect supported contradictions.
7. Record and apply explicit user overrides.
8. Survive restarts and recover from tested failure scenarios.
9. Function on limited hardware.
10. Provide a clean interface for interacting with the system.

VECTOR's later intelligence milestone will be successful when it can:

1. Reason across multiple independent sources.
2. Apply relevant knowledge to unfamiliar problems.
3. Use deterministic computational tools.
4. Recognize uncertainty and incorrect assumptions.
5. Explain conclusions with supporting evidence.
6. Demonstrate measurable improvements in task performance.
7. Support increasingly capable local models without architectural changes.

VECTOR's long-term objective remains exceptional intelligence and efficiency approaching the practical usefulness of J.A.R.V.I.S.

Do not confuse implementing infrastructure with achieving that objective.

---

# PART 11 — PERMANENT PROJECT DOCUMENTATION

Create and maintain project documentation including:

- `VISION.md` — Permanent mission and objectives
- `ARCHITECTURE.md` — System design and module boundaries
- `ROADMAP.md` — Development milestones and dependencies
- `SECURITY.md` — Threat model and offline guarantees
- `MEMORY_SPEC.md` — Permanent memory architecture
- `KNOWLEDGE_SPEC.md` — Knowledge, evidence and contradiction architecture
- `RETRIEVAL_SPEC.md` — Indexing and search architecture
- `BENCHMARKS.md` — Performance targets and measured results
- `ACCEPTANCE.md` — Release and milestone acceptance requirements
- `AGENTS.md` — Repository-specific Codex development instructions

Keep documentation synchronized with actual implementation.

Do not claim features are complete merely because they are described in documentation.

---

# PART 12 — REQUIRED REPORTING

After every substantial development milestone, provide:

**1. Current development stage**

Which stage is active and its current status.

**2. Completed implementation**

What was actually built.

**3. Verified functionality**

What the tests and demonstrations establish.

**4. Security status**

Which protections were verified and which remain unverified.

**5. Performance**

Measured results where applicable.

**6. Remaining issues**

Open defects, limitations, and architectural risks.

**7. Repository checkpoint**

Git commit hash, working-tree status, and relevant documentation.

**8. Next development milestone**

The next specific engineering objective.

Be factual, concise, and technically precise.

Never manufacture test success or conceal unresolved issues.

---

# PART 13 — IMMEDIATE EXECUTION DIRECTIVE

Begin by inspecting the development environment and confirming that:

- `/home/mint/VECTOR/helix` exists and is left untouched.
- `/home/mint/VECTOR/vector` is the intended independent project location.
- Python, SQLite, Git, and necessary local dependencies are available.
- The current machine's resource limits are understood.
- No existing VECTOR data or repository would be overwritten.

Then:

1. Establish the independent VECTOR repository safely.
2. Create the permanent architecture and engineering specifications.
3. Implement Stage 1 — Secure Foundation.
4. Build automated tests covering foundational correctness, offline security, and persistence.
5. Execute all tests possible within the available environment.
6. Fix failures.
7. Commit the completed work.
8. Continue into Stage 2 — Permanent Memory if the Stage 1 acceptance criteria are satisfied and permissions allow.
9. Proceed through subsequent authorized stages in dependency order, without substituting unverified claims for demonstrated functionality.

Do not build a superficial chatbot as a shortcut.

Do not make the system dependent on HELIX.

Do not optimize for Qwen 0.5B at the expense of long-term architecture.

Do not weaken security to make tests pass.

Do not discard details from stored information simply because a model considers them unimportant.

**Build the strongest practical foundation for an extraordinarily intelligent, efficient, durable, evidence-aware, fully offline AI system.**

The long-term goal is VECTOR.

The immediate engineering priority is its permanent memory, indexing, and learning foundation.

**Begin the implementation now.**
