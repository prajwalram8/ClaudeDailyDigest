---
name: daily-pulse-feedback
description: >
  Logs a news item that the DP World Daily Pulse missed and closes the loop by fixing the
  underlying search/retrieval/synthesis gap in the daily-pulse skill — not just recording the
  complaint. Use this whenever the user pastes a link (or several) saying it was missed, should
  have been flagged, "why wasn't this in today's pulse", or otherwise wants to improve the daily
  pulse's coverage. Also trigger on explicit references to feedback/log.md or "log this as a
  miss".
---

# Daily Pulse Feedback

## Purpose

Every reported miss is a chance to fix the daily-pulse skill itself, so the same gap doesn't
recur. The deliverable of this skill is an edit to
`.claude/skills/daily-pulse/SKILL.md` (a query, a materiality-bar clarification, a source to
check directly) — the log entry in `feedback/log.md` is the audit trail, not the fix.

## Step 1 — Take in the link(s)

For each link the user provides, fetch it (WebFetch or WebSearch) to establish:
- Headline, outlet, and publish date/time
- Which of the 8 daily-pulse pillars it belongs to
- Whether it actually clears the materiality bar in `.claude/skills/daily-pulse/SKILL.md` Step 4
  (new investment/capacity, regulatory/tax/customs change, M&A/JV/partnership, security/
  operational disruption, trade agreement/tariff/trade-flow data, or a strategically significant
  competitor move). If it doesn't clear the bar, say so plainly — not every missed link should
  have run.

## Step 2 — Diagnose why it was missed

Check, in order, against the relevant `digests/YYYY-MM-DD.md` file (find the run whose window
should have caught this item):

1. **Window**: was the article published within that run's stated lookback (24h, or 72h on a
   Monday/first run)? If it was published outside the window, that's not a miss — note it as
   such (the item may still be worth a "carry forward" mention if it's still live).
2. **Query coverage**: would any existing query for that pillar plausibly have surfaced this
   article? Try the pillar's queries yourself. If none would, that's the gap — draft the query
   (or query variant) that would have caught it.
3. **Source coverage**: did the miss happen because the outlet/source isn't well indexed by web
   search for this topic (e.g. a trade-specific publication, a regulator's own press page)? If
   so, consider whether that source is worth naming directly in the pillar's instructions.
4. **Materiality filtering**: was the item actually surfaced by search that day but wrongly
   excluded at Step 4? If so, the fix is a clarification to the materiality bar or exclusion
   list, not a new query.
5. **Pillar mismatch**: did it fall between two pillars and get missed because neither query set
   was aimed at it? If so, note it under the pillar it best fits, or flag if a new pillar
   boundary needs clarifying.

Only one of these is usually the true cause — say which, plainly, rather than hedging across
all five.

## Step 3 — Apply the fix

If Step 2 found a systematic, fixable gap, edit `.claude/skills/daily-pulse/SKILL.md` directly:
- Add or reword a search query under the relevant pillar in Step 3
- Clarify the materiality bar or exclusion list in Step 4
- Add a note to check a specific source/outlet directly for that pillar

Keep edits minimal and targeted — one line added to the right pillar, not a rewrite. If the miss
was a one-off (window-timing edge case, a search-engine gap with no fixable pattern), make no
skill edit and say so — don't force a change for its own sake.

## Step 4 — Log it

Append an entry to `feedback/log.md`, most recent first, in this form:

```
### YYYY-MM-DD — [headline]
- Link: [url]
- Published: [date] · Pillar: [pillar name]
- Materiality: [cleared the bar / did not clear the bar, because ...]
- Root cause: [window timing / query coverage / source coverage / materiality filtering /
  pillar mismatch / unclear]
- Fix: [what was changed in daily-pulse/SKILL.md, quoted briefly — or "no fix, one-off"]
```

## Step 5 — Commit and push

```
git add feedback/log.md .claude/skills/daily-pulse/SKILL.md
git commit -m "Feedback: <short description of the fix>"
git push -u origin main
```

Same retry rule as the daily-pulse skill: on a network failure, retry up to 4 times with
exponential backoff (2s, 4s, 8s, 16s). Push directly to `main`, no PR needed.

## Step 6 — Tell the user

One or two sentences: what was logged, what (if anything) changed in the skill, and — if
relevant — which future runs will benefit.
