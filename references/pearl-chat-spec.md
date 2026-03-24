<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2025-2026 Maple Brain Healthcare Inc. PEARL(TM) is a trademark of Maple Brain Healthcare Inc. -->

# PEARL-CHAT v0.2

Extension: `.pearl`  
Payload: UTF-8 JSON  
Media type: `application/vnd.pearl.chat+json`

## Design goals

- A `.pearl` file stays plain JSON so any model or tool can read it without special handling.
- The **core** is immutable after initialization and is protected by `_core_hash`.
- The **surface** holds the fully materialized working context.
- `hot`, `warm`, and `cold` model recency and retrieval priority.
- Layers are append-only and linked by deterministic hashes.
- Branching and merge outcomes are explicit, inspectable, and auditable.

## Mental model

- **core** = the thing being understood
- **layers** = what was discovered, decided, or produced
- **surface** = current working understanding
- **branches** = parallel lines of exploration
- **capsules** = compacted prior context
- **lineage** = cryptographic continuity across state transitions

## Required invariants

1. `core` remains immutable after initialization.
2. `_core_hash` equals the canonical hash of `core` for v0.2 files.
3. `layers` are append-only.
4. Each layer hash is derived from canonical JSON of `layer.state`.
5. Each `chain_hash` is derived as `SHA256(prior_chain_hash | layer_hash)`.
6. `lineage.current_layer_id` and `lineage.chain_hash` point to the latest layer.
7. `surface.active_branch_id` identifies exactly one active branch.
8. Each branch `head_layer_id` matches the last entry in that branch's `layer_ids`.

## File layout

- `pearl_version`
- `pearl_type`
- `media_type`
- `spec`
- `encoding`
- `_core_hash` for v0.2+
- `core`
- `surface`
- `lineage`
- `policy`
- `branches`
- `layers`
- optional `capsules`
- `provenance`
- optional `signatures`
- optional `extensions`

## Layer model

Supported `kind` values in the reference implementation:

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
- `reopen_event`
- `governance_event`

`phase` is optional and classifies work stage, for example:

- `audit`
- `design`
- `refactor`
- `verification`
- `handoff`
- `investigation`
- `planning`
- `implementation`
- `review`

## Temperature model

- `hot`: immediate working set presented first to a model
- `warm`: recent and relevant, but not primary
- `cold`: compacted or revisited prior context
- `core`: immutable seed, stored separately from temperature bands

## Branch model

- A PEARL session may contain multiple branches.
- Only one branch should be `active` at a time.
- Other common branch states are `candidate`, `suspended`, `merged`, `rejected`, `abandoned`, and `archived`.
- Branch creation emits a `branch_event`.
- Merge synthesis should record accepted and rejected branch outcomes when applicable.

## Suggested retrieval order

1. `core`
2. `surface.hot`
3. `surface.warm`
4. `surface.current_understanding`
5. active branch head
6. selected cold layers only if needed

## Notes

This is a practical chat/model profile derived from PEARL/TPE ideas, not a regulated-document profile.
