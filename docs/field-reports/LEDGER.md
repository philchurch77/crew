# Field-report ledger

One row per report, from filed to fixed. AGENTS.md section 7 says how a
row moves. Kind is `judgment` (needs a case) or `fact` (one line in the
Articles or the Captain, no case). Status is `open`, `clustered`, `cased`,
`fixed` or `declined`. A report is closed on GitHub when its row says
`fixed`, and the closing comment is the row.

Clusters, in working order (`docs/plan-2026-11.md` has the detail):

| Cluster | Pattern | Version |
|---|---|---|
| B | Reviewers read where they should have run | 2.16.0 |
| C | The Gunner cannot prove what it wrote | 2.17.0 |
| A | The Captain's dispatch and log | 2.18.0 |
| D | The Quartermaster's judgment | 2.19.0 |
| E | Scratch hygiene (fact, rides with B) | 2.16.0 |

| Report | Agent | Cluster | Kind | Fix | Case | Version | Status |
|---|---|---|---|---|---|---|---|
| #17 | Master-at-Arms, Purser, Gunner | B, C | judgment | ran/read label on every finding; Stage 1 asks what an unauthenticated fetch receives | master-at-arms-fetch-redirect | | cased |
| #18 | Quartermaster | D | judgment | a named risk becomes a plan step or an acceptance, never an argument | quartermaster-gauntlet-scope | | clustered |
| #19 | Quartermaster | D | fact | article 6: `AddField` with `preserve_default=False` leaves no database default on Postgres | no case: fact | | clustered |
| #20 | Gunner | C | fact | invisible characters are written as escapes | no case: fact | | clustered |
| #21 | Gunner | C | judgment | `isolation: worktree`; mutation proof is part of writing the test | gunner-mutation-proof | | clustered |
| #22 | Quartermaster | D | judgment | the Captain decides Gauntlet scope from files touched; the Quartermaster is told | quartermaster-gauntlet-scope | | clustered |
| #23 | Quartermaster | D | judgment | a recommendation on an unverified external fact is marked and held | quartermaster-gauntlet-scope | | clustered |
| #24 | Captain | A | fact | `git fetch` and a statement of what is live when a chart or deploy gate is in play | no case: fact | | clustered |
| #25 | Quartermaster | D | judgment | a permission change lists every entry and exit of the area | quartermaster-gauntlet-scope | | clustered |
| #26 | Captain | A | fact | the deck check caught it; no edit | none | | declined |
| #27 | Captain | A | judgment | dispatch template: what the agent may run and may write, with no contradiction | captain-fix-whole-surface | | clustered |
| #28 | Lookout | E | fact | article 11: run only what you wrote or were given; remove probe files | no case: fact | | clustered |
| #29 | Captain | A | fact | "Departures from the plan" line in the log | no case: fact | | clustered |
| #30 | Carpenter | B | judgment | ran/read label on every finding | master-at-arms-fetch-redirect | | cased |
| #31 | Gunner | C | judgment | a test asserts the behaviour the Articles require, never the behaviour observed | gunner-mutation-proof | | clustered |
| 001 (file) | Captain, Surgeon | A | judgment | dispatch carries the symptom as reported with the whole surface in scope | captain-fix-whole-surface | | clustered |
| #9, #10 | evals | | | harder Surgeon and Gunner cases | surgeon-third-bad-day, gunner-cross-school-test | 2.15.0 | fixed |
