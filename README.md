# ClaudeDailyDigest

A daily radar pass on developments that could affect DP World's positioning, risk profile, or
opportunity set across Jebel Ali Port & Terminals, JAFZA, NIP, Mina Rashid, Mina Hamriya, and
DP World's GCC/Levant logistics footprint.

This is a flag list, not a news summary: it stays silent on routine items and only reports
genuinely new, material developments since the previous run.

## How it works

- **`.claude/skills/daily-pulse/SKILL.md`** — the run instructions: which pillars and search
  queries to use, the materiality bar, and the output format.
- **`digests/`** — the persistent archive. One markdown file per run (`YYYY-MM-DD.md`), plus a
  running index in `digests/README.md`.
- **`agent/`** — a standalone Python agent that runs `SKILL.md` via GitHub Actions at 02:00 UTC.
  This is the **primary** way the digest gets produced. See `agent/README.md` for setup
  (API key, email).
- A Claude Code Routine runs the same skill 45 minutes later, as a **fallback**: its first move
  is to check whether today's file already exists, and it does nothing further if so. It only
  does a real run if the Python agent wasn't configured, failed, or GitHub Actions was
  unavailable — see "Relationship to the Claude Code Routine" in `agent/README.md`.
- **`.claude/skills/daily-pulse-feedback/SKILL.md`** + **`feedback/log.md`** — a self-improvement
  loop for missed items (see below).

## Running it manually

In a Claude Code session with this repo open, ask it to "run the daily pulse" (or invoke the
`daily-pulse` skill directly). It searches each pillar, compares against the most recent file in
`digests/`, writes today's file, updates the index, commits, and emails it.

## Reporting a missed item

Missed a genuinely material development? Paste the link(s) into a Claude Code session on this
repo and say it was missed. This invokes the `daily-pulse-feedback` skill, which diagnoses *why*
it was missed (outside the lookback window, no query would have surfaced it, wrongly filtered
out, fell between pillars) and, where the gap is systematic, edits
`.claude/skills/daily-pulse/SKILL.md` directly — a new query, a materiality-bar clarification, a
source to check — so future runs catch similar items. Every report is logged in
`feedback/log.md` with its diagnosis and whatever was changed (or "no fix" if it was a one-off).
