<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Copyright 2025-2026 Maple Brain Healthcare Inc. PEARL(TM) is a trademark of Maple Brain Healthcare Inc. -->

# PEARL-CHAT v0.2

Extension: `.pearl`  
Payload: UTF-8 JSON  
Media type: `application/vnd.pearl.chat+json`

## Scope

PEARL-CHAT is a practical profile for storing agent and chat working context in
a plain JSON envelope with verifiable lineage and durable session memory.

This v0.2 spec matches the reference implementation in `scripts/pearl_session.py`.

## Design Goals

- Keep the file plain JSON so any runtime can read it.
- Preserve an immutable seed context in `core`.
- Keep the current working state materialized in `surface`.
- Record discoveries, decisions, and results as append-only `layers`.
- Maintain deterministic hashes and chain continuity.
- Support branching, merge synthesis, compaction, and unsealing.

## Required v0.2 Invariants

1. `core` remains immutable after initialization.
2. `_core_hash` equals the canonical hash of `core`.
3. `layers` are append-only.
4. Each `layer_hash` is derived from canonical JSON of `layer.state`.
5. Each `chain_hash` is derived as `SHA256(prior_chain_hash | layer_hash)`.
6. `lineage.current_layer_id` matches the latest layer.
7. `lineage.chain_hash` matches the latest layer chain hash.
8. `surface.active_branch_id` identifies exactly one active branch.
9. Every branch `head_layer_id` matches the last element of that branch's `layer_ids`.
10. Temperature bands reference only existing layers whose `temperature` matches the band.

## Envelope Layout

Top-level fields used by the reference implementation:

- `pearl_version`
- `pearl_type`
- `media_type`
- `spec`
- `encoding`
- `_core_hash`
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

## Core

`core` contains the original task or context seed:

- `context_id`
- `created_at`
- `seed`
- `objective`
- optional constraints, facts, ontology, stakes, owner, labels

In v0.2 the reference CLI computes `_core_hash` at initialization and verifies
it before every write.

## Surface

`surface` is the materialized working state. It should contain:

- `updated_at`
- `active_branch_id`
- `focus`
- `hot`
- `warm`
- `cold`
- `current_understanding`
- `current_plan`
- `open_loops`
- `resolved_items`
- `retrieval_cues`
- `attention_weights`

`current_understanding` is an operational brief. It should summarize what is
currently true and what matters next, not merely echo the original seed.

## Lineage

`lineage` tracks continuity across updates. Important fields include:

- `genesis_layer_id`
- `current_layer_id`
- `prior_layer_id`
- `depth`
- `branch_count`
- `chain_hash`
- `chain_hash_derivation`
- `prior_chain_hash`
- `state_hash`

## Layers

Common `kind` values in the v0.2 reference implementation:

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

Supported `phase` values in the reference implementation:

- `audit`
- `design`
- `refactor`
- `verification`
- `handoff`
- `investigation`
- `planning`
- `implementation`
- `review`

## Branches

Branches model alternate lines of exploration for the same objective.

- Only one branch should be `active` at a time.
- Creating a branch emits a `branch_event`.
- Switching active branches suspends the previously active branch.
- Merge synthesis may record accepted and rejected branch outcomes.

Common branch states:

- `active`
- `candidate`
- `suspended`
- `merged`
- `rejected`
- `abandoned`
- `archived`

## Temperature Model

- `hot`: immediate working set
- `warm`: recent but secondary context
- `cold`: compacted or older context retained for retrieval
- `core`: immutable seed stored outside the temperature bands

Compaction creates a new outer layer and moves warm context inward. Unsealing
promotes selected cold layers back into the hot band and records the event.

## Suggested Retrieval Order

1. `core`
2. `surface.hot`
3. `surface.warm`
4. `surface.current_understanding`
5. active branch head
6. selected cold layers only as needed

## Verification Expectations

An implementation claiming v0.2 compatibility should be able to verify:

- Core hash integrity
- Layer hash integrity
- Chain continuity
- Prior layer and prior chain references
- Surface state hash
- Active branch consistency
- Branch head integrity
- Temperature-band integrity

## Legacy Notes

v0.1-era archives may exist in the wild, but the reference path in this
repository is now PEARL-CHAT v0.2.
