---
name: offline-audit
description: Exact, rule-based check of OT notes against bills. Lists items used in surgery but missing from the bill or billed short. Use before any audit answer so counts are correct.
metadata: { "openclaw": { "requires": { "bins": ["python"] } } }
---

# Offline audit

A small Python checker that compares each patient's `clinical_notes` with their `billing_invoice`
and prints every gap. It runs on this machine with no AI and no internet, so its counts are exact.

## When to use it

- Any time the user asks for an audit, leakage, missing items, or "which bills are wrong".
- Before you quote any number of missing items, patients or units.
- When the user asks about one patient (use `--patient`).

## How to run it

Run from the workspace folder with the `exec` tool:

```
python skills/offline-audit/audit.py
python skills/offline-audit/audit.py --patient P-004
python skills/offline-audit/audit.py <path-to-other-logs.json>
```

Add `--json` if you want structured output to work with.

## How to use the output

- Treat the checker's item names, quantities and gap counts as the source of truth. Don't change them.
- The checker has no prices. If you add rupee values, label them clearly as estimates, give a unit
  price per item, and work out totals step by step (unit price x missing quantity, then add the rows).
- If an item in the notes is something the checker missed (e.g. an implied item like bone cement for a
  hip replacement), you may add it, but mark it as "AI-flagged, not in notes".
