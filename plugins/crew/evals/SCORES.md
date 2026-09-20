# Scores

One row per plugin version that changed an agent, a skill, the Articles or
the Captain. The number that matters is the delta: crew minus the no-plugin
baseline. A version whose delta on any case drops below the previous row's
is not an improvement, whatever the diff reads like (AGENTS.md section 7).

Fill a row from the HTML report in `evals/results/<timestamp>/`. Judge the
Captain, Surgeon and Lookout cases with `--judge-model sonnet`. A blank cell
means the case did not exist or was not run; say which in the notes.

Cases: MaA = master-at-arms-unfiltered-detail, Bos = bosun-split-comment,
Pur = purser-destructive-migration, Trg = trigger-text-came-back-shorter,
Car = carpenter-oversized-dashboard, Gun = gunner-cross-school-test,
Sur = surgeon-deputy-head-500, Lkt = lookout-first-login-404,
CpH = captain-build-heaves-to, CpW = captain-build-weighs-anchor,
CpC = captain-chart-heaves-to. Each cell is crew score / baseline score,
each 0 to 1, over three runs.

| Version | Date | Judge | MaA | Bos | Pur | Trg | Car | Gun | Sur | Lkt | CpH | CpW | CpC | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.12.0 | 2026-09-20 | | | | | | | | | | | | | Scoreboard, budgets and the Surgeon and Lookout cases added. Not run. |
| 2.13.0 | 2026-09-20 | sonnet | | | 1.00 / 0.67 | | | | | | | | 0.86 / 0.14 | Purser: Actions, 3 runs per arm, $10.03; crew runs 1.55 to 3.76 and 5 to 8 min, baseline 0.35 and 90 s. Laptop, 1 run per arm: Purser 1.00 again; Chart 0.86 with the names-the-passage grader failing on case (fixed in 2.13.2), baseline wrote a plan file straight off. Surgeon and Lookout blocked on the Windows sandbox. |
