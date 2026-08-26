#!/usr/bin/env python3
"""DP World Daily Pulse — standalone Python agent.

Runs the same radar pass defined in .claude/skills/daily-pulse/SKILL.md, but
via the Claude API directly (using its built-in web search tool) instead of
a Claude Code session. Meant to run on a schedule via GitHub Actions, so it
doesn't depend on a Claude Code session or the Gmail connector staying
attached — see .github/workflows/daily-pulse.yml.

SKILL.md is read at run time and used as the system prompt, so editing that
file (including via the daily-pulse-feedback skill) changes this agent's
behavior too — there's one source of truth for the pillars, queries, and
materiality bar, not two copies that can drift apart.

Environment variables:
    LLM_PROVIDER   "anthropic" (default), "openai", or "openrouter" — which API to use.

    Anthropic path:
        ANTHROPIC_API_KEY   required if LLM_PROVIDER=anthropic.
        DAILY_PULSE_MODEL   Claude model id; defaults to claude-sonnet-5.
        DAILY_PULSE_MAX_SEARCHES  Cap on web searches per run; defaults to 40.

    OpenAI path:
        OPENAI_API_KEY      required if LLM_PROVIDER=openai.
        DAILY_PULSE_MODEL   OpenAI model id; defaults to gpt-5.6.
            (Must be a model that supports the Responses API "web_search"
            tool — check developers.openai.com/api/docs/guides/tools-web-search
            if this default has since been superseded.)

    OpenRouter path:
        OPENROUTER_API_KEY  required if LLM_PROVIDER=openrouter.
        DAILY_PULSE_MODEL   OpenRouter model slug; defaults to
            nvidia/nemotron-3-ultra-550b-a55b:free. Web search is enabled via
            OpenRouter's "web" plugin, which is billed per search even on a
            free model (check openrouter.ai/docs/guides/features/plugins/
            web-search for current syntax/pricing if this has changed) — the
            OpenRouter account needs a funded balance for this to work, the
            model being free only covers token costs, not search costs.
        DAILY_PULSE_MAX_SEARCHES  Max results per search call; defaults to 40
            (passed as the plugin's max_results, not a call-count cap — the
            model may still trigger multiple searches per run).

    Shared:
        GMAIL_ADDRESS        Gmail address to send from (app-password auth).
        GMAIL_APP_PASSWORD   Gmail app password (not your regular password).
        DIGEST_RECIPIENT     Recipient address; defaults to GMAIL_ADDRESS.
"""
from __future__ import annotations

import os
import re
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / ".claude" / "skills" / "daily-pulse" / "SKILL.md"
DIGESTS_DIR = REPO_ROOT / "digests"
FEEDBACK_LOG = REPO_ROOT / "feedback" / "log.md"

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-5.6",
    "openrouter": "nvidia/nemotron-3-ultra-550b-a55b:free",
}
MODEL = os.environ.get("DAILY_PULSE_MODEL", DEFAULT_MODELS.get(PROVIDER, ""))
MAX_SEARCHES = int(os.environ.get("DAILY_PULSE_MAX_SEARCHES", "40"))

# Must match the pillar headings in SKILL.md exactly — used to parse the
# generated digest back into an index row without a second model call.
PILLARS = [
    "Maritime & shipping operations",
    "Gulf regional infrastructure",
    "Trade and economic developments",
    "Geopolitical and security",
    "Industry and strategic moves",
    "South Asia connectivity and corridors",
    "Portfolio-specific (DP World UAE/GCC)",
    "UAE domestic free zone competitors",
]


def load_skill_instructions() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    # Strip the YAML frontmatter (--- ... ---) — it's Claude Code skill
    # metadata (name/description for skill discovery), not run instructions.
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)


def most_recent_digest() -> tuple[str | None, str | None]:
    files = sorted(DIGESTS_DIR.glob("????-??-??.md"))
    if not files:
        return None, None
    latest = files[-1]
    return latest.stem, latest.read_text(encoding="utf-8")


def read_feedback_log() -> str:
    if FEEDBACK_LOG.exists():
        return FEEDBACK_LOG.read_text(encoding="utf-8")
    return "(no feedback log yet)"


def determine_lookback(today: datetime, is_first_run: bool) -> str:
    if is_first_run or today.weekday() == 0:  # Monday
        return "72h"
    return "24h"


def build_context(
    today: datetime,
    lookback: str,
    prev_date: str | None,
    prev_digest: str | None,
    feedback: str,
) -> str:
    context_parts = [
        f"Today's real date is {today.strftime('%Y-%m-%d')} ({today.strftime('%A')}).",
        f"Lookback window for this run: {lookback}.",
    ]
    if prev_digest:
        context_parts.append(
            f"Most recent prior digest ({prev_date}), for dedup/carry-forward "
            f"context per Step 2:\n\n{prev_digest}"
        )
    else:
        context_parts.append("This is the first run — no prior digest exists yet.")
    context_parts.append(
        f"feedback/log.md (missed items reported and any fixes already "
        f"applied to this skill):\n\n{feedback}"
    )
    context_parts.append(
        "Produce today's digest now, following the format in Step 5 exactly. "
        "Output ONLY the digest text (starting with 'DAILY PULSE — ') — no "
        "preamble, no commentary before or after it, and do not perform "
        "Steps 6-9 yourself (saving, indexing, committing, emailing are "
        "handled by the calling script)."
    )
    return "\n\n".join(context_parts)


def run_digest_anthropic(system_prompt: str, user_context: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": MAX_SEARCHES,
            }
        ],
        messages=[{"role": "user", "content": user_context}],
    )
    text_blocks = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_blocks).strip()


def run_digest_openai(system_prompt: str, user_context: str) -> str:
    import openai

    client = openai.OpenAI()  # reads OPENAI_API_KEY from env
    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        tools=[{"type": "web_search"}],
        input=user_context,
    )
    return response.output_text.strip()


def run_digest_openrouter(system_prompt: str, user_context: str) -> str:
    import openai

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context},
        ],
        # OpenRouter's web-search plugin — billed per search even on a free
        # model. See the OPENROUTER_API_KEY note in the module docstring if
        # this stops working; OpenRouter has been migrating this from a
        # "plugins" parameter to an "openrouter:web_search" tool type.
        extra_body={"plugins": [{"id": "web", "max_results": MAX_SEARCHES}]},
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def run_digest(
    today: datetime,
    lookback: str,
    prev_date: str | None,
    prev_digest: str | None,
    feedback: str,
) -> str:
    system_prompt = load_skill_instructions()
    user_context = build_context(today, lookback, prev_date, prev_digest, feedback)

    if PROVIDER == "anthropic":
        digest = run_digest_anthropic(system_prompt, user_context)
    elif PROVIDER == "openai":
        digest = run_digest_openai(system_prompt, user_context)
    elif PROVIDER == "openrouter":
        digest = run_digest_openrouter(system_prompt, user_context)
    else:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER={PROVIDER!r} — expected 'anthropic', 'openai', "
            f"or 'openrouter'"
        )

    if not digest.startswith("DAILY PULSE"):
        raise RuntimeError(
            f"Unexpected model output — did not start with 'DAILY PULSE':\n{digest[:500]}"
        )
    return digest


def parse_index_row(date_str: str, lookback: str, digest: str) -> str:
    pillars_with_items = []
    for pillar in PILLARS:
        pattern = re.escape(pillar) + r"\n(.*?)(?=\n[A-Z⚑]|\Z)"
        match = re.search(pattern, digest, re.DOTALL)
        if not match:
            continue
        section = match.group(1).strip()
        if section and not section.lower().startswith("no material"):
            pillars_with_items.append(pillar.split(" (")[0])

    carry_forward_match = re.search(
        r"Carry forward to weekly digest:\s*\n(.*)", digest, re.DOTALL
    )
    carry_forward_count = 0
    if carry_forward_match:
        lines = [
            line.strip()
            for line in carry_forward_match.group(1).splitlines()
            if line.strip().startswith("-")
        ]
        if not (len(lines) == 1 and "quiet day" in lines[0].lower()):
            carry_forward_count = len(lines)

    pillars_str = ", ".join(pillars_with_items) if pillars_with_items else "none"
    return f"| {date_str} | {lookback} | {pillars_str} | {carry_forward_count} |"


def update_index(date_str: str, row: str) -> None:
    readme = DIGESTS_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    if f"| {date_str} |" in text:
        return  # already indexed — safe to re-run
    text = text.rstrip("\n") + "\n" + row + "\n"
    readme.write_text(text, encoding="utf-8")


def git_commit_and_push(date_str: str) -> None:
    subprocess.run(
        ["git", "config", "user.name", "daily-pulse-bot"], cwd=REPO_ROOT, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "daily-pulse-bot@users.noreply.github.com"],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(["git", "add", "digests/"], cwd=REPO_ROOT, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_ROOT)
    if diff.returncode == 0:
        print("Nothing to commit.")
        return

    subprocess.run(
        ["git", "commit", "-m", f"Daily pulse — {date_str}"], cwd=REPO_ROOT, check=True
    )

    for delay in (0, 2, 4, 8, 16):
        if delay:
            time.sleep(delay)
        result = subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT)
        if result.returncode == 0:
            return
    raise RuntimeError("git push failed after retries")


def send_email(date_str: str, digest: str) -> bool:
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("DIGEST_RECIPIENT", gmail_address)
    if not gmail_address or not gmail_app_password:
        print("Gmail credentials not set — skipping email.")
        return False

    body = digest + (
        "\n\n---\nFull archive: "
        "https://github.com/prajwalram8/ClaudeDailyDigest/tree/main/digests"
    )
    msg = MIMEText(body, "plain")
    msg["Subject"] = f"DAILY PULSE — {date_str}"
    msg["From"] = gmail_address
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(msg)
    return True


def main() -> int:
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%Y-%m-%d")

    out_path = DIGESTS_DIR / f"{date_str}.md"
    if out_path.exists():
        print(f"{out_path} already exists — nothing to do.")
        return 0

    prev_date, prev_digest = most_recent_digest()
    is_first_run = prev_digest is None
    lookback = determine_lookback(today, is_first_run)
    feedback = read_feedback_log()

    print(
        f"Running daily pulse for {date_str} "
        f"(provider={PROVIDER}, model={MODEL}, lookback={lookback}, first_run={is_first_run})"
    )
    digest = run_digest(today, lookback, prev_date, prev_digest, feedback)

    out_path.write_text(digest + "\n", encoding="utf-8")
    row = parse_index_row(date_str, lookback, digest)
    update_index(date_str, row)

    git_commit_and_push(date_str)

    emailed = send_email(date_str, digest)
    print(f"Done. Email sent: {emailed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
