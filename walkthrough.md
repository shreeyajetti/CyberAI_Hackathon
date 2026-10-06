# Walkthrough: running Doctor Nexus and using what's in this folder

## What's in this folder

Get everything, including the original Doctor Nexus repo (linked as a submodule):

```powershell
git clone --recursive https://github.com/shreeyajetti/CyberAI_Hackathon.git
```

```
CyberAI_H/
├── Doctor_Nexus_CyberAI_Hackathon.pptx   ← the presentation (built on the official template)
├── explanation.md                        ← what the project is, in plain English
├── walkthrough.md                        ← this file
├── Doctor-Nexus-HMS/                     ← the cloned GitHub repo (unchanged)
├── local_run/
│   ├── run_audit.py                      ← our local runner for the audit
│   └── recovery_table.csv                ← output from our run (39 rows)
└── deck_assets/
    ├── build_deck.py                     ← script that fills the template (re-run after edits)
    ├── local_run.png                     ← terminal screenshot used on slide 12
    └── run_output.txt                    ← full text output of the run
```

---

## Option A: run it on your laptop (5 minutes, no accounts needed)

The original project only runs inside OpenClaw with a Gemini key and a Telegram bot. To make it easy to demo, `run_audit.py` reads the **same files** from the repo (`agent.yaml` and `hospital_logs.json`) and runs the audit locally.

**You need:** Python 3.9 or newer. Nothing else to install.

### 1. Offline mode (no API key)

```powershell
cd C:\UNI\CyberAI_H\local_run
python run_audit.py
```

You'll see a table like this:

```
Doctor Nexus - Recovery Table (offline mode)
Records checked: 25
Patients with a gap: 25
Leaks found: 39  |  Units missing from bills: 46

Patient Procedure               Missing item          Used Billed Gap  Type              Certainty
P-001   Total Hip Replacement   Titanium Screws          2      1   1  Quantity short    High
P-001   Total Hip Replacement   Ceramic Liner            1      0   1  Not billed at all High
...
```

How to read it:
- **Used**: how many the OT note says were used
- **Billed**: how many are on the bill
- **Gap**: the difference, i.e. what the hospital forgot to charge
- **Certainty**: High for implants and devices, Medium for general consumables

This mode uses simple matching rules, not AI. It's there so you can always demo something, even without internet.

### 2. Save the results to a spreadsheet

```powershell
python run_audit.py --csv recovery_table.csv
```

Open `recovery_table.csv` in Excel.

### 3. AI mode (Gemini, like the original)

1. Get a free API key at https://aistudio.google.com/apikey
2. Set it and run:

```powershell
$env:GEMINI_API_KEY = "paste-your-key-here"
python run_audit.py --llm
```

This sends the repo's agent prompt and the patient logs to Gemini, and prints its Recovery Table with **estimated rupee values**. The default model is `gemini-2.5-flash`. To try another one: `--model gemini-2.0-flash`. We haven't run this mode ourselves (no key was available), so test it before the presentation.

### 4. Use your own data

Make a JSON file in the same shape as `hospital_logs.json`:

```json
[
  { "patient_id": "P-100", "procedure": "Knee Replacement",
    "clinical_notes": "2x Bone Cement (40g) and 1x Tibial Component used.",
    "billing_invoice": { "items": [ {"name": "Bone Cement", "quantity": 1} ] } }
]
```

Then run:

```powershell
python run_audit.py --data my_patients.json
```

Tip for offline mode: write quantities as `2x Item Name` in the notes, like the sample data does.

---

## Option B: run the original setup (OpenClaw + Telegram)

This is how the screenshots in the repo were made. It takes longer to set up.

1. **Install Node.js 22+**, then OpenClaw: `npm install -g openclaw@latest`
2. **Set it up:** `openclaw onboard` and pick Google Gemini as the model provider (paste your Gemini key).
3. **Create a Telegram bot:** in Telegram, message **@BotFather**, send `/newbot`, and copy the token.
4. **Connect Telegram:** `openclaw config set channels.telegram.botToken "YOUR_BOT_TOKEN"`, then restart the gateway and finish the pairing step it shows you.
5. **Add the agent and data:** copy `Doctor-Nexus-HMS/.openclaw/agents/auditor/agent.yaml` into your `~/.openclaw/agents/auditor/`, and `workspace/hospital_logs.json` into your OpenClaw workspace folder. Change the `workspace:` path in `agent.yaml`, since it currently points to the author's Linux home folder (`/home/srikanth/...`).
6. **Chat with it:** message your bot "Audit this", "Which patient bill is the most unfair?" or "Top 3 patient bills and how to recover".

OpenClaw changes quickly, so check https://docs.openclaw.ai/ if a command above doesn't match.

---

## Editing the presentation

Open `Doctor_Nexus_CyberAI_Hackathon.pptx` in PowerPoint. **Before submitting:**

1. **Slide 1:** fill in Team Num, Team Name, Institute, Team Members, Contact and Date, and delete the `<< >>` marks.
2. **Slide 10 (Team Role):** put in member names and tick each person's roles.
3. **Rename the file** as the template asks: `T-<number> - <TeamName>.pptx`.
4. Read the **speaker notes** under each slide; they have talking points and caveats for Q&A.

The slides are normal PowerPoint shapes and native charts, so you can edit any text, box or chart directly. If you'd rather regenerate the deck from the script, edit `deck_assets/build_deck.py` and run `python deck_assets/build_deck.py`. That overwrites the .pptx, so don't do it after making manual edits.

### Slide order (matches the hackathon outline)

| # | Slide | What's on it |
|---|---|---|
| 1 | Title | Project name, theme, team details |
| 2 | Background | How the billing gap happens + HFMA stats |
| 3 | Problem Statement | Real example: 2 stents used, 1 billed |
| 4 | Objectives | 4 goals |
| 5 | Proposed Solution | Read → Match → Flag → Report |
| 6 | Novelty & Show Stopper | Usual checks vs Doctor Nexus |
| 7 | Methodology | Flow diagram of the system |
| 8 | Tech Stack & Budget | Tools used; prototype costs ₹0 |
| 9 | Deliverable / Outcome | Charts from our run: 46 units unbilled |
| 10 | Team Role | Fill in |
| 11 | Screenshots 1 | Telegram bot answering |
| 12 | Screenshots 2 | Our local run |
| 13 | References | 6 sources |
| 14 | Thank You | |

---

## YouTube video (optional, 1–4 minutes)

We can't record or upload the video for you, but here's a plan you can follow with any screen recorder (Windows: **Win + Alt + R** with Xbox Game Bar, or OBS).

**Script (about 3 minutes):**

| Time | Show on screen | Say |
|---|---|---|
| 0:00–0:20 | Title slide | "Hi, we're team ___. Our project is Doctor Nexus, an AI auditor that finds surgical items hospitals forget to bill." |
| 0:20–0:50 | Slide 3 (P-002 example) | "Here's the problem. The surgery note says two stents. The bill says one. That one missing stent is real money, and it happens all the time because bills are typed by hand." |
| 0:50–1:20 | Slide 7 (flow diagram) | "An admin just messages our bot on Telegram. The agent reads the day's notes and bills on the hospital's own machine, Gemini compares them, and a recovery table comes back." |
| 1:20–2:10 | Terminal: `python run_audit.py` | "Here it is running live on 25 patients. It found 39 gaps: 46 units used in surgery but never billed. Red rows are items missing from the bill completely." |
| 2:10–2:40 | Telegram screenshots | "And this is the same agent answering on Telegram: the total leakage and which bills to fix first." |
| 2:40–3:00 | Slide 9 charts → Thank You | "Every patient in our test data had at least one gap. Doctor Nexus catches them before discharge. Thanks for watching." |

Upload to YouTube as **Unlisted** if you don't want it public, and paste the link into the hackathon form.

---

## Before you submit: please read

The hackathon guidelines say **"Don't use AI for ppt generation"** (both in the guidelines PDF and on the template's first slide). This deck was put together with AI help. Before submitting, go through it, rewrite anything in your own words, and make sure your team is comfortable with it under the rules. If you're unsure, ask the organisers (CyberAI2026@theamse.org).

Also, Doctor Nexus is someone else's public project (github.com/srikanth-hn). If that isn't your teammate's repo, credit the author and check that you're allowed to present it.
