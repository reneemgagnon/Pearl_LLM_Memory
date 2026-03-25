---
name: pearl-context
description: >
  Temporal context archive for agent sessions using the PEARL-CHAT v0.2 format
  (.pearl files). Provides structured, layered memory with hot/warm/cold bands,
  immutable core, hash-linked lineage, evidence refs, branching, compaction,
  unsealing, and verification. Use this skill at the start of multi-step tasks,
  long debugging sessions, refactors, investigations, handoffs, or when the user
  mentions pearl, .pearl, context archive, session memory, temporal context, or
  session state.
---

# PEARL Context v0.2

Use this skill when the work will span enough steps that losing context would
hurt correctness or momentum.

## When To Trigger It

Use PEARL when any of these are true:

- The task will likely take more than five tool calls.
- The work involves debugging, investigation, refactoring, design comparison,
  verification, or handoff.
- The user explicitly mentions `pearl`, `.pearl`, session memory, or a context
  archive.
- You need a durable audit trail of findings, decisions, evidence, and outcomes.

## First Step: Inspect, Then Decide

If `.pearl-context/session.pearl` exists, inspect it first. Do not blindly keep
writing to it.

After inspecting, choose exactly one of these paths:

1. Reuse the current session if the objective is the same and you are continuing
   the same work.
2. Create a branch if the objective is the same but you are exploring an
   alternative interpretation, design, or implementation path.
3. Initialize a new session or use a different `--file` if the objective is
   materially different from the current archive.

This rule prevents unrelated tasks from being mixed into one PEARL file.

## Quick Reference

All commands:

```bash
python <skill-path>/scripts/pearl_session.py <command>
```

The CLI accepts `--file` either before or after the subcommand:

```bash
python <skill>/scripts/pearl_session.py --file .pearl-context/session.pearl surface
python <skill>/scripts/pearl_session.py surface --file .pearl-context/session.pearl
```

## Initialize

```bash
python <skill>/scripts/pearl_session.py init \
  --objective "Refactor auth module" \
  --seed-kind task \
  --constraints "Backward compat|No new deps" \
  --labels "refactor,auth"
```

## Add Layers

Use `phase` and `evidence` whenever possible.

```bash
python <skill>/scripts/pearl_session.py add-layer \
  --kind observation \
  --phase audit \
  --summary "Found 3 circular imports" \
  --evidence "src/auth/manager.py|grep:circular" \
  --confidence 0.95
```

```bash
python <skill>/scripts/pearl_session.py add-layer \
  --kind decision \
  --phase design \
  --summary "Constructor injection over service locator" \
  --resolves "Choose DI pattern" \
  --understanding "DI chosen. Next: create interface, update consumers, rerun tests."
```

## Temperature Management

```bash
python <skill>/scripts/pearl_session.py promote
python <skill>/scripts/pearl_session.py compact --summary "Phase 1 complete"
python <skill>/scripts/pearl_session.py unseal \
  --layer-ids <layer-id> \
  --reason "Need to revisit earlier finding"
```

## Branching

```bash
python <skill>/scripts/pearl_session.py branch --name "try-di" --switch
python <skill>/scripts/pearl_session.py branch --name "try-locator" --switch
```

Merge a branch back into the active synthesis path:

```bash
python <skill>/scripts/pearl_session.py merge \
  --branch-id "try-di" \
  --summary "DI chosen: explicit dependencies, easier testing" \
  --accept "try-di" \
  --reject "try-locator" \
  --switch-to-main
```

## Surface and Retrieval

```bash
python <skill>/scripts/pearl_session.py surface
python <skill>/scripts/pearl_session.py load-context --token-budget 4000 --format text
python <skill>/scripts/pearl_session.py verify
```

## Recommended Layer Kinds and Phases

| Kind | Typical phases |
|------|----------------|
| `observation` | `audit`, `investigation` |
| `interpretation` | `audit`, `design`, `investigation` |
| `counter_interpretation` | `audit`, `review` |
| `decision` | `design`, `planning`, `refactor` |
| `tool_result` | `implementation`, `verification` |
| `synthesis` | `design`, `review`, `handoff` |
| `memory` | `handoff` |

Supported phases in the reference CLI:

- `audit`
- `design`
- `refactor`
- `verification`
- `handoff`
- `investigation`
- `planning`
- `implementation`
- `review`

## Evidence Refs

Evidence refs are pipe-separated strings. Common forms:

- File: `src/auth/manager.py`
- File with line: `src/auth/manager.py:42`
- Grep or search result: `grep:circular`
- Test run: `pytest:test_auth.py`
- Specific test: `test:test_auth::test_login_flow`
- Diff or commit: `diff:abc123` or `git:commit:<sha>`

## Working Pattern

```text
1. Inspect existing session if present.
2. Reuse, branch, or init based on objective match.
3. Add observations and evidence.
4. Add interpretations and decisions.
5. Perform the work.
6. Add tool results for verification.
7. Promote or compact when the hot band grows.
8. Unseal or branch when revisiting older or alternate context.
9. Run verify before handoff or major transitions.
```

## v0.2 Operating Rules

- Treat `current_understanding` as an operational brief, not a restatement of the seed.
- Keep evidence close to each consequential layer.
- Prefer branching over overwriting when exploring alternatives.
- Use a new file for unrelated objectives.
- Run `verify` regularly on long-lived archives.

## What `verify` Checks

The v0.2 verifier checks more than core and chain hashes. It also checks:

- `prior_layer_id` continuity
- `prior_chain_hash` continuity
- `lineage.depth`
- `lineage.state_hash`
- Surface band references
- Active-branch consistency
- Branch head integrity
- Layer-to-branch references

## File Locations

- Default session file: `.pearl-context/session.pearl`
- Override: `--file` or `-f`
- Store unrelated efforts in separate `.pearl` files instead of reusing one session

## References

- Schema: `references/pearl-chat-schema.json`
- Spec: `references/pearl-chat-spec.md`
- Engine: `scripts/pearl_session.py`
