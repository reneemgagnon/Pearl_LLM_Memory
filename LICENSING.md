# PEARL™ Licensing

PEARL™ is a trademark of Maple Brain Healthcare Inc.

This project uses a **three-layer licensing structure** to balance open
adoption of the `.pearl` format with commercial sustainability.

---

## Layer 1 — Format Specification & Documentation

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Scope:** everything under `references/` and all prose documentation
describing the `.pearl` format, including:

- `references/pearl-chat-spec.md`
- `references/pearl-chat-schema.json`
- Format examples and diagrams

Machine-readable schema files in `references/` are part of the open
specification and may be freely implemented by any compatible tool.

**Why CC BY 4.0:** easy reuse with attribution preserved, widely understood
for documentation and specifications. Per Creative Commons guidance, CC
licenses are not recommended for software — this layer covers prose,
specification, and schema artifacts only.

You are free to share and adapt these materials for any purpose, including
commercial, provided you give appropriate credit.

See [`LICENSE.docs`](LICENSE.docs) for the license text.

---

## Layer 2 — Reference Implementation, SDK & Validator

**License:** [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

**Scope:** all source code in `scripts/`, agent configurations, and tooling,
including:

- `scripts/pearl_session.py` (session engine)
- `agents/` (agent integration configs)
- `SKILL.md` (skill definition / integration glue)
- Any future SDK, CLI, validator, or MCP adapter code

**Why Apache-2.0:** fastest adoption path, explicit patent grant,
enterprise-safe, and permissive enough that governments, vendors, and
integrators will actually use it. Apache-2.0 also keeps trademarks out of
the license grant, preserving commercial brand control.

See [`LICENSE`](LICENSE) for the full text.

---

## Layer 3 — Enterprise Platform (Proprietary)

**License:** Commercial EULA (not included in this repository)

**Scope:** the following components, when offered by Maple Brain
Healthcare Inc. or its licensees:

- Orchestration / control-plane services
- Appliance software and firmware
- Compliance workflow modules
- Admin UI / governance dashboard
- Managed clustering and HSM integrations
- Certification packs, support contracts, and hardening profiles

Contact **Maple Brain Healthcare Inc.** for enterprise licensing inquiries.

---

## Quick Reference

| Layer | Artifacts | License | File |
|-------|-----------|---------|------|
| Specification & docs | `references/*`, format prose | CC BY 4.0 | [`LICENSE.docs`](LICENSE.docs) |
| Reference implementation | `scripts/*`, `agents/*`, `SKILL.md` | Apache-2.0 | [`LICENSE`](LICENSE) |
| Enterprise platform | Control plane, compliance, admin UI | Proprietary EULA | Not in this repo |

---

## Trademark Policy

See [`TRADEMARKS.md`](TRADEMARKS.md) for full details.
