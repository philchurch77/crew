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
Sur = surgeon-deputy-head-500, Sr2 = surgeon-third-bad-day, Lkt = lookout-first-login-404,
CpH = captain-build-heaves-to, CpW = captain-build-weighs-anchor,
CpC = captain-chart-heaves-to. Each cell is crew score / baseline score,
each 0 to 1, over three runs.

| Version | Date | Judge | MaA | Bos | Pur | Trg | Car | Gun | Sur | Sr2 | Lkt | CpH | CpW | CpC | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.12.0 | 2026-09-20 | | | | | | | | | | | | | | Scoreboard, budgets and the Surgeon and Lookout cases added. Not run. |
| 2.13.0 | 2026-09-20 | sonnet | | | 1.00 / 0.67 | | | 1.00 / 1.00 | 0.86 / 0.86 | | 1.00 / 0.83 | | | 0.86 / 0.14 | Purser: Actions, 3 runs per arm, $10.03; crew runs 1.55 to 3.76 and 5 to 8 min, baseline 0.35 and 90 s. Laptop, 1 run per arm: Purser 1.00 again; Chart 0.86 with the names-the-passage grader failing on case (fixed in 2.13.2), baseline wrote a plan file straight off. Gunner, Surgeon, Lookout on WSL2 at 1 run per arm (2.13.2, agents unchanged). Gunner: both arms perfect, crew 3.97 vs 0.47; the case is too easy. Surgeon: agent never dispatched, both arms found it by reading; case too easy to need a loop, and the loop-was-red judge passed with no Bash call, so it is removed in 2.13.3. Lookout: agent never dispatched, but the crew arm walked the flow and the baseline only read. Two routing misses to work. |
| 2.14.1 | 2026-09-20 | sonnet | | | | | | | 0.71 / 0.71 | | 0.83 / 0.67 | | | | Surgeon and Lookout descriptions say to use the agent proactively, before answering; character text trimmed to pay for it. Re-run of surgeon*: still not dispatched (0.71 / not run); the description is not the lever. 2.14.1 sends both prompts through /crew:captain: both agents now dispatched (Agent 1x). But Bash is 0x in both crew arms even though the Lookout's report was labelled ran and the Surgeon must build a loop. Open question: does the tool_used grader count a subagent's calls, or did the agents not run anything? Unresolved; see docs/handoff.md. Harder Gunner and Surgeon cases: issues #9 and #10. |
| 2.15.0 | 2026-09-21 | sonnet | | | | | | 1.00 / 1.00 | | 1.00 / 0.76 | 0.86 / | | | | Issues #9 and #10, candidate 1 of each. New case surgeon-third-bad-day: the dashboard rates a pupil high on a third dysregulated observation dated exactly 28 days ago, inside a "four week" window that is 29 days; data from a new seed_demo command, scaffolded with seed.sh --demo. Gunner case gains a second hole, an unfiltered ?pupil= on the list, with a weight-2 regex grader. Both reproduced by hand and in fixture_check. No agent changed. WSL2, 1 run per arm. Surgeon: crew 1.39, baseline 0.48; Surgeon dispatched, Bash 6x in the crew arm and 2x in the baseline, so plain Claude built a loop too and ruled out an alternative on two votes of three. Gunner: crew 1.77, baseline 0.45; both arms wrote and ran the ?pupil= test. Then at 3 runs per arm, which is the score above. Surgeon: crew 1.00 on all three (Bash 7, 7, 8), baseline 0.71, 0.71, 0.86 with no loop on two runs of three; the case measures the Surgeon, issue #9 done. Gunner: 1.00 on all six runs, and crew run 2 never dispatched the Gunner and scored 1.00 at 0.50; plain Claude sends the parameter every time. That is the roster question in issue #10. Lookout, crew arm only, 1 run, --keep-temp: 0.86, 5.84, dispatched, Bash 10x, finding right, but labelled-ran failed three votes to none. So yesterday's 0x was not the grader: the counts follow the agent. Kept directory on WSL2 at /tmp/claude-eval-KC7BGK. |
| 2.15.1 | 2026-09-21 | sonnet | | | | | | | | | 1.00 / 0.89 | | | | Captain's log: on a Look passage, carry every finding with its severity and ran/read label, not a count. Paid for by cutting the sentence after "give each agent the actual files" that only restated it. Driven by the 2.15.0 Lookout run: the Lookout labelled every finding, the log compressed them to one line, labelled-ran failed three votes to none. Confirmed at 3 runs per arm: labelled-ran passes on every crew run; baseline skipped the walk on two runs of three (Bash 0x) and got the finding by reading. Cost is the thing to watch: crew runs 5.22 to 6.64 against baseline 0.86 to 1.34, because the Captain sends Lookout, Master-at-Arms, Purser and Bosun on this Look. Nothing measures whether that is over-dispatch yet. |
