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
- A daily scheduled trigger runs the skill automatically and pushes each day's file straight to
  `main`.

## Running it manually

In a Claude Code session with this repo open, ask it to "run the daily pulse" (or invoke the
`daily-pulse` skill directly). It searches each pillar, compares against the most recent file in
`digests/`, writes today's file, updates the index, and commits.
