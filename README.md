# PEARL(TM)-LLM Memory

**PEARL** = Protected - Evolving - Annotation - Resistant - Layering

PEARL is an open, JSON-native temporal context format for agent memory. It is
designed for coding agents, research agents, orchestration runtimes, and other
systems that need durable, inspectable session state instead of opaque vendor
memory.

This repository is the v0.2 reference path. The docs, schema, tests, and CLI
all target PEARL-CHAT v0.2.

## What v0.2 Means

PEARL-CHAT v0.2 standardizes the behavior implemented by the reference CLI:

- Immutable `core`, guarded by `_core_hash`
- Append-only `layers`
- Canonical JCS-RFC8785 hashing
- Explicit `chain_hash = SHA256(prior_chain_hash | layer_hash)`
- `surface` as the fully materialized working state
- Hot, warm, and cold temperature bands
- Single active branch enforcement
- Explicit branch merge outcomes with accept/reject tracking
- Cold-to-hot unsealing with audit traceability
- A stronger `verify` command that checks structural and lineage integrity

## Why PEARL Exists

Most agent systems lose context between runs or keep it in a format that is hard
to inspect, validate, reuse, or migrate. PEARL provides a portable envelope that
any runtime can read because it is still just JSON, while preserving the history
and evidence that agents actually need.

The goal is interoperable agentic memory:

- One durable file format
- Many compatible runtimes
- Verifiable lineage instead of trust-me state

## Core v0.2 Invariants

The reference implementation and docs assume these invariants:

1. `core` does not change after initialization.
2. `_core_hash` matches the canonical hash of `core`.
3. `layers` are append-only.
4. Every layer has a deterministic `layer_hash`.
5. Every non-genesis layer has a `chain_hash` derived from the prior chain hash.
6. `lineage.current_layer_id` and `lineage.chain_hash` point to the latest layer.
7. `surface.active_branch_id` points to exactly one active branch.
8. Every branch `head_layer_id` matches the final element in its `layer_ids`.
9. Temperature bands only reference layers that exist and match that temperature.

## Quick Start

Install folder into Coder /agent SKILL directory as normal. 

In new Agent session invoke with "Start a new PEARL-CONTEXT for this session " to create a new pearl. Afterwards you can ask "load prior PEARL and load ________(topic)". 

As CLI for agents 

Initialize a new PEARL session:

```bash
python scripts/pearl_session.py init --objective "Refactor auth module"
```

Add evidence-backed working memory:

```bash
python scripts/pearl_session.py add-layer ^
  --kind observation ^
  --phase audit ^
  --summary "Found three circular imports" ^
  --evidence "src/auth/manager.py|grep:circular"
```

Inspect the current surface:

```bash
python scripts/pearl_session.py surface
python scripts/pearl_session.py load-context --token-budget 4000 --format text
```

Verify the archive:

```bash
python scripts/pearl_session.py verify
```

The CLI accepts `--file` either before or after the subcommand:

```bash
python scripts/pearl_session.py --file .pearl-context/session.pearl surface
python scripts/pearl_session.py surface --file .pearl-context/session.pearl
```

## Session Selection Rules

The most common source of PEARL drift is mixing unrelated work into the same
archive. Use this rule set consistently:

- Reuse the current session when the task is the same objective and you are
  continuing the same line of work.
- Branch when the task is still the same objective but you are testing an
  alternative interpretation, design, or implementation path.
- Initialize a new session or use a different `--file` when the objective is
  materially different from the existing archive.

In practice, inspect `.pearl-context/session.pearl` first, then decide whether
to continue, branch, or start a new file.

## What `verify` Checks in v0.2

The v0.2 verifier is stronger than the minimal v0.1 checks. It validates:

- Core hash integrity
- Layer hash integrity
- Chain hash continuity
- `prior_layer_id` and `prior_chain_hash` continuity
- `lineage.current_layer_id`, `lineage.chain_hash`, and `lineage.depth`
- `surface.state_hash`
- Temperature-band references
- Active-branch consistency
- Branch head and branch layer references
- Layer-to-branch references

## Temperature Model

- `hot`: immediate working set
- `warm`: recent but not primary
- `cold`: compacted or revisited prior context
- `core`: immutable seed, stored outside temperature bands

Compaction moves warm context inward. Unsealing promotes selected cold context
back to hot and records that action as a new layer.

## Branching Model

- `main` is the default root branch created at initialization.
- Only one branch should be `active` at a time.
- Creating a branch records a `branch_event`.
- Merging records a synthesis layer and can mark branches as accepted or rejected.
- Switching to another active branch suspends the prior active branch.

## Repository Layout

```text
references/
  pearl-chat-spec.md
  pearl-chat-schema.json
scripts/
  pearl_session.py
tests/
  test_pearl_session_phase1.py
agents/
assets/
SKILL.md
```

## Development and Tests

The reference implementation is a zero-dependency Python CLI. The regression
tests exercise the CLI as an end user would.

Run the test suite:

```bash
py -3.11 -m unittest discover -s tests -v
```

## Compatibility

PEARL-CHAT v0.2 may read legacy 0.1-era archives in limited cases, but the
reference docs, schema, and validation path in this repository are now centered
on v0.2 artifacts.

## Licensing

This project uses a three-layer licensing structure:

| Layer | Scope | License |
|-------|-------|---------|
| Format specification and docs | `references/*` | CC BY 4.0 |
| Reference implementation | `scripts/*`, `agents/*`, `SKILL.md` | Apache-2.0 |
| Enterprise platform | Orchestration, compliance, control plane, admin UI | Proprietary EULA |

See `LICENSING.md`, `LICENSE`, `LICENSE.docs`, and `NOTICE` for details.

## Trademark Notice

PEARL(TM) is a trademark of Maple Brain Healthcare Inc.

The `.pearl` file extension and `PEARL-CHAT` format identifier may be used to
describe genuine compatibility with the published specification. Controlled
marks such as `PEARL(TM) Enterprise`, `PEARL(TM) Certified`, and
`PEARL(TM) Appliance` remain reserved.
