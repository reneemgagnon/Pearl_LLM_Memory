# PEARL-CHAT

**PEARL**: Protected · Evolving · Annotation · Resistant · Layering

An open temporal context format and reference toolkit for agentic memory.

## What PEARL Is

PEARL-CHAT (`.pearl`) is a JSON-based file format for storing structured,
layered, verifiable context that persists across agent sessions. It gives
autonomous agents a durable memory with immutable history, temperature-graded
recall, cryptographic chain of custody, and branching decision trails.

The format is agent-agnostic. The reference implementation is a zero-dependency
Python CLI. Both are open.

## Why It Exists

Autonomous agents — coding agents, research agents, orchestration frameworks —
lose context between sessions. When they do retain state, it is typically
opaque, unverifiable, and locked to a single vendor.

PEARL addresses this by defining a portable, auditable memory container that
any agent runtime can read and write. The goal is interoperable agentic memory:
one format, many runtimes, verifiable history.

**Compatibility targets:** Claude Code, OpenAI Codex, OpenClaw, NemoClaw /
OpenShell, LangChain, CrewAI, and any system that can read JSON.

## Core Design Goals

- **Immutable core.** The seed context is hash-locked at creation and never mutated.
- **Append-only layers.** New information is added as layers; prior layers are never rewritten.
- **Temperature model.** Hot (working set), warm (recent), cold (compacted archive), core (immutable seed).
- **Cryptographic lineage.** Every layer carries a JCS-RFC8785 canonical hash; chain hashes link layers into a verifiable sequence.
- **Branching and merging.** Explore alternatives on branches; merge with explicit accept/reject tracking.
- **Evidence refs.** Each layer can cite files, tool outputs, diffs, and test results.
- **Plain JSON.** No special parser required. Any tool that reads JSON can read a `.pearl` file.

## Key Features (v0.2)

- Core immutability enforced at the engine level (hash-guarded)
- JCS-RFC8785 canonical JSON for deterministic, verifiable hashing
- Explicit chain derivation: `SHA256(prior_chain_hash | layer_hash)`
- Layer phases: audit, design, refactor, verification, handoff, and more
- Evidence refs: file paths, tool runs, diffs, test outputs per layer
- Unseal: promote cold layers back to hot with full audit trail
- Single active branch: switching suspends prior automatically
- Accept/reject tracking on merge synthesis
- Capsule compression: zlib+base64 for large cold archives
- Operational briefs: `current_understanding` as a working summary

## Conceptual Model

```
core        — the immutable seed (objective, constraints, facts)
layers      — what was discovered, decided, or produced
surface     — current working understanding (hot/warm/cold bands)
branches    — parallel lines of exploration
capsules    — compressed snapshots of prior state
lineage     — cryptographic continuity across all state transitions
```

A model loads context in priority order: core, hot layers, warm layers,
current understanding, active branch head, then selected cold layers as needed.

## Example Use Cases

- **Coding agent memory.** A refactoring session persists decisions, tool
  results, and verification outcomes across multiple agent invocations.
- **Multi-agent handoff.** Agent A writes observations and decisions to a
  `.pearl` file; Agent B loads it and continues with full context.
- **Audit trail.** Every layer is hash-chained. A compliance reviewer can
  verify that no prior state was silently altered.
- **Long-running workflows.** A research or investigation task that spans
  days compacts warm context to cold, unseals when needed, and branches
  to explore alternatives.
- **Secure sandboxed agents.** Agents running inside NemoClaw / OpenShell
  use `.pearl` files scoped to the sandbox filesystem policy for persistent,
  verifiable memory.

## Installation & Integration

This repository can be used as a standalone toolkit, embedded library, or
skill/integration for agent runtimes.

### Standalone CLI

```bash
python scripts/pearl_session.py init --objective "Refactor auth module"
python scripts/pearl_session.py add-layer -k observation -s "Found 3 circular imports"
python scripts/pearl_session.py surface
```

### As an agent skill (example paths)

```
# Claude Code skills directory
~/.claude/skills/pearl-context/

# Or any agent runtime that supports skill directories
<agent-skills-dir>/pearl-context/
```

### Requirements

- Python 3.10+ (stdlib only: json, hashlib, uuid, zlib, base64, argparse)
- Zero external dependencies

## Repository Layout

```
references/             Format specification and schema (CC BY 4.0)
  pearl-chat-spec.md      PEARL-CHAT format specification
  pearl-chat-schema.json  JSON Schema for .pearl file validation
scripts/                Reference implementation (Apache-2.0)
  pearl_session.py        Session engine CLI
agents/                 Agent integration configs (Apache-2.0)
assets/                 Logo, gitignore template
SKILL.md                Skill definition for agent runtimes
```

## Licensing

This project uses a three-layer licensing structure:

| Layer | Scope | License |
|-------|-------|---------|
| Format specification & docs | [`references/*`](references/) | [CC BY 4.0](LICENSE.docs) |
| Reference implementation | [`scripts/*`](scripts/), [`agents/*`](agents/), [`SKILL.md`](SKILL.md) | [Apache-2.0](LICENSE) |
| Enterprise platform | Orchestration, compliance, control plane, admin UI | Proprietary EULA |

The `.pearl` format is open. The reference tools are open. Enterprise
orchestration, compliance workflow, appliance, and control-plane offerings
by Maple Brain Healthcare Inc. are proprietary.

See [`LICENSING.md`](LICENSING.md) for full details and [`NOTICE`](NOTICE)
for attribution.

## Trademark Notice

PEARL™ is a trademark of Maple Brain Healthcare Inc.

The `.pearl` file extension and "PEARL-CHAT" format identifier may be used
freely to describe genuine compatibility with the published specification.
Controlled marks — including PEARL™ Enterprise, PEARL™ Certified, and
PEARL™ Appliance — are reserved and require written permission.

See [`TRADEMARKS.md`](TRADEMARKS.md) for the full trademark policy.

## Security

The PEARL format includes cryptographic hash chains (JCS-RFC8785 + SHA-256)
for tamper detection and core-immutability enforcement. These provide
integrity verification, not encryption. Sensitive data should be protected
at the storage and transport layer, not inside the `.pearl` file itself.

If you discover a security issue, please report it to Maple Brain
Healthcare Inc. rather than filing a public issue.

## Contributing

Contributions to the open specification and reference implementation are
welcome. By submitting a contribution you agree that it will be licensed
under the applicable layer license (CC BY 4.0 for spec/docs, Apache-2.0
for code).

Please open an issue to discuss significant changes before submitting a
pull request.
