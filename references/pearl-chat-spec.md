<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2025-2026 Maple Brain Healthcare Inc. PEARL™ is a trademark of Maple Brain Healthcare Inc. -->

# PEARL-CHAT v0.1

Extension: `.pearl`  
Payload: UTF-8 JSON  
Media type: `application/vnd.pearl.chat+json`

## Design goals

- A `.pearl` file stays plain JSON so any model or tool can read it without special handling.
- The **core** is the immutable context seed.
- The **surface** is the current working context.
- `hot` and `warm` stay near the surface.
- `cold` sits closer to the core.
- Prior states are never silently mutated; compaction emits a new outer layer.

## Mental model

- **core** = the thing being understood
- **layers** = what was discovered about it
- **surface** = current working understanding
- **branches** = different ways to understand the same thing
- **capsules** = carried prior state
- **lineage** = continuity across state transitions

## Recommended invariants

1. Current state is fully materialized at the surface.
2. Prior layers must not mutate.
3. Canonical JSON should be used before hashing.
4. Compression, if used, should occur before encryption.
5. Compaction should emit a new layer, not rewrite old ones.
6. The core context remains immutable.
7. Branch merges should produce explicit synthesis layers.

## File layout

- `core`
- `surface`
- `lineage`
- `policy`
- `branches`
- `layers`
- `provenance`
- optional `signatures`
- optional `extensions`

## Layer guidance

Use `kind` values like:

- `seed`
- `observation`
- `message_turn`
- `tool_result`
- `interpretation`
- `counter_interpretation`
- `synthesis`
- `decision`
- `memory`
- `compaction_event`
- `branch_event`
- `unseal_event`
- `governance_event`

## Temperature guidance

- `hot`: immediate working set presented first to a model
- `warm`: recent and relevant, but not primary
- `cold`: compacted prior context, retained near the core
- `core`: immutable seed, stored separately from temperature bands

## Suggested use

A model can load the file in this order:

1. `core`
2. `surface.hot`
3. `surface.warm`
4. `surface.current_understanding`
5. active branch head
6. selected cold layers only if needed

## Notes

This is a practical chat/model profile derived from PEARL/TPE ideas, not a regulated-document profile.