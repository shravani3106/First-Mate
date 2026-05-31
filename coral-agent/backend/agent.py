"""
Coral Personal Agent - Backend
Connects GitHub + Notion via Coral SQL and uses Claude to summarize.
Run: python agent.py
"""

import subprocess
import json
import os
import sys
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = """You are a personal productivity assistant called "First Mate".
You help developers understand what they should work on by analyzing their GitHub activity.

You have access to real data fetched from GitHub via Coral SQL.
When given raw data, summarize it clearly and helpfully:
- List open PRs that need attention
- Highlight issues assigned to the user
- Note any recent activity worth knowing
- Give a clear "Top 3 things to do today" at the end

Be concise, friendly, and actionable. Use emojis sparingly for readability.
Format your response in clean markdown."""

def run_coral_query(query: str) -> dict:
    """Run a Coral SQL query and return results."""
    try:
        result = subprocess.run(
            ["coral", "sql", "--output", "json", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return {"success": True, "data": result.stdout, "error": None}
        else:
            return {"success": False, "data": None, "error": result.stderr}
    except FileNotFoundError:
        return {"success": False, "data": None, "error": "Coral CLI not found. Please install Coral first."}
    except subprocess.TimeoutExpired:
        return {"success": False, "data": None, "error": "Query timed out after 30 seconds."}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def fetch_github_data(github_username: str, github_repo_owner: str, github_repo: str) -> dict:
    """Fetch relevant GitHub data using Coral SQL."""
    results = {}

    # Open PRs
    pr_query = f"""
    SELECT number, title, state, created_at, updated_at
    FROM github.pulls
    WHERE owner = '{github_repo_owner}' AND repo = '{github_repo}' AND state = 'open'
    ORDER BY updated_at DESC
    LIMIT 10
    """
    results["open_prs"] = run_coral_query(pr_query)

    # Open issues assigned to user
    issues_query = f"""
    SELECT number, title, state, created_at, labels
    FROM github.issues
    WHERE owner = '{github_repo_owner}' AND repo = '{github_repo}' AND state = 'open'
    ORDER BY created_at DESC
    LIMIT 10
    """
    results["open_issues"] = run_coral_query(issues_query)

    # Recent commits
    commits_query = f"""
    SELECT sha, message, author__name, committed_at
    FROM github.commits
    WHERE owner = '{github_repo_owner}' AND repo = '{github_repo}'
    ORDER BY committed_at DESC
    LIMIT 5
    """
    results["recent_commits"] = run_coral_query(commits_query)

    return results

def ask_agent(data: dict, user_question: str, conversation_history: list) -> str:
    """Send data + question to Claude and get a response."""
    
    # Build context from fetched data
    context_parts = []
    
    for key, result in data.items():
        if result["success"] and result["data"]:
            context_parts.append(f"=== {key.replace('_', ' ').upper()} ===\n{result['data']}")
        elif result["error"]:
            context_parts.append(f"=== {key.replace('_', ' ').upper()} ===\nError: {result['error']}")
    
    context = "\n\n".join(context_parts)
    
    # Add user message with context
    full_message = f"""Here is the latest data from GitHub (fetched via Coral SQL):

{context}

User question: {user_question}"""
    
    conversation_history.append({
        "role": "user",
        "content": full_message
    })
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    reply = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })
    
    return reply

def demo_with_mock_data() -> dict:
    """Return mock data for demo purposes when Coral isn't set up."""
    return {
        "open_prs": {
            "success": True,
            "data": json.dumps([
                {"number": 42, "title": "feat: add dark mode support", "state": "open", "created_at": "2026-05-30T10:00:00Z", "updated_at": "2026-05-31T08:00:00Z"},
                {"number": 41, "title": "fix: resolve login bug on mobile", "state": "open", "created_at": "2026-05-29T14:00:00Z", "updated_at": "2026-05-30T16:00:00Z"},
                {"number": 39, "title": "docs: update README with API examples", "state": "open", "created_at": "2026-05-28T09:00:00Z", "updated_at": "2026-05-28T11:00:00Z"},
            ], indent=2)
        },
        "open_issues": {
            "success": True,
            "data": json.dumps([
                {"number": 105, "title": "Performance regression in dashboard loading", "state": "open", "created_at": "2026-05-31T07:00:00Z", "labels": ["bug", "priority-high"]},
                {"number": 103, "title": "Add export to CSV feature", "state": "open", "created_at": "2026-05-30T12:00:00Z", "labels": ["enhancement"]},
                {"number": 98, "title": "Write unit tests for auth module", "state": "open", "created_at": "2026-05-27T10:00:00Z", "labels": ["testing"]},
            ], indent=2)
        },
        "recent_commits": {
            "success": True,
            "data": json.dumps([
                {"sha": "a1b2c3d", "message": "fix: handle null user sessions correctly", "author__name": "You", "committed_at": "2026-05-31T06:00:00Z"},
                {"sha": "e4f5g6h", "message": "refactor: split UserService into smaller modules", "author__name": "teammate", "committed_at": "2026-05-30T20:00:00Z"},
            ], indent=2)
        }
    }

def main():
    print("\n🏴‍☠️  First Mate — Your Personal Dev Agent (powered by Coral + Claude)\n")
    print("=" * 60)
    
    # Check for demo mode
    demo_mode = "--demo" in sys.argv
    
    if demo_mode:
        print("🎭 Running in DEMO MODE (using mock data)\n")
        github_username = "demo-user"
        repo_owner = "demo-org"
        repo = "demo-repo"
    else:
        print("Enter your GitHub details (or run with --demo flag for demo mode):\n")
        github_username = input("Your GitHub username: ").strip()
        repo_owner = input("Repo owner (org or your username): ").strip()
        repo = input("Repo name: ").strip()
    
    print(f"\n⚓ Fetching data for {repo_owner}/{repo}...\n")
    
    if demo_mode:
        data = demo_with_mock_data()
    else:
        data = fetch_github_data(github_username, repo_owner, repo)
    
    # Show what was fetched
    success_count = sum(1 for v in data.values() if v["success"])
    print(f"✅ Fetched {success_count}/3 data sources successfully\n")
    
    conversation_history = []
    
    # Initial summary
    print("🤖 First Mate is analyzing your data...\n")
    initial_reply = ask_agent(data, "What should I focus on today? Give me a full summary and top priorities.", conversation_history)
    print("─" * 60)
    print(initial_reply)
    print("─" * 60)
    
    # Interactive loop
    print("\n💬 Ask me anything about your work (or type 'quit' to exit):\n")
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n⚓ Fair winds, Captain! Good luck with your work.\n")
                break
            if not user_input:
                continue
            
            # For follow-up questions, reuse existing data
            reply = ask_agent(data, user_input, conversation_history)
            print(f"\n🤖 First Mate: {reply}\n")
            print("─" * 60)
        except KeyboardInterrupt:
            print("\n\n⚓ Fair winds, Captain!\n")
            break

if __name__ == "__main__":
    main()
