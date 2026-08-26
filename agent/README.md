# Daily Pulse — Python agent

A standalone version of the `daily-pulse` skill that runs on its own schedule via
GitHub Actions, independent of any Claude Code session. It reads
`.claude/skills/daily-pulse/SKILL.md` at run time as its instructions, so the two
stay in sync automatically — edit the skill (including via `daily-pulse-feedback`)
and this agent picks up the change on its next run.

## How it works

1. Computes today's date and the lookback window (24h, or 72h on Monday / first run).
2. Reads the most recent file in `digests/` and `feedback/log.md` for context.
3. Calls Claude, OpenAI, or OpenRouter (your choice — see below) with web search
   enabled, using SKILL.md as the system prompt, to research each pillar and
   write the digest.
4. Saves `digests/YYYY-MM-DD.md`, updates the index in `digests/README.md`.
5. Commits and pushes directly to `main`.
6. Emails the digest via Gmail SMTP, if credentials are configured.

If the file for today already exists, the script exits immediately — safe to
trigger more than once a day.

## Choosing a provider

Set the `LLM_PROVIDER` repo **variable** (not secret — it's not sensitive) to
`anthropic` (default), `openai`, or `openrouter`. Whichever you pick, only that
provider's API key needs to be set; the others can be left out entirely.

## One-time setup

### 1. LLM API key

**Anthropic** (default): get a key from
[console.anthropic.com](https://console.anthropic.com/settings/keys), add it as
the `ANTHROPIC_API_KEY` secret.

**OpenAI**: get a key from
[platform.openai.com/api-keys](https://platform.openai.com/api-keys), add it as
the `OPENAI_API_KEY` secret, and set the `LLM_PROVIDER` repo variable to
`openai`. This path uses the Responses API's built-in `web_search` tool (model
must support it — the default is `gpt-5.6`; check
[developers.openai.com/api/docs/guides/tools-web-search](https://developers.openai.com/api/docs/guides/tools-web-search)
if that default has since changed).

**OpenRouter**: get a key from
[openrouter.ai/keys](https://openrouter.ai/keys), add it as the
`OPENROUTER_API_KEY` secret, and set the `LLM_PROVIDER` repo variable to
`openrouter`. Default model is `nvidia/nemotron-3-ultra-550b-a55b:free` —
token usage on this model is free, **but web search is not**: it's enabled via
OpenRouter's "web" plugin, billed per search (roughly $0.005–$0.015 each
depending on the backend engine OpenRouter routes to) regardless of whether
the underlying model is a free one. At ~30-40 searches per run that's on the
order of $0.20–$0.50/day. Your OpenRouter account needs a funded balance (add
credit at [openrouter.ai/credits](https://openrouter.ai/credits)) for this to
work at all — a $0 free-tier account can call the free model but web search
calls will fail. Check
[openrouter.ai/docs/guides/features/plugins/web-search](https://openrouter.ai/docs/guides/features/plugins/web-search)
if the plugin syntax has since changed (OpenRouter has been migrating this
from a `plugins` parameter to an `openrouter:web_search` tool type).

Whichever provider you use, this is billed separately from any existing
subscription — real spend on your card, even where token costs are zero.

**Never paste an API key into a chat conversation with Claude (or any
assistant) to "hand it over" — always add it directly as a GitHub repo
secret** (see step 3). A key typed into chat can end up logged in the
conversation history; a key added as a secret is encrypted and never
displayed back to you or to Claude after you save it.

### 2. Gmail app password (optional — only needed for email delivery)

1. Enable 2-Step Verification on the sending Gmail account, if not already on:
   [myaccount.google.com/security](https://myaccount.google.com/security).
2. Create an app password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
   Choose "Mail" as the app.
3. Use the generated 16-character password as `GMAIL_APP_PASSWORD` below — not
   your regular Gmail password.

If you skip this, the script just logs "Gmail credentials not set — skipping
email" and still completes the save/commit/push.

### 3. Add repo secrets and variable

Secrets: **Settings → Secrets and variables → Actions → Secrets tab → New repository secret**.

| Secret | Required | Value |
|---|---|---|
| `ANTHROPIC_API_KEY` | if using Anthropic (default) | your Anthropic API key |
| `OPENAI_API_KEY` | if using OpenAI | your OpenAI API key |
| `OPENROUTER_API_KEY` | if using OpenRouter | your OpenRouter API key |
| `GMAIL_ADDRESS` | for email | the Gmail address to send from |
| `GMAIL_APP_PASSWORD` | for email | the 16-character app password from step 2 |
| `DIGEST_RECIPIENT` | no | recipient address; defaults to `GMAIL_ADDRESS` if unset |

Variable (only needed to switch away from Anthropic): **Settings → Secrets and
variables → Actions → Variables tab → New repository variable** — name
`LLM_PROVIDER`, value `openai` or `openrouter`. Leave it unset to use the
Anthropic default.

No GitHub token needs adding — the workflow's built-in `GITHUB_TOKEN` already has
push access to this repo via the `permissions: contents: write` block in the
workflow file.

### 4. Test it

Once secrets are set, go to **Actions → Daily Pulse → Run workflow** to trigger it
manually instead of waiting for 02:00 UTC. Check the run logs, then confirm a new
file appeared in `digests/`.

## Running it locally

```bash
cd agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...    # or LLM_PROVIDER=openai + OPENAI_API_KEY=...
                                 # or LLM_PROVIDER=openrouter + OPENROUTER_API_KEY=...
export GMAIL_ADDRESS=...        # optional
export GMAIL_APP_PASSWORD=...   # optional
python daily_pulse.py
```

It commits and pushes to `main` from wherever it runs, same as in CI — make sure
your local git remote and credentials are set up for push access first.

## Relationship to the Claude Code Routine

This repo also has a Claude Code scheduled Routine (`daily-pulse-run`) doing the
same job from inside a Claude Code session, on the same 02:00 UTC schedule. With
both active, whichever finishes first wins cleanly (this script checks whether
today's file already exists and exits immediately if so) — but if they run
close enough together, both could start before either has written the file,
producing two different digests for the same day, a push race, or two emails.
Don't leave both enabled long-term: run them in parallel for a few days to
compare output quality, then disable one. Disabling the Routine is a
`delete_trigger` call on `daily-pulse-run`; ask Claude to do it once you're
ready, or remove it from the claude.ai Routines UI.
