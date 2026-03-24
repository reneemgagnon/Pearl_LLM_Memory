#!/usr/bin/env python3
"""
pearl_session.py — PEARL-CHAT v0.2 Session Engine
===================================================
Protected · Evolving · Annotation · Resistant · Layering

v0.2 CHANGES FROM v0.1:
    [1]  Core immutability enforced — core_hash at genesis, verified every write.
    [2]  JCS-RFC8785 canonical serialization for all hashing.
    [3]  Explicit chain_hash: SHA256(prior_chain_hash + "|" + layer_hash).
    [4]  Layer phases: audit, design, refactor, verification, handoff, etc.
    [5]  unseal command — cold → hot with unseal_event traceability.
    [6]  Single active branch enforced — switching suspends prior.
    [7]  Merge records accepted_branch_id and rejected_branch_ids.
    [8]  surface.current_understanding is an operational brief, not seed echo.
    [9]  evidence_refs on every layer — files, tool runs, diffs, tests.
    [10] Capsule compression — large capsules use zlib+base64.

Copyright 2025-2026 Maple Brain Healthcare Inc.
PEARL™ is a trademark of Maple Brain Healthcare Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PEARL_VERSION = "0.2"
PEARL_TYPE = "chat_context"
MEDIA_TYPE = "application/vnd.pearl.chat+json"
SPEC_NAME = "PEARL-CHAT"
HASH_ALGORITHM = "sha256"
CHAIN_SEP = "|"

DEFAULT_PEARL_DIR = Path(".pearl-context")
DEFAULT_PEARL_FILE = DEFAULT_PEARL_DIR / "session.pearl"
DEFAULT_PROMOTE_HOT_AFTER = 5
DEFAULT_PROMOTE_WARM_AFTER = 3
DEFAULT_COLD_THRESHOLD_BYTES = 8192
DEFAULT_COMPRESS_THRESHOLD = 16384

LAYER_PHASES = [
    "audit", "design", "refactor", "verification", "handoff",
    "investigation", "planning", "implementation", "review",
]
LAYER_KINDS = [
    "seed", "observation", "message_turn", "tool_result",
    "interpretation", "counter_interpretation", "synthesis",
    "decision", "memory", "compaction_event", "branch_event",
    "unseal_event", "reopen_event", "governance_event",
]

# ---------------------------------------------------------------------------
# JCS-RFC8785 Canonical JSON [FEEDBACK #2]
# ---------------------------------------------------------------------------
def _jcs(obj: Any) -> str:
    """Serialize to canonical JSON per RFC 8785 (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)

def _hash_jcs(obj: Any) -> str:
    """SHA-256 of JCS-canonical JSON."""
    return hashlib.sha256(_jcs(obj).encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Explicit Chain Hash [FEEDBACK #3]
# ---------------------------------------------------------------------------
def _chain(prior: str, layer_hash: str) -> str:
    """chain_hash = SHA256(prior_chain_hash + "|" + layer_hash)"""
    return hashlib.sha256(f"{prior}{CHAIN_SEP}{layer_hash}".encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Core Immutability [FEEDBACK #1]
# ---------------------------------------------------------------------------
def _core_hash(core: dict) -> str:
    return _hash_jcs(core)

def _guard_core(pearl: dict) -> None:
    """Fatal error if core was mutated after genesis."""
    expected = pearl.get("_core_hash")
    if expected is None:
        return
    actual = _core_hash(pearl["core"])
    if actual != expected:
        print("FATAL: Core immutability violation!", file=sys.stderr)
        print(f"  Expected: {expected[:24]}...", file=sys.stderr)
        print(f"  Actual:   {actual[:24]}...", file=sys.stderr)
        sys.exit(2)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now():
    return datetime.now(timezone.utc).isoformat()

def _uid():
    return uuid.uuid4().hex[:12]

def _load(fp: Path) -> dict:
    if not fp.exists():
        print(f"ERROR: No PEARL file at {fp}", file=sys.stderr)
        sys.exit(1)
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(pearl: dict, fp: Path) -> None:
    _guard_core(pearl)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(pearl, f, indent=2, ensure_ascii=False)

def _layer(pearl, lid):
    for l in pearl.get("layers", []):
        if l["layer_id"] == lid:
            return l
    return None

def _single_active(pearl, new_id):
    """Enforce one active branch [FEEDBACK #6]."""
    for b in pearl["branches"]:
        if b["branch_id"] == new_id:
            b["status"] = "active"
        elif b["status"] == "active":
            b["status"] = "suspended"

# ---------------------------------------------------------------------------
# Capsule Compression [FEEDBACK #10]
# ---------------------------------------------------------------------------
def _capsule(body: dict, threshold: int = DEFAULT_COMPRESS_THRESHOLD) -> dict:
    raw = _jcs(body).encode("utf-8")
    h = _hash_jcs(body)
    if len(raw) > threshold:
        comp = zlib.compress(raw, level=6)
        return {"representation": "compressed_inline", "content_type": "application/json",
                "encoding": "zlib+base64", "body": base64.b64encode(comp).decode("ascii"),
                "size_bytes": len(raw), "compressed_bytes": len(comp), "hash": h}
    return {"representation": "inline_snapshot", "content_type": "application/json",
            "encoding": "utf-8", "body": body, "size_bytes": len(raw), "hash": h}

def _uncapsule(cap: dict) -> dict:
    if cap.get("representation") == "compressed_inline":
        return json.loads(zlib.decompress(base64.b64decode(cap["body"])))
    if cap.get("representation") == "external_ref":
        loc = cap.get("locator", "")
        if os.path.exists(loc):
            with open(loc, "r") as f:
                return json.load(f)
        return {"error": f"Not found: {loc}"}
    return cap.get("body", {})

# ===========================================================================
# INIT
# ===========================================================================
def cmd_init(args):
    fp = Path(args.file)
    if fp.exists() and not args.force:
        print(f"PEARL file exists at {fp}. Use --force.", file=sys.stderr); sys.exit(1)

    now = _now(); cid = _uid(); gid = f"layer-{_uid()}"; bid = f"branch-{_uid()}"

    core = {
        "context_id": cid, "created_at": now,
        "seed": {"kind": args.seed_kind, "content": {"summary": args.objective}},
        "objective": args.objective,
        "constraints": args.constraints.split("|") if args.constraints else [],
        "enduring_facts": [], "ontology": [],
        "stakes": args.stakes or "",
        "owner": {"type": "user", "id": args.owner or "claude-code-user"},
        "labels": args.labels.split(",") if args.labels else [],
    }
    ch = _core_hash(core)

    gs = {"summary": f"Session initialized: {args.objective}"}
    gh = _hash_jcs(gs)
    gc = _chain("genesis", gh)

    genesis = {
        "layer_id": gid, "created_at": now, "temperature": "hot", "kind": "seed",
        "phase": None, "actor": {"type": "system", "id": "pearl-engine", "name": "PEARL v0.2"},
        "branch_id": bid, "caused_by": [], "evidence_refs": [],
        "state": gs, "hashes": {"layer_hash": gh, "chain_hash": gc}, "tags": ["genesis"],
    }

    # [FEEDBACK #8] operational brief, not seed echo
    surface = {
        "updated_at": now, "active_branch_id": bid,
        "focus": args.objective,
        "hot": {"layer_ids": [gid]}, "warm": {"layer_ids": []}, "cold": {"layer_ids": []},
        "current_understanding": f"Starting: {args.objective}. No observations yet.",
        "current_plan": [], "open_loops": [], "resolved_items": [],
        "retrieval_cues": [], "attention_weights": {},
    }

    lineage = {
        "genesis_layer_id": gid, "current_layer_id": gid, "depth": 0, "branch_count": 1,
        "chain_hash": gc, "chain_hash_derivation": "SHA256(prior_chain_hash | layer_hash)",
        "prior_chain_hash": None, "state_hash": _hash_jcs(surface),
    }

    policy = {
        "immutability": "prior_layers_must_not_mutate", "core_immutability": "enforced",
        "temperature_model": {"core_is_immutable": True, "hot": "immediate working set",
                              "warm": "recent but not primary", "cold": "compacted prior context"},
        "compaction": {"mode": "snapshot_only", "promote_hot_after_messages": DEFAULT_PROMOTE_HOT_AFTER,
                       "promote_warm_after_compactions": DEFAULT_PROMOTE_WARM_AFTER,
                       "cold_capsule_inline_threshold_bytes": DEFAULT_COLD_THRESHOLD_BYTES,
                       "compress_capsule_above_bytes": DEFAULT_COMPRESS_THRESHOLD,
                       "retain_exact_prior_state": True},
        "branching": {"allow_parallel_interpretations": True, "require_synthesis_on_merge": True,
                      "enforce_single_active_branch": True},
        "verification": {"hash_algorithm": HASH_ALGORITHM, "canonical_json": "JCS-RFC8785",
                         "verify_without_unsealing": True},
    }

    branches = [{"branch_id": bid, "name": "main", "status": "active",
                 "head_layer_id": gid, "parent_branch_id": None,
                 "intent": "Primary working branch", "summary": args.objective, "layer_ids": [gid]}]

    pearl = {
        "pearl_version": PEARL_VERSION, "pearl_type": PEARL_TYPE, "media_type": MEDIA_TYPE,
        "spec": {"name": SPEC_NAME, "version": PEARL_VERSION, "compatibility": ["0.1", "0.2"]},
        "encoding": {"charset": "utf-8", "canonical_json": "JCS-RFC8785", "compression_order": "none"},
        "_core_hash": ch, "core": core, "surface": surface, "lineage": lineage,
        "policy": policy, "branches": branches, "layers": [genesis],
        "provenance": {"created_by": {"type": "system", "id": "pearl-engine", "name": "PEARL v0.2"}, "created_at": now},
        "extensions": {},
    }

    _save(pearl, fp)
    print(f"✓ PEARL v0.2 session initialized at {fp}")
    print(f"  Context ID : {cid}")
    print(f"  Core Hash  : {ch[:24]}...")
    print(f"  Objective  : {args.objective}")
    print(f"  Branch     : main ({bid})")
    print(f"  Chain Hash : {gc[:24]}...")

# ===========================================================================
# ADD-LAYER [FEEDBACK #4, #9]
# ===========================================================================
def cmd_add_layer(args):
    fp = Path(args.file); pearl = _load(fp)
    now = _now(); lid = f"layer-{_uid()}"
    prior_id = pearl["lineage"]["current_layer_id"]
    prior_ch = pearl["lineage"]["chain_hash"]
    ab = pearl["surface"]["active_branch_id"]

    state = {"summary": args.summary}
    if args.claims: state["claims"] = args.claims.split("|")
    if args.questions: state["questions"] = args.questions.split("|")
    if args.confidence is not None: state["confidence"] = args.confidence
    if args.open_loops: state["open_loops"] = args.open_loops.split("|")
    if args.payload:
        try: state["payload"] = json.loads(args.payload)
        except json.JSONDecodeError: state["payload"] = args.payload

    lh = _hash_jcs(state)
    ch = _chain(prior_ch, lh)
    ev = args.evidence.split("|") if args.evidence else []

    layer = {
        "layer_id": lid, "created_at": now, "temperature": args.temperature or "hot",
        "kind": args.kind, "phase": args.phase,
        "actor": {"type": args.actor_type or "assistant", "id": args.actor_id or "claude-code"},
        "branch_id": ab, "caused_by": [], "evidence_refs": ev,
        "state": state,
        "hashes": {"layer_hash": lh, "chain_hash": ch, "prior_layer_id": prior_id, "prior_chain_hash": prior_ch},
        "tags": args.tags.split(",") if args.tags else [],
    }

    pearl["layers"].append(layer)
    pearl["surface"]["hot"]["layer_ids"].append(lid)
    pearl["surface"]["updated_at"] = now

    if args.understanding:
        pearl["surface"]["current_understanding"] = args.understanding
    if args.open_loops:
        existing = pearl["surface"].get("open_loops", [])
        pearl["surface"]["open_loops"] = list(set(existing + args.open_loops.split("|")))
    if args.resolves:
        resolved = args.resolves.split("|")
        pearl["surface"]["resolved_items"] = pearl["surface"].get("resolved_items", []) + resolved
        pearl["surface"]["open_loops"] = [o for o in pearl["surface"].get("open_loops", []) if o not in resolved]

    pearl["lineage"].update({"current_layer_id": lid, "prior_layer_id": prior_id,
        "depth": pearl["lineage"]["depth"] + 1, "prior_chain_hash": prior_ch,
        "chain_hash": ch, "state_hash": _hash_jcs(pearl["surface"])})

    for b in pearl["branches"]:
        if b["branch_id"] == ab:
            b["head_layer_id"] = lid; b["layer_ids"].append(lid); break

    pearl["provenance"]["updated_by"] = layer["actor"]
    pearl["provenance"]["updated_at"] = now

    _save(pearl, fp)
    print(f"✓ Layer added: {lid}")
    print(f"  Kind       : {args.kind}" + (f" [{args.phase}]" if args.phase else ""))
    print(f"  Temp       : {layer['temperature']}")
    print(f"  Summary    : {args.summary[:80]}...")
    print(f"  Chain      : {ch[:24]}...")
    print(f"  Depth      : {pearl['lineage']['depth']}")
    if ev: print(f"  Evidence   : {len(ev)} refs")

# ===========================================================================
# PROMOTE
# ===========================================================================
def cmd_promote(args):
    fp = Path(args.file); pearl = _load(fp)
    hot = pearl["surface"]["hot"]["layer_ids"]
    thr = pearl["policy"]["compaction"].get("promote_hot_after_messages", DEFAULT_PROMOTE_HOT_AFTER)

    if len(hot) <= thr and not args.force:
        print(f"Hot band has {len(hot)} layers (threshold: {thr}). No promotion needed."); return

    keep = max(1, thr - 1) if not args.force else max(1, len(hot) // 2)
    promote = hot[:-keep] if len(hot) > keep else []
    if not promote: print("Nothing to promote."); return

    pearl["surface"]["hot"]["layer_ids"] = hot[len(promote):]
    pearl["surface"]["warm"]["layer_ids"] += promote
    pearl["surface"]["updated_at"] = _now()

    for l in pearl["layers"]:
        if l["layer_id"] in promote: l["temperature"] = "warm"

    _save(pearl, fp)
    print(f"✓ Promoted {len(promote)} layers: hot → warm")
    for lid in promote: print(f"  → {lid}")

# ===========================================================================
# COMPACT [FEEDBACK #10]
# ===========================================================================
def cmd_compact(args):
    fp = Path(args.file); pearl = _load(fp)
    warm = pearl["surface"]["warm"]["layer_ids"]
    if not warm: print("Warm band empty."); return

    now = _now(); cid = f"layer-{_uid()}"
    pch = pearl["lineage"]["chain_hash"]

    sums, evs = [], []
    for l in pearl["layers"]:
        if l["layer_id"] in warm:
            sums.append(f"[{l['kind']}] {l['state']['summary']}")
            evs.extend(l.get("evidence_refs", []))

    cap_body = {"compacted_layer_ids": warm, "summaries": sums, "evidence_refs": list(set(evs))}
    thr = pearl["policy"]["compaction"].get("compress_capsule_above_bytes", DEFAULT_COMPRESS_THRESHOLD)
    cap = _capsule(cap_body, thr)

    state = {"summary": args.summary or f"Compacted {len(warm)} warm layers", "claims": sums[:5]}
    lh = _hash_jcs(state); ch = _chain(pch, lh)

    layer = {
        "layer_id": cid, "created_at": now, "temperature": "cold", "kind": "compaction_event",
        "phase": None, "actor": {"type": "system", "id": "pearl-engine", "name": "PEARL v0.2"},
        "branch_id": pearl["surface"]["active_branch_id"],
        "caused_by": [{"type": "compaction", "ref": lid, "summary": "warm→cold"} for lid in warm],
        "evidence_refs": list(set(evs)), "state": state, "prior_capsule": cap,
        "hashes": {"layer_hash": lh, "chain_hash": ch, "prior_chain_hash": pch, "prior_capsule_hash": cap["hash"]},
        "tags": ["compaction"],
    }

    pearl["layers"].append(layer)
    pearl["surface"]["cold"]["layer_ids"] += warm + [cid]
    pearl["surface"]["warm"]["layer_ids"] = []
    pearl["surface"]["updated_at"] = now

    for l in pearl["layers"]:
        if l["layer_id"] in warm: l["temperature"] = "cold"

    pearl["lineage"].update({"current_layer_id": cid, "depth": pearl["lineage"]["depth"] + 1,
        "prior_chain_hash": pch, "chain_hash": ch,
        "compacted_from_layer_ids": pearl["lineage"].get("compacted_from_layer_ids", []) + warm})

    _save(pearl, fp)
    rep = cap["representation"]
    print(f"✓ Compacted {len(warm)} warm layers → cold ({rep})")
    print(f"  Compaction layer: {cid}")
    print(f"  Chain: {ch[:24]}...")
    if rep == "compressed_inline":
        print(f"  Compressed: {cap['size_bytes']}B → {cap['compressed_bytes']}B ({cap['compressed_bytes']/cap['size_bytes']*100:.0f}%)")

# ===========================================================================
# UNSEAL [FEEDBACK #5]
# ===========================================================================
def cmd_unseal(args):
    fp = Path(args.file); pearl = _load(fp)
    now = _now(); targets = args.layer_ids.split(",")
    pch = pearl["lineage"]["chain_hash"]
    cold = pearl["surface"]["cold"]["layer_ids"]

    for t in targets:
        if t not in cold:
            print(f"ERROR: {t} not in cold band.", file=sys.stderr); sys.exit(1)

    uid = f"layer-{_uid()}"
    state = {"summary": f"Unsealed {len(targets)} cold layers: {args.reason}",
             "claims": [f"Promoted {t} cold → hot" for t in targets]}
    lh = _hash_jcs(state); ch = _chain(pch, lh)

    layer = {
        "layer_id": uid, "created_at": now, "temperature": "hot", "kind": "unseal_event",
        "phase": None, "actor": {"type": "system", "id": "pearl-engine", "name": "PEARL v0.2"},
        "branch_id": pearl["surface"]["active_branch_id"],
        "caused_by": [{"type": "manual_review", "ref": t, "summary": f"Unseal: {args.reason}"} for t in targets],
        "evidence_refs": [], "state": state,
        "hashes": {"layer_hash": lh, "chain_hash": ch, "prior_chain_hash": pch},
        "tags": ["unseal"],
    }

    pearl["layers"].append(layer)
    pearl["surface"]["cold"]["layer_ids"] = [l for l in cold if l not in targets]
    pearl["surface"]["hot"]["layer_ids"] = targets + [uid] + pearl["surface"]["hot"]["layer_ids"]
    pearl["surface"]["updated_at"] = now

    for l in pearl["layers"]:
        if l["layer_id"] in targets: l["temperature"] = "hot"

    pearl["lineage"].update({"current_layer_id": uid, "depth": pearl["lineage"]["depth"] + 1,
        "prior_chain_hash": pch, "chain_hash": ch})

    _save(pearl, fp)
    print(f"✓ Unsealed {len(targets)} layers: cold → hot")
    print(f"  Reason: {args.reason}")
    print(f"  Unseal layer: {uid}")
    for t in targets: print(f"  ↑ {t}")

# ===========================================================================
# BRANCH [FEEDBACK #6]
# ===========================================================================
def cmd_branch(args):
    fp = Path(args.file); pearl = _load(fp)
    now = _now(); bid = f"branch-{_uid()}"
    parent = pearl["surface"]["active_branch_id"]
    head = pearl["lineage"]["current_layer_id"]
    pch = pearl["lineage"]["chain_hash"]

    pearl["branches"].append({
        "branch_id": bid, "name": args.name, "status": "candidate",
        "head_layer_id": head, "parent_branch_id": parent,
        "intent": args.intent or f"Explore: {args.name}",
        "summary": args.name, "layer_ids": [],
    })

    blid = f"layer-{_uid()}"
    state = {"summary": f"Branched '{args.name}' from {parent} at {head}"}
    lh = _hash_jcs(state); ch = _chain(pch, lh)

    pearl["layers"].append({
        "layer_id": blid, "created_at": now, "temperature": "hot", "kind": "branch_event",
        "phase": None, "actor": {"type": "system", "id": "pearl-engine", "name": "PEARL v0.2"},
        "branch_id": bid, "caused_by": [], "evidence_refs": [],
        "state": state,
        "hashes": {"layer_hash": lh, "chain_hash": ch, "prior_chain_hash": pch},
        "tags": ["branch-created"],
    })

    pearl["lineage"]["branch_count"] = len(pearl["branches"])
    pearl["lineage"]["chain_hash"] = ch
    pearl["lineage"]["prior_chain_hash"] = pch

    if args.switch:
        _single_active(pearl, bid)
        pearl["surface"]["active_branch_id"] = bid
        pearl["surface"]["updated_at"] = now
        print(f"  Switched to branch: {args.name} (prior branches suspended)")

    _save(pearl, fp)
    print(f"✓ Branch created: {args.name} ({bid})")

# ===========================================================================
# MERGE [FEEDBACK #7]
# ===========================================================================
def cmd_merge(args):
    fp = Path(args.file); pearl = _load(fp)
    now = _now(); pch = pearl["lineage"]["chain_hash"]

    target = None
    for b in pearl["branches"]:
        if b["branch_id"] == args.branch_id or b["name"] == args.branch_id:
            target = b; break
    if not target:
        print(f"ERROR: Branch '{args.branch_id}' not found.", file=sys.stderr); sys.exit(1)

    # Resolve accepted/rejected [FEEDBACK #7]
    acc_id = None
    if args.accept:
        for b in pearl["branches"]:
            if b["branch_id"] == args.accept or b["name"] == args.accept:
                acc_id = b["branch_id"]; break

    rej_ids = []
    if args.reject:
        for nm in args.reject.split("|"):
            for b in pearl["branches"]:
                if b["branch_id"] == nm or b["name"] == nm:
                    rej_ids.append(b["branch_id"]); break

    sid = f"layer-{_uid()}"
    state = {"summary": args.summary or f"Merged branch '{target['name']}'",
             "claims": [f"Branch '{target['name']}' findings incorporated"]}
    if acc_id: state["accepted_branch_id"] = acc_id
    if rej_ids: state["rejected_branch_ids"] = rej_ids

    lh = _hash_jcs(state); ch = _chain(pch, lh)

    pearl["layers"].append({
        "layer_id": sid, "created_at": now, "temperature": "hot", "kind": "synthesis",
        "phase": None, "actor": {"type": "assistant", "id": "claude-code"},
        "branch_id": pearl["surface"]["active_branch_id"],
        "caused_by": [{"type": "merge", "ref": target["branch_id"], "summary": f"Merged: {target['name']}"}],
        "evidence_refs": [], "state": state,
        "hashes": {"layer_hash": lh, "chain_hash": ch, "prior_chain_hash": pch},
        "tags": ["merge-synthesis"],
    })

    pearl["surface"]["hot"]["layer_ids"].append(sid)
    pearl["surface"]["updated_at"] = now
    target["status"] = "merged"
    for b in pearl["branches"]:
        if b["branch_id"] in rej_ids: b["status"] = "rejected"

    if args.switch_to_main:
        for b in pearl["branches"]:
            if b["name"] == "main":
                _single_active(pearl, b["branch_id"])
                pearl["surface"]["active_branch_id"] = b["branch_id"]; break

    pearl["lineage"].update({"current_layer_id": sid, "depth": pearl["lineage"]["depth"] + 1,
        "prior_chain_hash": pch, "chain_hash": ch})

    _save(pearl, fp)
    print(f"✓ Merged '{target['name']}' → synthesis {sid}")
    if acc_id: print(f"  Accepted: {acc_id}")
    if rej_ids: print(f"  Rejected: {rej_ids}")

# ===========================================================================
# SURFACE
# ===========================================================================
def cmd_surface(args):
    fp = Path(args.file); pearl = _load(fp)
    s = pearl["surface"]; li = pearl["lineage"]; c = pearl["core"]

    print("=" * 64)
    print("  PEARL v0.2 SESSION SURFACE")
    print("=" * 64)
    print(f"  Objective         : {c['objective']}")
    print(f"  Focus             : {s.get('focus', '—')}")
    print(f"  Understanding     : {s.get('current_understanding', '—')}")
    print(f"  Active Branch     : {s['active_branch_id']}")
    print(f"  Depth             : {li['depth']}")
    print(f"  Chain Hash        : {li['chain_hash'][:24]}...")
    print(f"  Core Immutable    : {'✓ enforced' if pearl.get('_core_hash') else '? (v0.1)'}")
    print(f"  Updated           : {s['updated_at']}")
    print()

    for bn, bk in [("HOT", "hot"), ("WARM", "warm"), ("COLD", "cold")]:
        ids = s[bk]["layer_ids"]
        print(f"  {bn} layers ({len(ids)})")
        for lid in ids:
            l = _layer(pearl, lid)
            if l:
                ph = f" [{l.get('phase')}]" if l.get("phase") else ""
                ev = f" ({len(l.get('evidence_refs', []))} ev)" if l.get("evidence_refs") else ""
                print(f"    [{l['kind']:22s}]{ph} {l['state']['summary'][:50]}{ev}")

    print()
    print("  BRANCHES:")
    for b in pearl["branches"]:
        m = {"active": "●", "candidate": "○", "merged": "✓", "rejected": "✗", "suspended": "◌"}.get(b["status"], "?")
        print(f"    {m} {b['name']} ({b['status']}) — {b.get('intent', '')[:40]}")

    if s.get("open_loops"):
        print(); print("  OPEN LOOPS:")
        for loop in s["open_loops"]: print(f"    ○ {loop}")
    if s.get("current_plan"):
        print(); print("  CURRENT PLAN:")
        for step in s["current_plan"]: print(f"    → {step}")
    print("=" * 64)

# ===========================================================================
# LOAD-CONTEXT
# ===========================================================================
def cmd_load_context(args):
    fp = Path(args.file); pearl = _load(fp)
    budget = args.token_budget * 4 if args.token_budget else float("inf")
    used = 0; blocks = []

    def add(label, content):
        nonlocal used
        sz = len(content)
        if used + sz > budget: return False
        blocks.append({"section": label, "content": content}); used += sz; return True

    add("core", json.dumps(pearl["core"], indent=2))
    u = pearl["surface"].get("current_understanding", "")
    if u: add("operational_brief", u)

    for lid in pearl["surface"]["hot"]["layer_ids"]:
        l = _layer(pearl, lid)
        if l:
            blk = {"state": l["state"]}
            if l.get("phase"): blk["phase"] = l["phase"]
            if l.get("evidence_refs"): blk["evidence"] = l["evidence_refs"]
            if not add(f"hot/{l['kind']}", json.dumps(blk, indent=2)): break

    for lid in pearl["surface"]["warm"]["layer_ids"]:
        l = _layer(pearl, lid)
        if l:
            if not add(f"warm/{l['kind']}", json.dumps(l["state"], indent=2)): break

    loops = pearl["surface"].get("open_loops", [])
    if loops: add("open_loops", json.dumps(loops))
    plan = pearl["surface"].get("current_plan", [])
    if plan: add("current_plan", json.dumps(plan))

    for lid in pearl["surface"]["cold"]["layer_ids"]:
        l = _layer(pearl, lid)
        if l:
            if not add(f"cold/{l['kind']}", l["state"]["summary"]): break

    if args.format == "text":
        for b in blocks: print(f"\n--- {b['section']} ---\n{b['content']}")
    else:
        print(json.dumps(blocks, indent=2))

# ===========================================================================
# UPDATE-SURFACE
# ===========================================================================
def cmd_update_surface(args):
    fp = Path(args.file); pearl = _load(fp)
    if args.focus: pearl["surface"]["focus"] = args.focus
    if args.understanding: pearl["surface"]["current_understanding"] = args.understanding
    if args.plan: pearl["surface"]["current_plan"] = args.plan.split("|")
    if args.add_loop:
        pearl["surface"].setdefault("open_loops", []).append(args.add_loop)
    if args.resolve_loop:
        pearl["surface"]["open_loops"] = [l for l in pearl["surface"].get("open_loops", []) if l != args.resolve_loop]
        pearl["surface"].setdefault("resolved_items", []).append(args.resolve_loop)
    pearl["surface"]["updated_at"] = _now()
    _save(pearl, fp); print("✓ Surface updated.")

# ===========================================================================
# DUMP
# ===========================================================================
def cmd_dump(args):
    print(json.dumps(_load(Path(args.file)), indent=2))

# ===========================================================================
# VERIFY [FEEDBACK #1, #2, #3, #6]
# ===========================================================================
def cmd_verify(args):
    fp = Path(args.file); pearl = _load(fp)
    errors = []; layers = pearl["layers"]

    # Core immutability [#1]
    ch = pearl.get("_core_hash")
    if ch:
        actual = _core_hash(pearl["core"])
        if actual != ch: errors.append(f"CORE TAMPERED: {ch[:24]}... vs {actual[:24]}...")
        else: print("✓ Core immutability: intact")
    else:
        print("⚠ No _core_hash (v0.1 file?) — core check skipped")

    # Layer hashes [#2]
    lok = 0
    for l in layers:
        exp = _hash_jcs(l["state"])
        if exp != l["hashes"]["layer_hash"]:
            errors.append(f"Layer {l['layer_id']}: hash mismatch")
        else: lok += 1
    print(f"✓ Layer hashes: {lok}/{len(layers)} verified")

    # Chain walkthrough [#3]
    if layers:
        g = layers[0]; gc = g["hashes"].get("chain_hash")
        exp_gc = _chain("genesis", g["hashes"]["layer_hash"])
        if gc and gc != exp_gc:
            errors.append("Genesis chain_hash mismatch")
        elif gc:
            running = gc; cv = 1
            for l in layers[1:]:
                lc = l["hashes"].get("chain_hash")
                if lc:
                    exp = _chain(running, l["hashes"]["layer_hash"])
                    if lc != exp:
                        errors.append(f"Chain break at {l['layer_id']}")
                    else: cv += 1
                    running = lc
            print(f"✓ Chain hash: {cv} links verified")

    # Single active branch [#6]
    ac = sum(1 for b in pearl["branches"] if b["status"] == "active")
    if ac > 1: errors.append(f"Multiple active branches: {ac}")
    elif ac == 1: print("✓ Single active branch: enforced")

    if errors:
        print(f"\n✗ FAILED — {len(errors)} error(s):")
        for e in errors: print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"\n✓ All checks passed. {len(layers)} layers, chain intact.")

# ===========================================================================
# CLI
# ===========================================================================
def build_parser():
    p = argparse.ArgumentParser(prog="pearl_session",
        description="PEARL-CHAT v0.2 — Protected · Evolving · Annotation · Resistant · Layering")
    p.add_argument("--file", "-f", default=str(DEFAULT_PEARL_FILE))
    subs = p.add_subparsers(dest="command", required=True)

    s = subs.add_parser("init")
    s.add_argument("--objective", "-o", required=True); s.add_argument("--seed-kind", default="task",
        choices=["chat","task","incident","document","prompt","question","mixed"])
    s.add_argument("--constraints"); s.add_argument("--stakes"); s.add_argument("--owner")
    s.add_argument("--labels"); s.add_argument("--force", action="store_true")

    s = subs.add_parser("add-layer")
    s.add_argument("--kind", "-k", required=True, choices=LAYER_KINDS)
    s.add_argument("--summary", "-s", required=True)
    s.add_argument("--phase", "-p", choices=LAYER_PHASES, default=None)
    s.add_argument("--temperature", "-t", choices=["hot","warm","cold","governance"])
    s.add_argument("--claims"); s.add_argument("--questions"); s.add_argument("--confidence", type=float)
    s.add_argument("--open-loops"); s.add_argument("--resolves"); s.add_argument("--understanding")
    s.add_argument("--payload"); s.add_argument("--evidence"); s.add_argument("--tags")
    s.add_argument("--actor-type", default="assistant"); s.add_argument("--actor-id", default="claude-code")

    s = subs.add_parser("promote"); s.add_argument("--force", action="store_true")
    s = subs.add_parser("compact"); s.add_argument("--summary", "-s")

    s = subs.add_parser("unseal")
    s.add_argument("--layer-ids", required=True); s.add_argument("--reason", required=True)

    s = subs.add_parser("branch")
    s.add_argument("--name", "-n", required=True); s.add_argument("--intent")
    s.add_argument("--switch", action="store_true")

    s = subs.add_parser("merge")
    s.add_argument("--branch-id", "-b", required=True); s.add_argument("--summary", "-s")
    s.add_argument("--accept"); s.add_argument("--reject"); s.add_argument("--switch-to-main", action="store_true")

    subs.add_parser("surface"); subs.add_parser("dump"); subs.add_parser("verify")

    s = subs.add_parser("load-context")
    s.add_argument("--token-budget", type=int); s.add_argument("--format", choices=["json","text"], default="json")

    s = subs.add_parser("update-surface")
    s.add_argument("--focus"); s.add_argument("--understanding"); s.add_argument("--plan")
    s.add_argument("--add-loop"); s.add_argument("--resolve-loop")

    return p

DISPATCH = {"init": cmd_init, "add-layer": cmd_add_layer, "promote": cmd_promote,
    "compact": cmd_compact, "unseal": cmd_unseal, "branch": cmd_branch, "merge": cmd_merge,
    "surface": cmd_surface, "load-context": cmd_load_context, "update-surface": cmd_update_surface,
    "dump": cmd_dump, "verify": cmd_verify}

def main():
    args = build_parser().parse_args()
    DISPATCH[args.command](args)

if __name__ == "__main__":
    main()
