---
name: daily-pulse
description: >
  Runs the DP World Daily Pulse — a daily radar pass across maritime, Gulf infrastructure,
  trade, geopolitical, competitor, corridor, and free-zone developments that could affect
  DP World's Jebel Ali Port & Terminals, JAFZA, NIP, Mina Rashid, Mina Hamriya, and GCC/Levant
  logistics footprint. Use this skill whenever the user asks to "run the daily pulse", "run the
  daily digest", "do today's radar pass", references daily-pulse.md, or when fired by the
  daily-pulse-run scheduled trigger. Flags only genuinely new, material developments since the
  last run and saves the result to digests/ in this repo — it is not a general news summarizer.
---

# DP World Daily Pulse

## Purpose

A daily radar pass, not a daily digest. Flag genuinely new, material developments since the
last run. Stay silent on anything routine. Output is short, scannable, and built for someone
who already read yesterday's pulse — don't re-explain background they already have.

---

## Step 1 — Determine run mode and date

Work out today's actual date (do not assume what "recent" means — check it).

- **Standard run**: look back **24 hours**.
- **Extended run — use 72 hours** if either is true:
  - Today is a Monday, OR
  - This is the first run ever (no files exist yet in `digests/`).

## Step 2 — Load prior context

List `digests/` and open the single most recent dated file (sorted by filename, which is
`YYYY-MM-DD.md`). Use it to:

- Avoid re-flagging items already reported, unless there is a **material update** to a
  previously flagged item (escalation, reversal, confirmation of a rumor, new figures) — in
  that case, note it as an update, not a new item, e.g. "Update to Aug 15 item: ...".
- Pull forward its "Carry forward to weekly digest" list as context for what's still open,
  so today's run can note if any of those items have since resolved or escalated.

If `digests/` is empty (first run), skip this step — there is nothing to compare against.

Also check `feedback/log.md` for entries logged since the last run. Most feedback is resolved by
editing this file directly (see the `daily-pulse-feedback` skill) — you don't need to re-derive
anything from the log itself. It's listed here only as a sanity check that nothing pending was
missed.

## Step 3 — Search each pillar

Use web search for each query below, using today's real date in the search. If a query returns
nothing useful, try a close variant rather than forcing a result.

**1. Maritime & shipping operations**
Red Sea Houthi shipping attacks · Strait of Hormuz tanker disruption · Drewry World Container
Index · Asia Europe blank sailings · Jebel Ali port congestion

**2. Gulf regional infrastructure**
AD Ports Group announcement · KEZAD Khalifa Industrial Zone · NEOM Red Sea port project · Oman
Sohar Salalah port · GCC rail network corridor

**3. Trade and economic developments**
UAE CEPA agreement update · UAE non-oil trade data · US tariffs Middle East trade ·
manufacturing relocation Gulf China+1 · UAE FDI manufacturing announcement

**4. Geopolitical and security**
Strait of Hormuz tensions today · Red Sea shipping insurance rates · Iran Gulf sanctions update
· Suez Canal traffic status

**5. Industry and strategic moves**
AD Ports Gulftainer announcement · CMA CGM terminal investment · COSCO Shipping Ports deal ·
port automation green corridor

**6. South Asia connectivity and corridors**
IMEC corridor progress update · India Middle East Europe corridor · INSTC corridor development
· India Pakistan port SEZ news

**7. Portfolio-specific (DP World UAE/GCC)**
Jebel Ali Port news · JAFZA free zone announcement · DP World UAE news · National Industries
Park news

**8. UAE domestic free zone competitors**
SAIF Zone RAKEZ DMCC news · KIZAD industrial zone announcement · Dubai South free zone news ·
Egypt SCZONE Suez Canal Economic Zone

## Step 4 — Apply the materiality bar

Include only:
- New investments, capacity additions, or facility launches
- Regulatory, tax, or customs policy changes
- M&A, JV, or partnership announcements
- Security/operational disruptions (Red Sea, Hormuz, Suez, sanctions)
- Trade agreements, tariff changes, or material trade-flow data
- Competitor moves with strategic significance (new services, pricing, capacity, tech)

Exclude: routine PR, executive quote pieces with no new fact, recycled wire syndication, minor
personnel news, anything you can't verify against at least one credible source.

If nothing material turns up in a pillar, say so in one line and move on. Do not pad with minor
items to make a pillar look active. Omit a pillar entirely from the output only if it has zero
material items AND nothing worth a one-line "quiet" note — in practice, prefer the one-line note
over silent omission so the reader knows the pillar was actually checked.

## Step 5 — Write the digest

```
DAILY PULSE — [DATE]
[Lookback: 24h | 72h — Monday/first-run extended window]

[Pillar Name]
- [One to two sentences: what happened, why it matters] — Source: [outlet], [date]
(repeat per material item; write "No material developments." if the pillar was checked and
clean — do not omit the pillar)

⚑ Watch items (early/unconfirmed signals worth monitoring):
- [item, if any — otherwise omit this section entirely]

Carry forward to weekly digest: [bullet list of items, or "none — quiet day"]
```

Keep each item to one or two sentences — this is a flag, not analysis. Save deeper synthesis
(Big Picture, themed grouping, strategic framing) for the weekly digest run
(`weekly-trade-digest` skill).

## Step 6 — Save persistently

Write the digest to `digests/YYYY-MM-DD.md` (today's date, e.g. `digests/2026-08-18.md`) in
this repo. This is the permanent record — the next run reads it back in Step 2.

## Step 7 — Update the index

Append one row to the table in `digests/README.md`:

`| YYYY-MM-DD | 24h/72h | pillars with material items | carry-forward count |`

Create `digests/README.md` with a header and empty table if it doesn't exist yet.

## Step 8 — Commit and push

```
git add digests/
git commit -m "Daily pulse — YYYY-MM-DD"
git push -u origin main
```

If push fails on a network error, retry up to 4 times with exponential backoff (2s, 4s, 8s,
16s). This repo pushes daily pulse files directly to `main` — no PR needed for these routine
data commits.

## Step 9 — Email the digest

Send today's digest by email using the Gmail `send_message` tool:

- To: prajwalram8@gmail.com
- Subject: `DAILY PULSE — YYYY-MM-DD`
- Body: the full digest text exactly as written in Step 5 (plain text, no reformatting), followed
  by a blank line and `Full archive: https://github.com/prajwalram8/ClaudeDailyDigest/tree/main/digests`
- Also add one line inviting feedback: `Missed something? Just reply to this thread or paste the
  link(s) into a Claude Code session on this repo — see feedback/log.md.`

Do this after the push in Step 8 succeeds, not before — the committed file is the source of
truth; the email is a convenience copy. If the Gmail tool is unavailable in this session (no
Gmail connector granted), skip this step and note it in your final summary rather than failing
the whole run — the digest is still saved and pushed either way.
