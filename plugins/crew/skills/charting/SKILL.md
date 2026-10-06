---
name: charting
description: >-
  Load when a task is too big to finish in one passage or one session — a new
  app, a new feature area, a migration across several models, a rebuild, or
  anything the developer calls a "project", "chart" or "voyage". Also load
  whenever the developer says "sail leg N", "next leg", "where are we on the
  chart" or "update the chart", or a task names a chart in `docs/chart/`. Maps
  the work as a chart of open decisions and one-passage legs before any code
  is written, and keeps that chart as the shared record between sessions.
---

# Charting

A chart is the map of work too big for one sitting. It exists so that no leg
stalls halfway on a question nobody asked, and no session runs out of context
mid-build. Charting writes no application code. Article 11 carries the rule;
this skill carries the procedure and the file, so every session reads and
keeps the chart the same way.

Where `/captain` is available, its Chart passage draws the chart and "sail
leg N" is its Build passage; this skill is what both work to. Where it is
not, follow this skill directly.

## When to chart, and when not to

Chart when the work clearly spans several sessions, or cannot be classified
into a single passage. Do not chart a task that one Build, Fix, Tidy, Look or
Ship passage can finish: say so and proceed with that passage. When a Build
plan comes back as more than one leg's worth, stop building and chart.

## Drawing a chart

1. **Read the water.** Fetch; check the current branch against `origin/main`
   and the deploy branch; read the project `CLAUDE.md` and `CONTEXT.md`
   (article 5). Name anything stale before planning on top of it.
2. **Dispatch the Quartermaster** with the goal and the relevant file paths,
   first for the round of questions, then, with the answers, for the chart.
   Ask for three things: the destination (what done looks like), the open
   decisions, and the legs. This is the one time an agent sails twice.
3. **Settle the decisions in rounds** (article 11): numbered, titled, with
   options and a recommended answer, the whole frontier at once and never
   one at a time. Facts the code can answer are read, not asked.
4. **Write the chart and the glossary.** Agents do not write files; the
   session that dispatched them does. `docs/chart/<name>.md` from the format
   below, and the new terms into `CONTEXT.md` at the project root.
5. **One checkpoint.** Show the developer the decisions and legs. Nothing is
   sailed until the chart is agreed.

## Open decisions come first

A decision is anything with more than one reasonable answer that would change
how a leg is built: a model shape, a permission rule, a library, a data
source, a name the client will see.

- List every decision separately from the legs, with the options and a
  recommendation. Once taken, record the answer and the reason, not the
  options.
- No leg that depends on an open decision may be sailed. Name the blocker
  on the leg.
- A decision nobody can phrase sharply yet is fog: it goes under **Not yet
  charted**, and a leg that needs it waits.

## Sizing legs

Each leg must be finishable in one passage with room to spare.

- One leg, one outcome a user can be shown: a vertical slice through model,
  migration, view, form, template and test, never one layer of everything.
  "All the models" is not a leg; "a teacher can take the AM register for
  one class" is.
- If a leg needs the words "and also", it is two legs.
- Every leg names its passage (Build, Fix, Tidy, Look or Ship), what it
  delivers, the crew it needs, and how it is verified.
- A leg touching anything the project `CLAUDE.md` declares sensitive
  (article 0) is marked **Gauntlet**: the gate runs before it is done. A
  leg with a migration, a field change or a text-handling form is marked
  **Purser** (article 6).
- A leg that ends in a deploy is a **Ship** passage and closes with
  `/wheels-up`.

## Where the chart lives

`docs/chart/<name>.md` in the project, committed with the code, so any
session on any surface can read it. The glossary is `CONTEXT.md` at the
project root, terms only (article 5). If the developer asks, open each
decision and leg as a GitHub issue and link them from the chart.

## Chart format

```markdown
# Chart: <name>

## Destination
<two lines: what reaching the end looks like>

## Decisions so far
- <decision>: <one-line gist, and why>

## Legs
| # | Leg | Blocked by | Delivers | Crew | Status |
|---|---|---|---|---|---|
| 1 | <name> | — | <what a user can do when it is done> | <agents, Gauntlet?, Purser?> | open |

## Not yet charted
<the fog: decisions you can see coming but cannot phrase sharply yet>

## Out of scope
<what this chart deliberately does not reach, and why>
```

Status is `open`, `sailing`, or `done <date>` with one line on what the
leg changed or carried forward.

## Sailing a leg

When asked to sail a leg, or "the next leg":

1. Read the chart. Take the requested leg, or the first open leg whose
   blockers are all settled. One leg per passage, never two.
2. If a needed decision is still open, stop and raise it in a round. Never
   decide it silently.
3. Run the leg as its named passage, with the crew that passage needs, and
   give the planner the chart and the leg, not the feature description
   alone, so it plans inside the decisions already taken.
4. When the leg makes port, update the chart in the same turn: set the
   leg's status, add any decision the leg forced to **Decisions so far**,
   cut fog that is now sharp enough into new legs, and move anything that
   turned out beyond the destination to **Out of scope**.
5. Report honestly (article 10): tests run and their result, anything
   skipped, anything that changed the remaining legs.

## Keeping it honest

- A chart is a living record, not a promise. Redraw legs when the water
  changes, and say why in the leg's status line.
- Never mark a leg done because the code was written. Done means verified.
