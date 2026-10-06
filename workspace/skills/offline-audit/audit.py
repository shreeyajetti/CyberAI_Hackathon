"""
Offline billing check for Doctor Nexus (no AI, no internet).

Reads OT notes + bills from a JSON file and lists every item that was used
in theatre but is missing from the bill, or billed in a smaller quantity.
The counts come from code, so they're exact, unlike numbers an AI model adds up.

  python audit.py                      -> checks ../../hospital_logs.json
  python audit.py other_logs.json      -> checks another file
  python audit.py --patient P-004      -> one patient only
  python audit.py --json               -> machine-readable output
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "hospital_logs.json"

# Words that end an item name in a clinical note ("2x Onyx Stents deployed in LAD")
STOP_WORDS = r"(?:and|used|deployed|utilized|implanted|for|in|today|injections?)"
ITEM_RE = re.compile(r"(\d+)x\s+(.+?)(?=\s+" + STOP_WORDS + r"\b|[,.;]|$)", re.I)
SIZE_RE = re.compile(r"^\s*\d[\d.\-]*\s*(?:mm|cm|g|f|d)?\s+", re.I)

# Implants / high-value devices -> "High" certainty leak
HIGH_VALUE = ("screw", "stent", "graft", "pacemaker", "port", "prosthesis", "component",
              "plate", "coil", "mesh", "rod", "iol", "liner", "lead", "button", "balloon",
              "catheter", "patch", "head", "stem", "cement", "endobutton", "tack")


def tokens(text):
    words = re.findall(r"[a-z0-9\-]+", text.lower())
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words}


def parse_note(note):
    """Pull (quantity, item name) pairs out of a free-text OT note."""
    clean = re.sub(r"\([^)]*\)", "", note)  # drop sizes in brackets, e.g. (3.5mm)
    return [{"item": SIZE_RE.sub("", name).strip(), "qty": int(qty)} for qty, name in ITEM_RE.findall(clean)]


def match_billed(item_name, billed):
    """A bill line matches a note item when all of its words appear in the note item."""
    item_tok = tokens(item_name)
    return next((line for line in billed if tokens(line["name"]) <= item_tok), None)


def audit(records):
    findings = []
    for r in records:
        billed = r["billing_invoice"]["items"]
        for used in parse_note(r["clinical_notes"]):
            line = match_billed(used["item"], billed)
            billed_qty = line["quantity"] if line else 0
            gap = used["qty"] - billed_qty
            if gap <= 0:
                continue
            findings.append({
                "patient_id": r["patient_id"],
                "procedure": r["procedure"],
                "item": used["item"],
                "used": used["qty"],
                "billed": billed_qty,
                "missing": gap,
                "type": "not billed" if billed_qty == 0 else "billed short",
                "certainty": "High" if any(k in used["item"].lower() for k in HIGH_VALUE) else "Medium",
            })
    return findings


def report(findings, n_records):
    if not findings:
        return f"Checked {n_records} patients. Every bill matches its notes."
    lines = [
        f"Checked {n_records} patients",
        f"Patients with a gap: {len({f['patient_id'] for f in findings})}",
        f"Gaps: {len(findings)} ({sum(f['type'] == 'not billed' for f in findings)} not billed, "
        f"{sum(f['type'] == 'billed short' for f in findings)} billed short)",
        f"Units missing from bills: {sum(f['missing'] for f in findings)}",
    ]
    last = None
    for f in findings:
        if f["patient_id"] != last:
            lines.append(f"\n{f['patient_id']} | {f['procedure']}")
            last = f["patient_id"]
        lines.append(f"  - {f['item']}: used {f['used']}, billed {f['billed']}, "
                     f"missing {f['missing']} ({f['type']}, {f['certainty']})")
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Doctor Nexus offline billing check")
    ap.add_argument("data", nargs="?", default=str(DEFAULT_DATA), help="patient log JSON file")
    ap.add_argument("--patient", help="only check this patient ID, e.g. P-004")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args()

    path = Path(args.data)
    if not path.exists():
        sys.exit(f"Can't find '{path}'.")
    records = json.loads(path.read_text(encoding="utf-8"))
    if args.patient:
        records = [r for r in records if r["patient_id"].lower() == args.patient.lower()]
        if not records:
            sys.exit(f"No patient with ID {args.patient}.")

    findings = audit(records)
    print(json.dumps(findings, indent=1) if args.json else report(findings, len(records)))


if __name__ == "__main__":
    main()
