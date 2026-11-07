# Response to the final audit (reviews/final.md), 2026-11-08

The research code (`src/neuralpet`, `experiments/0NN`) is frozen at tag `research-freeze`. We changed
no experiment code and reran no confirmatory analysis. Fixes are in the report generator
(`scripts/make_final_report.py`, which now computes the numbers the audit asked for from the raw result
files), the docs, the play app and the tests.

| # | finding | what we did |
|---|---|---|
| 1 | "never better" contradicted by real − random | **Fixed.** FINAL now computes real − random and shuffle − random from `results_registered/runs.csv` (headline 2, "Expected vs happened" row, "What is not supported"). README reworded. These rows are descriptive and were not added to 010's `tables()` (frozen). |
| 2 | individuality and adaptation are internal, not behavioural | **Fixed.** FINAL headline 8, LIFE_CRITERIA and README now say "learned preferences (internal valences), not shown in behaviour". "Plus learning" was dropped (no learning-off condition). The self-maintenance and precariousness verdicts are labelled post hoc. |
| 3 | the S2 generic control was not size-matched in realisation | **Reported, not rerun.** FINAL computes the realised generic/on DA ratio and the count of zero-DA seeds and says "matched in expectation, not in realisation". LIFE_CRITERIA too. A better match needs a new plan; recorded under the 013 recommendation in OPEN_QUESTIONS. |
| 4 | the H1 deficit comes mostly from one cell | **Fixed.** Headline 1 gives the worst cell, the number of cells whose CI includes 0, the FlyWire hemispheres and the deviation-run value, all computed. |
| 5 | verdict prose hard-coded | **Mostly fixed.** The replication summary, the "H2 held in every sample" sentence (now conditional on every per-sample CI excluding 0), the 011 verdict and the 012 plan rules ("matters", "wiring helps", equivalence falsifier) are computed in the report script. 012's own `tables()` is unchanged (frozen); its verdict is applied in FINAL. |
| 6 | 012 falsifier not met, so the result is inconclusive | **Fixed.** Headline 6 states it, with how much wider the CIs are than the bounds (computed), and links it to the steering finding. README says "inconclusive". |
| 7 | rule 7: N2 row quoted sparse only | **Fixed.** Both sparsities are quoted, and the co-convergence account is limited to the pooled sparse code. |
| 8 | 011 caveats | **Fixed.** A caveat paragraph under the 011 table covers sparse only, the equivalence-style H1 rule, unequal KC rates (computed from the 011 table) and H2 AULC. Headline 5 says "sparse-code". |
| 9 | H3 literal "equivalent to 0" with a negative CI | **Fixed.** Headline 4 notes the negative point estimate and that the 009 literal effect did not replicate. |
| 10 | 4× steering gain overclaimed | **Fixed** in FINAL (paired differences vs steering off, computed), PLAY.md and OPEN_QUESTIONS. The discarded water run is now mentioned in FINAL. The commit message of eee66a5 cannot be changed without rewriting history (no force-push); this response corrects it. |
| 11 | freeze guard fails at HEAD | **Fixed.** The guard excludes `experiments/explore` (post-hoc scripts added after the freeze); `src/neuralpet` and `experiments/0NN` are still checked. The test passes. |
| 12 | play gain mutates a research module global | **Partly fixed.** `test_freeze` now calls 012's `check_constants()` (it asserts K_CONTRAST = 25) before reproducing 012, and ADAPTERS.md has a "play-only" entry. A per-instance gain would need a change to `src/neuralpet/creature.py`, which is frozen. Remaining risk: research and play in one process. Separate processes are the documented way to run them. |
| 13 | individuality CIs bootstrap non-independent pairs | **Fixed in FINAL.** A cluster bootstrap (individuals and groups resampled) is reported next to the table. The difference stays above 0 with a much wider CI. 012's `tables()` is unchanged (frozen). |
| 14 | HTTP/1.1 desync in the play server | **Fixed.** `do_POST` closes the connection on every early refusal. Keep-alive is allowed only after the body has been read. New test `test_refused_post_body_is_not_a_second_request`; it fails without the fix and passes with it. |
| 15 | methods nits | **Fixed.** Literal fractions per sample (computed from meta.json) and the CLAUDE.md figure; the seed-7 smoke run; the "expectation" column (starting hope vs the 010 plan's prediction); H2 wording; a pointer to secondary metrics including M3. |
| 16 | teaching-demo details | **Fixed:** the note field and docstring; FINAL mentions the 2.5 BL test and that the play run and forced-valence check disagree. **Left as is:** the global auth-failure limiter (documented trade-off: it protects the token from guessing) and bidi characters in names (inert with `textContent`). |
| 17 | housekeeping | STATUS updated and notebook committed with this change. **Not done:** a `task.P` assert in 010/011 (frozen). `test_freeze` reproduces a 010 slice with exact equality against the registered raw outputs, so a changed `task.P` would fail it. |
