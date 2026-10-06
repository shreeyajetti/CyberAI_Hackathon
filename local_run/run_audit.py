"""
Local runner for Doctor Nexus HMS.

The original project runs inside OpenClaw (agent gateway) + Gemini + a Telegram bot.
This script lets you run the same audit on your own laptop:

  python run_audit.py              -> offline mode, no API key needed (rule-based audit)
  python run_audit.py --llm        -> sends the same data + the agent's system prompt to Gemini
                                      (needs GEMINI_API_KEY set in your environment)

It reads the agent prompt from .openclaw/agents/auditor/agent.yaml and the patient
records from workspace/hospital_logs.json inside the cloned repo.
"""
import argparse
import csv
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parent / "Doctor-Nexus-HMS"

# Words that end an item name in a clinical note ("2x Onyx Stents deployed in LAD")
STOP_WORDS = r"(?:and|used|deployed|utilized|implanted|for|in|today|injections?)"
ITEM_RE = re.compile(r"(\d+)x\s+(.+?)(?=\s+" + STOP_WORDS + r"\b|[,.;]|$)", re.I)
SIZE_RE = re.compile(r"^\s*\d[\d.\-]*\s*(?:mm|cm|g|f|d)?\s+", re.I)

# Items that are implants / high-value devices -> "High" certainty leak
HIGH_VALUE = ("screw", "stent", "graft", "pacemaker", "port", "prosthesis", "component",
              "plate", "coil", "mesh", "rod", "iol", "liner", "lead", "button", "balloon",
              "catheter", "patch", "head", "stem", "cement", "endobutton", "tack")


def tokens(text):
    words = re.findall(r"[a-z0-9\-]+", text.lower())
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words}


def parse_note(note):
    """Pull (quantity, item name) pairs out of a free-text OT note."""
    clean = re.sub(r"\([^)]*\)", "", note)  # drop sizes in brackets, e.g. (3.5mm)
    items = []
    for qty, name in ITEM_RE.findall(clean):
        name = SIZE_RE.sub("", name).strip()
        items.append({"item": name, "qty": int(qty)})
    return items


def match_billed(item_name, billed):
    """A bill line matches a note item when all of its words appear in the note item."""
    item_tok = tokens(item_name)
    for line in billed:
        if tokens(line["name"]) <= item_tok:
            return line
    return None


def offline_audit(records):
    findings = []
    for r in records:
        billed = r["billing_invoice"]["items"]
        for used in parse_note(r["clinical_notes"]):
            line = match_billed(used["item"], billed)
            billed_qty = line["quantity"] if line else 0
            gap = used["qty"] - billed_qty
            if gap <= 0:
                continue
            high = any(k in used["item"].lower() for k in HIGH_VALUE)
            findings.append({
                "patient_id": r["patient_id"],
                "procedure": r["procedure"],
                "item": used["item"],
                "used": used["qty"],
                "billed": billed_qty,
                "missing": gap,
                "type": "Not billed at all" if billed_qty == 0 else "Quantity short",
                "certainty": "High" if high else "Medium",
            })
    return findings


def print_table(findings, n_records):
    print(f"\nDoctor Nexus - Recovery Table (offline mode)\n{'=' * 44}")
    print(f"Records checked: {n_records}")
    print(f"Patients with a gap: {len({f['patient_id'] for f in findings})}")
    print(f"Leaks found: {len(findings)}  |  Units missing from bills: {sum(f['missing'] for f in findings)}\n")
    head = f"{'Patient':<8}{'Procedure':<30}{'Missing item':<34}{'Used':>5}{'Billed':>7}{'Gap':>5}  {'Type':<18}{'Certainty'}"
    print(head)
    print("-" * len(head))
    for f in findings:
        print(f"{f['patient_id']:<8}{f['procedure'][:29]:<30}{f['item'][:33]:<34}"
              f"{f['used']:>5}{f['billed']:>7}{f['missing']:>5}  {f['type']:<18}{f['certainty']}")
    print("\nNote: the repo has no hospital price list, so this mode counts missing units."
          "\nUse --llm to let the model estimate rupee values the way the original agent does.")


def read_system_prompt(agent_yaml):
    text = agent_yaml.read_text(encoding="utf-8")
    m = re.search(r"system_prompt:\s*\|\n((?:[ \t]+.*\n?)+)", text)
    return "\n".join(l.strip() for l in m.group(1).splitlines()) if m else ""


def llm_audit(records, system_prompt, model):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text":
            "Audit this. Here are today's hospital logs:\n" + json.dumps(records, indent=1)}]}],
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.load(resp)
    print(out["candidates"][0]["content"]["parts"][0]["text"])


def main():
    ap = argparse.ArgumentParser(description="Run the Doctor Nexus billing audit locally")
    ap.add_argument("--repo", default=str(DEFAULT_REPO), help="path to the cloned Doctor-Nexus-HMS repo")
    ap.add_argument("--data", help="patient log JSON (default: <repo>/workspace/hospital_logs.json)")
    ap.add_argument("--llm", action="store_true", help="use Gemini instead of the offline rules")
    ap.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name for --llm")
    ap.add_argument("--csv", help="also save the offline recovery table to this CSV file")
    args = ap.parse_args()

    repo = Path(args.repo)
    data = Path(args.data) if args.data else repo / "workspace" / "hospital_logs.json"
    records = json.loads(data.read_text(encoding="utf-8"))

    if args.llm:
        prompt = read_system_prompt(repo / ".openclaw" / "agents" / "auditor" / "agent.yaml")
        llm_audit(records, prompt, args.model)
        return

    findings = offline_audit(records)
    print_table(findings, len(records))
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)
        print(f"\nSaved {len(findings)} rows to {args.csv}")


if __name__ == "__main__":
    main()
