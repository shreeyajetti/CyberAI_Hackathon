# Doctor Nexus HMS, explained simply

Repo: https://github.com/srikanth-hn/Doctor-Nexus-HMS

## Which hackathon problem statement is this?

**AI and its applied domain → Healthcare & Life Sciences.**

Doctor Nexus uses AI inside a hospital to read surgery notes and check them against patient bills. That makes it healthcare, with "predictive analytics" and "AI-powered diagnostics" being the closest listed examples.

It also overlaps with **Finance, Retail & Business (fraud detection)**, because at heart it's a billing audit tool. If the team wants to pitch the money side more, that theme works as a second choice.

It is **not** a Cybersecurity & Digital Trust project. It does take patient privacy seriously, since raw files stay on the hospital's machine, but it doesn't do intrusion detection, phishing filtering or identity checks.

---

## The problem, in plain words

Picture a heart operation. During the surgery, the doctor puts in two small metal tubes (stents) to keep an artery open. A nurse writes in the operation notes: *"2x Onyx Stents deployed."*

A few hours later, someone in the billing office makes the patient's bill. They're busy and working from handwritten or typed notes. They enter *"Onyx Stent × 1."*

That's one stent the hospital paid for, used on the patient, and never charged for. Stents, screws, artificial joints and grafts can cost thousands each. Across hundreds of surgeries a month, that adds up to a lot of lost money.

In the US, the Healthcare Financial Management Association (HFMA) estimates hospitals lose **1–5% of their net revenue** to charges that never get captured. The project's README says Indian tertiary hospitals lose 15–20% of surgical revenue this way, but it gives no source for that number, so we haven't used it in the slides.

**Why doesn't anyone catch it?** Checking every bill against every surgery note by hand is slow and boring. Simple computer checks don't work well either, because the notes are messy. One person writes "Ti screw", another writes "Titanium Interference Screw", and a basic program thinks those are two different things.

## What Doctor Nexus does

Doctor Nexus is an **AI assistant you chat with on Telegram**. A hospital admin sends it a message like *"Audit this"* or *"Show me leakage for today's ortho surgeries"*. It then:

1. **Reads** the day's operation-theatre (OT) notes and the matching bills.
2. **Matches** each item in the notes to the bill, even when the names are written differently.
3. **Flags** anything that was used but not billed, or billed in a smaller quantity.
4. **Reports** back a "Recovery Table": patient ID, missing item, and estimated value.

The point is to catch this **before the patient is discharged**, while the bill can still be fixed.

## How it's built

The project is small. There's no app code in the repo, just configuration, sample data and docs. That's because it's built on a ready-made agent tool called **OpenClaw**.

| Piece | What it is | What it does here |
|---|---|---|
| **OpenClaw** | Open-source "agent gateway" you run on your own computer | Hosts the Doctor Nexus agent, gives it a safe folder (workspace) to read files from, and connects it to Telegram |
| **Gemini 2.0 Flash** | Google's AI model | Does the actual thinking: reads the notes, compares them to the bills, spots gaps |
| **Telegram bot** | A chat bot | The screen the admin uses to ask questions and get answers |
| **`agent.yaml`** | The agent's instructions | Tells the AI: "You are a senior auditor for Indian hospitals. Find implants, stents and special drugs in the notes that are missing from the bill. Output a Recovery Table." |
| **`hospital_logs.json`** | Sample data | 25 made-up patients, each with a procedure, free-text OT notes, and a bill |

### Files in the repo

```
Doctor-Nexus-HMS/
├── .openclaw/agents/auditor/agent.yaml   ← the agent's instructions (its "job description")
├── workspace/hospital_logs.json          ← 25 sample patients: notes + bills
├── docs/HLD.jpg                          ← architecture diagram
├── docs/audi_flow.md                     ← step-by-step logic the agent follows
├── docs/Screenshot_*.png                 ← the bot answering on Telegram
└── README.md
```

### How a request flows

```
Admin (phone) ──"Audit this"──▶ Telegram bot
                                     │
                                     ▼
              ┌──────── Hospital's own computer (OpenClaw) ────────┐
              │  Doctor Nexus agent ──read_file──▶ hospital_logs.json│
              │        │                                            │
              └────────┼────────────────────────────────────────────┘
                       ▼  (encrypted API call)
                  Gemini (cloud) — compares notes vs bills
                       │
                       ▼
              Recovery Table ──▶ back to the admin on Telegram
```

**The privacy idea ("local-first"):** the hospital's raw records stay on the hospital's own machine inside OpenClaw's workspace. Only the text the AI needs to reason about goes to Gemini. In a real hospital you'd also want an audit log and access controls; the architecture diagram shows these as a planned "HIPAA audit trail".

### The audit logic (from `docs/audi_flow.md`)

- **Understand names:** "Ti Screw" in a note = "Titanium Interference Screw" on a bill.
- **Recognise brands:** "Hem-o-lok" and "Echelon" are expensive surgical consumables.
- **Spot implied items:** a hip replacement almost always needs bone cement, so check for it even if the note doesn't mention it.
- **Check three things:** Is the quantity the same? Is the item on the bill at all? Does the billed procedure match what was actually used?
- **Rate certainty:** a missing implant is "high certainty"; a missing pack of sutures is "low".

## What we found when we ran it

OpenClaw needs a Gemini key and a Telegram bot to run, so we wrote a small local runner (`local_run/run_audit.py`). It does the same check on your laptop with **no API key**, and can also call Gemini if you give it one. See `walkthrough.md`.

On the 25 sample patients in the repo:

| Result | Number |
|---|---|
| Patients with at least one gap | **25 of 25** |
| Gaps found | **39** |
| Items used in theatre | 77 units |
| Items on the bills | 31 units |
| Units missing from bills | **46** |
| Gaps that were never billed at all | 24 |
| Gaps that were billed short (e.g. 2 used, 1 billed) | 15 |
| Gaps involving implants/devices (high certainty) | 29 |

The sample data was clearly written so that every patient has a gap. That's fine for a demo, but real hospital data would have far fewer.

## Honest limitations (worth knowing before Q&A)

- **No price list.** The repo has no hospital price list, so the rupee amounts in the Telegram screenshots (e.g. ₹3,31,300 total) are the AI's own estimates, not real prices.
- **The screenshots don't match the current data.** They mention patients P-102, P-123 and P-114, which aren't in `hospital_logs.json` (that file has P-001 to P-025). They seem to come from an earlier, different dataset.
- **Prototype only.** There's no link to a real hospital billing system yet; the data is a JSON file.
- **Data still leaves the building for reasoning.** "Local-first" means raw files stay local, but the note text does get sent to Gemini. A real hospital would need a data agreement, or a model that runs fully on-site.
- **AI can be wrong.** Flags should be reviewed by a billing person before a bill is changed. It's an assistant, not an automatic biller.

## Glossary

| Term | Meaning |
|---|---|
| **OT** | Operation theatre (operating room) |
| **HMS** | Hospital Management System, the software hospitals use for records and billing |
| **Tertiary care hospital** | A large, specialist hospital that does complex surgeries |
| **Revenue leakage** | Money a hospital should have charged but didn't |
| **Charge capture** | The process of making sure everything used gets onto the bill |
| **Agent** | An AI that can follow instructions and use tools (like reading a file) by itself |
| **LLM** | Large Language Model, the type of AI behind ChatGPT and Gemini |
| **OpenClaw** | Open-source software that runs AI agents on your own machine and connects them to chat apps |

## References

1. Doctor Nexus HMS, GitHub. https://github.com/srikanth-hn/Doctor-Nexus-HMS
2. JTS Health Partners, "How Much Is Your Hospital Losing Through a Poor Charge Capture Process?" (cites HFMA, 1–5% of net revenue). https://jtshealthpartners.com/blog/how-much-is-your-hospital-losing-through-poor-charge-capture-process/
3. Commure, "Charge Capture in Healthcare: What It Is, Why Revenue Leaks, and How AI Fixes It" (cites HFMA; Novant Health recovered $7.5M in 15 months). https://www.commure.com/blog/charge-capture-in-healthcare-what-it-is-why-revenue-leaks-and-how-ai-fixes-it
4. OpenClaw documentation. https://docs.openclaw.ai/
5. Gemini API documentation. https://ai.google.dev/gemini-api/docs
6. Telegram Bot API. https://core.telegram.org/bots/api
