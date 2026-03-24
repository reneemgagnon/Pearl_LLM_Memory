---
name: pearl-context
description: >
  Temporal context archive for agent sessions using the PEARL-CHAT v0.2 format (.pearl files).
  PEARL = Protected · Evolving · Annotation · Resistant · Layering. Provides structured, layered
  memory with temperature-graded context (hot/warm/cold), immutable core, JCS-hashed chain of
  custody, branching with accept/reject tracking, evidence refs, layer phases, unsealing, and
  capsule compression. Use this skill at the START of any multi-step task, complex refactor,
  debugging session, architectural exploration, security audit, or long-running coding project.
  Also trigger when the user mentions "pearl", ".pearl", "context archive", "session memory",
  "temporal context", "session state", or when you detect the task will require more than ~5
  tool calls. If `.pearl-context/session.pearl` exists, ALWAYS load it first. Think of PEARL as
  geological memory: immutable core at the center, cold compacted history, warm recent context,
  hot lava at the surface.
---

# PEARL Context v0.2 — Temporal Archive Skill

## What's New in v0.2

1. **Core immutability enforced** — `_core_hash` snapshot at genesis, verified every write
2. **JCS-RFC8785** canonical serialization for all hashing (deterministic, verifiable)
3. **Explicit chain_hash** — `SHA256(prior_chain_hash | layer_hash)`, walkable by any verifier
4. **Layer phases** — `--phase audit|design|refactor|verification|handoff|...`
5. **Unseal command** — promote cold → hot with `unseal_event` audit trail
6. **Single active branch** — switching suspends prior branches automatically
7. **Accept/reject on merge** — `--accept` and `--reject` track branch outcomes
8. **Operational brief** — `current_understanding` is a working summary, not a seed echo
9. **Evidence refs** — `--evidence "file.py|grep:pattern|test:output"` on every layer
10. **Capsule compression** — large cold capsules auto-compress with zlib+base64

## Quick Reference

All commands: `python <skill-path>/scripts/pearl_session.py <command>`

### Initialize
```bash
python <skill>/scripts/pearl_session.py init \
  --objective "Refactor auth module" --seed-kind task \
  --constraints "Backward compat|No new deps" --labels "refactor,auth"
```

### Add Layers (with phase + evidence)
```bash
# Observation during audit phase
python <skill>/scripts/pearl_session.py add-layer \
  -k observation -s "Found 3 circular imports" \
  --phase audit --evidence "src/auth/manager.py|grep:circular" --confidence 0.95

# Tool result during verification
python <skill>/scripts/pearl_session.py add-layer \
  -k tool_result -s "All 47 tests pass after refactor" \
  --phase verification --evidence "pytest:test_auth.py|coverage:92pct"

# Decision during design
python <skill>/scripts/pearl_session.py add-layer \
  -k decision -s "Constructor injection over service locator" \
  --phase design --resolves "Choose DI pattern" \
  --understanding "DI chosen. Next: create Protocol interface, update 12 consumers."
```

### Temperature Management
```bash
python <skill>/scripts/pearl_session.py promote          # hot → warm
python <skill>/scripts/pearl_session.py compact -s "Phase 1 done"  # warm → cold (auto-compresses if large)
python <skill>/scripts/pearl_session.py unseal \          # cold → hot [NEW]
  --layer-ids <id> --reason "Need to revisit finding"
```

### Branching (single-active enforced)
```bash
python <skill>/scripts/pearl_session.py branch -n "try-DI" --switch
python <skill>/scripts/pearl_session.py branch -n "try-locator" --switch  # suspends try-DI

# Merge with accept/reject tracking [NEW]
python <skill>/scripts/pearl_session.py merge -b "try-DI" \
  -s "DI chosen: explicit deps, fully testable" \
  --accept "try-DI" --reject "try-locator" --switch-to-main
```

### Surface & Context
```bash
python <skill>/scripts/pearl_session.py surface
python <skill>/scripts/pearl_session.py load-context --token-budget 4000 --format text
python <skill>/scripts/pearl_session.py verify   # core + hashes + chain + single branch
```

## Layer Kinds × Phases

| Kind                     | Typical Phases                    |
|--------------------------|-----------------------------------|
| `observation`            | audit, investigation              |
| `interpretation`         | audit, design, investigation      |
| `counter_interpretation` | audit, review                     |
| `decision`               | design, refactor, planning        |
| `tool_result`            | verification, implementation      |
| `synthesis`              | design, review                    |
| `memory`                 | handoff                           |

## Evidence Refs Format

Pipe-separated, freeform but conventionally:
- Files: `src/auth/manager.py` or `src/auth/manager.py:42`
- Tool runs: `grep:pattern`, `pytest:test_auth.py`, `bandit:output.json`
- Diffs: `diff:abc123`, `git:commit:sha`
- Tests: `test:test_auth::test_login_flow`

## Workflow Pattern
```
1. INIT          → Create .pearl with objective
2. OBSERVE       → add-layer -k observation --phase audit --evidence "..."
3. INTERPRET     → add-layer -k interpretation --phase audit
4. DECIDE        → add-layer -k decision --phase design
5. ACT           → (do the work)
6. VERIFY        → add-layer -k tool_result --phase verification --evidence "..."
7. PROMOTE       → promote (age hot layers to warm)
8. REPEAT 2-7
9. COMPACT       → compact (warm → cold, auto-compresses if large)
10. UNSEAL       → unseal (if cold context needs revisiting)
11. BRANCH/MERGE → branch/merge with --accept/--reject for alternatives
12. SURFACE      → check state anytime
```

## Key Principles

1. **Always init before complex tasks.** The seed anchors everything.
2. **Use phases.** They classify *what stage of work* each layer belongs to.
3. **Attach evidence.** Files, tool outputs, diffs — makes layers forensically useful.
4. **Write operational briefs.** `--understanding` should say what's happening NOW, not echo the seed.
5. **Branch when uncertain.** Use `--accept`/`--reject` to document the decision.
6. **Unseal when needed.** Cold context can return to hot — but the unseal is logged.
7. **Verify regularly.** Core integrity, hash chain, single active branch — all checked.

## File Locations

- Default: `.pearl-context/session.pearl`
- Override: `--file` / `-f`
- Gitignore `.pearl-context/` (session-local state)

## References

- Schema: `references/pearl-chat-schema.json`
- Spec: `references/pearl-chat-spec.md`
