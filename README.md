# Missing Stitch: AI billing auditor on OpenClaw

Hospitals lose money when items used in surgery (stents, screws, grafts) never make it onto the patient's bill.
Missing Stitch is an OpenClaw agent you message on Telegram. It reads the day's OT notes and bills and replies with a
Recovery Table: which patient, which item is missing, and roughly what it's worth.

Built on [Doctor Nexus HMS](https://github.com/srikanth-hn/Doctor-Nexus-HMS) by srikanth-hn (agent prompt, sample
data, architecture and screenshots). **Our addition is the offline audit skill**: a small Python checker the agent
runs first, so counts of missing items come from code instead of the AI's own arithmetic.

## What's here

```
workspace/                         OpenClaw workspace (point OpenClaw here)
├── AGENTS.md                      the auditor's instructions (original prompt + "run the checker first")
├── hospital_logs.json             25 sample patients: OT notes + bills (original data)
└── skills/offline-audit/          our add-on
    ├── SKILL.md                   tells the agent when and how to use it
    └── audit.py                   exact, rule-based check (no AI, no internet)
docs/                              original architecture diagram, audit logic and screenshots
```

## How it works

1. An admin messages the bot on Telegram, e.g. *"Audit this"*.
2. OpenClaw (running on the hospital's machine) hands it to the Missing Stitch agent.
3. The agent runs `audit.py`, which lists every item used but not billed, with exact quantities.
4. Gemini adds what code can't: estimated rupee values, implied items, and how to recover the money.
5. The reply goes back to Telegram.

Raw patient files stay on the local machine. Only the text needed for reasoning is sent to Gemini.

## Setup

Needs Node.js 24.16+ (or 26.1+), Python 3.9+, a [Gemini API key](https://aistudio.google.com/apikey) and a Telegram
bot token from [@BotFather](https://t.me/BotFather) (`/newbot`).

**1. Install OpenClaw**

```powershell
npm install -g --allow-scripts=@google/genai,esbuild,koffi,protobufjs,openclaw openclaw@latest
```

**2. Copy the workspace out of the repo.** OpenClaw tags its prompts with the GitHub URL when the workspace sits
inside a git repo, and the model sometimes echoes that tag into replies. Running from a copy avoids it. Re-run this
after editing anything in `workspace/`.

```powershell
Copy-Item -Recurse -Force workspace "$HOME\.openclaw\workspace-missing-stitch"
```

**3. Onboard with Gemini**

```powershell
openclaw onboard --non-interactive --accept-risk --mode local --auth-choice gemini-api-key `
  --gemini-api-key "<GEMINI_KEY>" --workspace "$HOME/.openclaw/workspace-missing-stitch" `
  --agent-name "Missing Stitch" --skip-channels --skip-daemon --skip-bootstrap
openclaw models set google/gemini-3.1-flash-lite
openclaw models fallbacks add google/gemini-flash-latest
```

`gemini-3.1-flash-lite` has the most generous free-tier limits. Larger models allow only a handful of requests per
minute or day, and one agent reply uses several.

**4. Lock the agent down and connect Telegram.** Save this as `setup.json5` (use forward slashes in paths), then run
`openclaw config patch --file setup.json5`:

```json5
{
  agents: { entries: { "missing-stitch": {
    cwd: "C:/Users/<you>/.openclaw/workspace-missing-stitch",
    skills: ["offline-audit"],          // only our skill
    tools: { allow: ["read", "exec"] }, // read the logs, run the checker
    thinkingDefault: "low",             // flash models reject "minimal"
  } } },
  tools: { exec: { mode: "allowlist", strictInlineEval: true } },
  plugins: { entries: { "memory-core": { enabled: false } } }, // don't keep patient data between chats
  channels: { telegram: { enabled: true, botToken: "<BOT_TOKEN>", dmPolicy: "pairing" } },
}
```

Allow the agent to run Python (and nothing else):

```powershell
openclaw approvals allowlist add --agent missing-stitch (Get-Command python).Source
```

**5. Run it**

```powershell
cd $HOME
openclaw gateway run
```

Message your bot on Telegram. It replies with a pairing code. Approve it from another terminal with
`openclaw pairing approve telegram <CODE>`, then try *"Audit this"*. The bot works while the gateway is running.

Try the checker on its own:

```powershell
cd workspace
python skills/offline-audit/audit.py                 # all patients
python skills/offline-audit/audit.py --patient P-004  # one patient
```

On the sample data it finds 39 gaps across all 25 patients: 77 units used in theatre, 31 billed, 46 missing.
