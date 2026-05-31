# 🏴‍☠️ First Mate — Personal Dev Agent
### Built for Pirates of the Coral-bean Hackathon (WeMakeDevs)

> Query GitHub as SQL via Coral. Summarize with Claude. Know what to work on today.

---

## What This Does

**First Mate** is a personal productivity agent that:
1. Uses **Coral SQL** to query your GitHub repo (open PRs, issues, recent commits)
2. Feeds the data to **Claude** to generate a smart daily brief
3. Lets you **chat** with the agent for follow-up questions
4. Shows everything in a **beautiful web dashboard**

---

## Windows Setup (Step by Step)

### STEP 1: Install Python
1. Go to https://python.org/downloads
2. Download Python 3.11 or later
3. ✅ CHECK "Add Python to PATH" during install
4. Open Command Prompt and verify: `python --version`

### STEP 2: Install Coral CLI
1. Go to https://github.com/withcoral/coral/releases/latest
2. Download: `coral-x86_64-pc-windows-msvc.zip`
3. Unzip it — you'll get `coral.exe`
4. Move `coral.exe` to `C:\coral\`
5. Add to PATH:
   - Press Win + S → "Environment Variables"
   - Click "Environment Variables"
   - Under System Variables → PATH → Edit → New → type `C:\coral`
   - Click OK → OK → OK
6. Open a NEW Command Prompt and verify: `coral --version`

### STEP 3: Get Anthropic API Key
1. Go to https://console.anthropic.com
2. Sign up / Log in
3. Go to API Keys → Create new key
4. Copy the key (starts with `sk-ant-...`)
5. In Command Prompt, set the environment variable:
   ```
   setx ANTHROPIC_API_KEY "sk-ant-your-key-here"
   ```
6. Close and reopen Command Prompt for it to take effect

### STEP 4: Install Python dependencies
```
cd path\to\coral-agent\backend
pip install -r requirements.txt
```

### STEP 5: (Optional) Connect GitHub for Live Mode
Only needed if you want real data instead of demo mode:
```
coral source add --interactive github
```
It will ask for your GitHub Personal Access Token.
Get one at: https://github.com/settings/tokens (needs `repo` and `read:user` scopes)

### STEP 6: Run the Agent

**Option A — Demo Mode (no Coral setup needed, great for testing):**
```
cd path\to\coral-agent
python backend\agent.py --demo
```

**Option B — Web Dashboard (full experience):**
```
cd path\to\coral-agent
python backend\server.py
```
Then open your browser to: http://localhost:5000

---

## Project Structure

```
coral-agent/
├── backend/
│   ├── agent.py          # Core agent logic (Coral + Claude)
│   ├── server.py         # Flask API server
│   └── requirements.txt  # Python dependencies
├── frontend/
│   └── index.html        # Beautiful web dashboard
└── README.md
```

---

## How Coral Powers This

Instead of calling the GitHub API directly, we use Coral SQL:

```sql
-- Get open PRs
SELECT number, title, state, updated_at
FROM github.pulls
WHERE owner = 'your-org' AND repo = 'your-repo' AND state = 'open'
ORDER BY updated_at DESC LIMIT 10;

-- Get open issues
SELECT number, title, created_at, labels
FROM github.issues
WHERE owner = 'your-org' AND repo = 'your-repo' AND state = 'open';

-- Cross-source join (add Sentry, Slack, etc.)
SELECT g.title, s.error_message
FROM github.pulls g
JOIN sentry.issues s ON s.first_seen >= g.merged_at
WHERE s.level = 'fatal';
```

Coral handles auth, pagination, and rate limits. Your agent just writes SQL.

---

## Judging Criteria Coverage

| Criterion | How We Address It |
|---|---|
| 🏴‍☠️ Potential Impact | Helps any developer know what to work on daily |
| ⚓ Creativity | SQL-powered agent with beautiful chat UI |
| 🗺️ Learning & Growth | Built Coral source integration from scratch on Windows |
| ⚔️ Technical Implementation | Flask API + Coral CLI + Claude MCP-ready |
| 🎨 Aesthetics & UX | Dark terminal aesthetic dashboard |
| 🪸 Best Use of Coral | Core SQL cross-source queries demonstrated |

---

## Demo Script (for submission video)

1. Open http://localhost:5000
2. Click "Try Demo"
3. Click "🚀 Launch First Mate"
4. Show the SQL queries in the Coral SQL panel
5. Show Claude's daily brief
6. Ask in chat: "Which PR should I review first?"
7. Ask: "What bugs are most urgent?"

---

## Built With
- [Coral](https://withcoral.com) — SQL layer for APIs
- [Anthropic Claude](https://anthropic.com) — AI summarization
- Python + Flask — Backend API
- Vanilla HTML/CSS/JS — Frontend dashboard
