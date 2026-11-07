# Audit of NeuralPet v1.0: FINAL report, protocol, stats, rules 5 and 6, data, play security

**Auditor:** independent read-only review, 2026-11-08. Every number below was either recomputed from the committed raw files (`experiments/*/results*/`) with `uv run python` or checked against the generated tables.

## Verdict

The protocol was followed: no backdating or plan editing was found. Each PLAN.md for 010, 011 and 012 is a single commit made before its results. No code changed between the 012 plan and its run. The task-parameter deviation is disclosed honestly, and the rerun decision is timestamped before the rerun. The statistics code (Holm, percentile bootstrap, paired t, d_z, the 010 verdict rules) is correct. Holm values were checked by hand against both families. Git holds no connectome data, derived connectivity, neuron IDs or secrets.

The main problems are in interpretation. One summary line says real wiring was never better, but by the repo's own data real beats random wiring at the SESOI size (sparse code). "Individuality" and "adaptation" are reported as properties of behaviour, but they were measured on learned valences, and the same report shows valences do not reach behaviour. The rule-6 "size-matched" generic control was often not matched in practice. Several summary sentences are hard-coded prose rather than computed. Two smaller technical faults: the freeze test fails at HEAD, and the play server has an HTTP/1.1 desync (no auth bypass found).

## Findings

### 1. [major] "Real wiring was not better, in any model we built" is contradicted by the repo's own data
- **Where:** `reports/FINAL.md`, "What is not supported", first bullet. The same idea appears in the bold lead of `README.md` ("Real mushroom-body partners did not help dopamine-gated learning").
- **What is wrong:** CLAUDE.md rule 2 compares real against both random and shuffle. Recomputed from `experiments/010/results_registered/runs.csv`, real − random on M2 is:
  - sparse: **+0.0202 [0.0114, 0.0290]**, p = 3.6e-5
  - literal: −0.0026 [−0.0093, 0.0043]

  FINAL's own "earlier experiments" list gives 006 real − random = +0.029 [+0.012, +0.046]. Real wiring is better than random with a sparse code. It is just not better than a degree-preserving shuffle. Neither FINAL nor `reports/010/tables.md` reports real − random, the most direct answer to half of "the one real question".
- **Fix:** add real − random, and shuffle − random (sparse +0.0278 [0.0200, 0.0355]), as descriptive rows in `experiments/010/run.py` `tables()`. Reword the bullet and the README lead to: "Real wiring beat random wiring (sparse code, about the SESOI) but not a degree-preserving shuffle; the benefit comes from degree structure, not from which PN contacts which KC."

### 2. [major] Individuality and adaptation are learned-weight properties, reported as behaviour
- **Where:** `reports/FINAL.md` headline 7 and the "Operational life criteria" table (copied from `docs/LIFE_CRITERIA.md`); `README.md` last bullet.
- **What is wrong:**
  - Both measures are computed on learned valences (`c.preferences()`, `experiments/012/run.py` `job_indiv` and `job_rev`). Learned valence acts on behaviour only through steering.
  - The same report shows steering has no detectable effect (on − steer_off, meals 1.0 [−1.8, 4.0]). The exploratory check shows that at the registered gain, valence does not move the body.
  - So "Adaptation: changes its learned **behaviour**" and "history-specific individuals" overclaim. The difference is internal, not behavioural.
  - "Self-maintenance comes from the fixed body/world rules **plus learning**" is unsupported. No learning-off condition was run, and the only route from learning to behaviour was null.
  - The self-maintenance and precariousness verdicts had no pre-registered threshold. LIFE_CRITERIA.md was first committed in e072ebf at 00:11:23, after the 012 results (3a6f898, 00:10:56). The 012 PLAN pre-specifies "met" rules only for individuality and adaptation.
- **Fix:** say "learned odour preferences (internal valence) diverge / re-adapt; under the registered constants this does not show in behaviour". Drop "plus learning". Label the self-maintenance and precariousness verdicts as defined after the results.

### 3. [major] The S2 "size-matched generic" control was often not size-matched
- **Where:** `experiments/012/run.py` `generic_coef()` (about lines 95–104). FINAL's life-criteria row says "did no better than a constant or a size-matched generic rule".
- **What is wrong:**
  - The quadratic is rescaled to match the `on` run's mean DA, evaluated at the **`on` run's** pre-meal energies. The generic run then meets different energies, and `max(0, ·)` clips.
  - Realised mean reward DA in `main.csv`: the generic run got **exactly zero reward DA in 9 of 36 seeds with meals**, and less than half of the `on` run's DA in 10 of 36. The generic/on ratio has median 0.92, 25th percentile 0.135, maximum 2.35. `const` matches exactly (ratio 1.000).
  - So about a quarter of S2 pairs compare against no reward learning at all. This is the plan as registered (no protocol breach), but describing it as "size-matched" in the results is inaccurate. It also weakens S2 as the rule-6 control.
- **Fix:** have `tables()` report the realised generic/on DA ratio and the count of zero-DA seeds. In FINAL and LIFE_CRITERIA, say the substitute was matched in expectation and not in realisation. Any rerun should match on the substitute's own realised DA, pre-registered as a new experiment.

### 4. [minor] Headline 1 hides that the H1 deficit comes mostly from one cell
- **Where:** `reports/FINAL.md` headline 1 ("they are slightly worse"); `reports/010/tables.md`, per-sample H1 sparse row.
- **What is wrong:**
  - Per-sample H1 sparse values: FlyWire right −0.0021 [−0.0087, 0.0048] and FlyWire left −0.0003 [−0.0067, 0.0062], both with CIs including 0. Hemibrain is −0.0204. The Hallem source is +0.0010.
  - Recomputed per sample × source cell, hemibrain × DoOR is −0.0405 [−0.0538, −0.0278]. 4 of the 6 cells have CIs including 0.
  - At the harder (deviation) setting, H1 sparse was −0.0007 [−0.0033, 0.0020].
  - The plan's "sample-dependent" rule only fires on a sign flip, so the label "replicated" is correct under the plan. The headline still generalises beyond what the data show.
- **Fix:** add one sentence to headline 1: "with the sparse code the deficit is carried by the hemibrain sample and DoOR odours; in both FlyWire hemispheres it is indistinguishable from 0, and it vanished at the harder task setting."

### 5. [minor] Summary verdicts are hard-coded prose, not computed
- **Where:** `scripts/make_final_report.py` (the module docstring says "Prose is fixed text; numbers are inserted"). The f-string around lines 130–175 holds "It held in every sample and both odour sources", "H1 and H2 replicated in both code settings; H3 only with the sparse code", "real ≈ n2a … by the plan's rule the deficit is carried by co-convergence", and "no; signs and sizes hold".
- **What is wrong:** these are all true for the current data, but they would stay in the report unchanged if the tables changed. Only "010 overturned" is derived from the data. `experiments/012/run.py` `tables()` applies none of the 012 PLAN decision rules ("matters" requires S1 and S2 significant with the same sign; the falsifier needs CIs within ±0.02 energy and ±60 s survival).
- **Fix:** compute each verdict string from the parsed rows, or `assert` its premise, for example that every per-sample H2 CI excludes 0. Add a 012 verdict line implementing the plan's rules.

### 6. [minor] The plan's 012 falsifier is not met, so S1/S2 are inconclusive, and FINAL does not say so
- **Where:** `experiments/012/PLAN.md` ("What would show the state rule does nothing here: all S1/S2 CIs within ±0.02 mean energy and ±60 s survival"); `reports/012/tables.md`, confirmatory family.
- **What is wrong:**
  - Survival CIs: S1 [−146.7, 244.9] s and S2 [−151.4, 166.2] s, against a ±60 s bound.
  - Energy CIs: S1 [−0.038, 0.042] and S2 [−0.018, 0.068], against a ±0.02 bound.
  - The design could not show "does nothing". Headline 5's "no detectable effect, not shown to be zero" is honest but does not cite the registered rule.
  - The structural reason (learning has no route to behaviour at K = 25) appears only in the exploratory section, not in headline 5.
- **Fix:** add "inconclusive by the plan's equivalence bounds (CIs 2–4× wider than ±0.02 / ±60 s); and since learned valence barely reaches behaviour at the registered gain, 012 could hardly detect a state-rule effect."

### 7. [minor] Rule 7 not respected in the N2 summary row
- **Where:** `reports/FINAL.md`, "Expected versus what happened", the row "What makes real worse than shuffle?".
- **What is wrong:** only the sparse values are quoted. With the literal code, real − n2a_coconv = −0.0034 [−0.0052, −0.0017]. Under the 010 plan's other rule ("if real < n2a, the pairing matters") that means pairing matters. Hemibrain sparse is also −0.0061 [−0.0078, −0.0044].
- **Fix:** quote both sparsities and note that the co-convergence account holds for the pooled sparse code only.

### 8. [minor] The 011 summary omits material caveats
- **Where:** `reports/FINAL.md` headline 4 and the 011 row; `experiments/011/PLAN.md`; `reports/011/tables.md`.
- **What is wrong:**
  - 011 is sparse-only, so headline 4 ("these wiring results survive") does not cover the literal results.
  - The H1 "sign holds" rule is an equivalence test (90% CI within ±0.02). It was written when the 010 run being checked was the deviation run (H1 = −0.0007, quoted in the 011 PLAN). With the registered H1 negative, "sign holds: yes" means "smaller than ±0.02", not "negative".
  - Graded-APL variants do not match KC activity across wiring conditions. apl_comp KC mean rate is 0.0674 for random vs 0.0754 for pn_out vs 0.0774 for pn_out_perm_live, so H2/H3 there are partly confounded with KC activity level.
  - Secondary AULC for H2 in apl_comp points the other way: −0.0051 [−0.0156, 0.0051].
- **Fix:** add these four points as one caveat sentence under the 011 table.

### 9. [minor] H3 literal is called "equivalent to 0" while both CIs exclude 0 on the negative side
- **Where:** `reports/010/tables.md`, family row H3 literal.
- **What is wrong:** the 95% bootstrap CI is [−0.0153, −0.0002] and the 90% CI is [−0.0140, −0.0014]. The t-test gives p = 0.057. The verdict follows the plan, but readers should know the point estimate is negative and the 009 literal finding (+0.031) failed to replicate. The bootstrap and t-test also disagree near the boundary (nit).
- **Fix:** in headline 3, add "(literal: point estimate negative; the 009 literal effect of +0.031 did not replicate)".

### 10. [minor] Overclaims about the 4× steering gain in docs
- **Where:** `docs/PLAY.md`, "Play-only steering gain" paragraph ("with 100 the liked smell is approached and the disliked one avoided"); `docs/OPEN_QUESTIONS.md`, 2026-11-08 entry ("4× the gain gives clear approach and avoidance"); commit eee66a5's message ("4x gain does").
- **What is wrong:** from `experiments/explore/results/steer_check.csv` (runs are paired by seed):
  - At K = 100 with valence +0.3, the creature still moves **away** (+0.50 [+0.25, +0.78] BL). It is not approaching, only drifting away less than with steering off. Paired against steering off: −0.84 [−1.24, −0.45].
  - At K = 100 with valence −0.3, paired against steering off: +0.20 [−0.09, +0.49]. **No avoidance is shown.**
  - The play teaching run shows the opposite pattern (dislike shows, like does not), which the docs do not reconcile.
  - The odorant set was chosen after a discarded first run that used water. This is disclosed only in the script docstring.
- **Fix:** reword to "at 4× gain a positive valence reduces drift away from the smell; avoidance was not distinguishable from steering off". Report paired differences in FINAL's steering table. Mention the discarded first version in FINAL.

### 11. [minor] The freeze guard fails at HEAD, yet FINAL cites it
- **Where:** `tests/test_freeze.py`, `test_research_code_unchanged_since_tag`; FINAL's play section ("checked by `tests/test_freeze.py`").
- **What is wrong:** tag `research-freeze` is e072ebf. Commit eee66a5 later added `experiments/explore/steer_check.py` and its results CSV. Running `git diff --name-only research-freeze -- src/neuralpet experiments` now lists both files, and the test fails (reproduced).
- **Fix:** exclude `experiments/explore` from the guard, or re-tag after confirming that `src/neuralpet` is unchanged. Rerun the test before the v1.0 tag.

### 12. [minor] The play gain override mutates a research module global for the whole process
- **Where:** `src/neuralpet_play/game.py:63` (`C.K_CONTRAST = float(self.cfg["steer_gain"])`); `src/neuralpet/creature.py:143` reads the module global at call time.
- **What is wrong:**
  - Separate processes are isolated, so production is fine. But any research code running in the same process after a `Game()` is created silently uses K = 100. That includes pytest when `test_play` runs before `test_freeze` (for example with `-p random` or an explicit file order), and any script importing both.
  - `test_freeze.test_012_slice_unchanged` calls `life()` without `check_constants()`, so it would catch this only indirectly, through a numeric mismatch.
  - The play gain is an output-to-action adapter, but it is documented in DECISIONS.md and PLAY.md, not in `docs/ADAPTERS.md` (rule 5 says adapters belong there).
  - Disclosure is otherwise adequate: PLAY.md, DECISIONS.md and FINAL all state that the gain is tuned and play-only.
- **Fix:** make the gain an attribute of each `Creature` instance (default `K_CONTRAST`), set by the play `Game` on its own pet. Add `assert C.K_CONTRAST == 25.0` to `test_freeze`. Add a "play-only" entry to ADAPTERS.md.

### 13. [minor] Individuality CIs bootstrap pairs that are not independent
- **Where:** `experiments/012/run.py` `tables()`, individuality block: `boot_ci(d_hist)` resamples 190 pairs drawn from 20 individuals, and `boot_ci(d_noise)` resamples 50 pairs from 5 groups.
- **What is wrong:** a cluster bootstrap (recomputed, resampling individuals or groups) gives different-history distance [0.265, 0.391] vs same-history distance [0.153, 0.302]. These overlap. The reported [0.308, 0.347] vs [0.178, 0.255] do not. The plan's rule compares point values, so "met" holds by the letter of the plan, but the precision is overstated.
- **Fix:** resample individuals (and whole groups for same-history), and report the CI of the difference.

### 14. [minor] Play server: an unread request body is parsed as a second request (HTTP/1.1 desync)
- **Where:** `src/neuralpet_play/server.py` `do_POST`. It returns 403/404/415 before reading the body, on a keep-alive connection (`protocol_version = "HTTP/1.1"`).
- **What is wrong:** verified locally. A POST with no session whose body was a complete `GET /?t=wrong…` request received two responses: 403 "not signed in", then 403 "forbidden". The smuggled request was also counted in the global auth-failure limiter.
  - Behind cloudflared, connections to the origin are pooled across clients. That makes this a request-smuggling / response-queue-desync primitive (for example, swapping responses between clients, or locking the owner out).
  - No authentication bypass was found: smuggled requests carry none of the victim's cookie or CSRF token.
  - The other PLAY.md rules are implemented as described: 127.0.0.1 bind, Host allow-list, constant-time token compare, HttpOnly + SameSite=Strict cookie, CSRF, Origin check, 1 KB limit, JSON content type, whitelist schema, per-session rate limit, read-only switch, CSP/nosniff/XFO/no-store.
- **Fix:** set `self.close_connection = True` on every response sent before the body is consumed. Alternatively, read and discard `Content-Length` bytes (≤ MAX_BODY) first and close the connection otherwise. Add a test for it.

### 15. [nit] Methods and wording inaccuracies
- **"literal: as the connectome input gives"** (FINAL Methods): literal is actually kWTA at a fixed fraction, measured once with random v1 odours (0.552 / 0.571 / 0.613, `results_registered/meta.json`), not a threshold readout. State the fractions. Note that CLAUDE.md's figure is about 68%.
- **"Parameters chosen on synthetic circuits before any connectome run"**: the 010 PLAN discloses one connectome smoke run (seed 7) seen before the plan was committed. Mention it.
- **Expected column "real > shuffle > random"**: the 010 PLAN predicted real < shuffle (H1 sign −1). Attribute that expectation to the original question, not "plans".
- **"degree-preserving wirings > random (H2)"**: H2 tests pn_out only. shuffle − random is not in the family.
- **Secondary metrics**: CLAUDE.md lists interference (M3) as a metric, but FINAL reports no M3 or AULC. One line pointing to `reports/010/tables.md` would do.

### 16. [nit] Teaching demo and play-security details
- **`docs/play_teach.json` `note` field** says "over 40 s … mean of 4 copies". That applies only to the 2.5 BL test, not the 1 BL test FINAL quotes. The `scripts/play_teach_demo.py` docstring says "distance after 40 s", but the function returns the change in distance.
- **FINAL's play section** quotes only the 1 BL test. The 2.5 BL test (null) is in PLAY.md. Mention it in FINAL too.
- **Token-failure limiter**: it is global, so anyone who has the tunnel URL can lock the owner out for a minute (documented).
- **`host_ok`**: accepts any `*.trycloudflare.com` name (acceptable, since those names cannot rebind to 127.0.0.1).
- **Rename**: allows bidi control characters (U+202E). This is harmless with `textContent`.

### 17. [nit] Housekeeping
- `STATUS.md` still says "Next: WP6 play app commit … then WP7 final report", though both are done.
- `notebook/2026-11-08.md` exists but is untracked. No notebook entry is committed for the 2026-11-07/08 sessions.
- `task.P` has no constants assert in 010/011 equivalent to 012's `check_constants()`. Only `meta.json` records the values. Add an assert, given the deviation history.

## Checked and found in order
- **Protocol:** `git log --follow` shows one commit each for 010 PLAN (ff83d39, 23:06:53), 011 PLAN (0387df8, 23:12:49) and 012 PLAN (72b3370, 23:57:07). Every one comes before its results (2a9ae3a / ed69c8e; 20462ba / 667daf8; 3a6f898). `git diff 72b3370 3a6f898` touches only result and report files.
- **Deviations:** both DEVIATION.md files (23:27) come before the registered reruns (23:32, 23:43). The deviation runs are kept untouched in `results/`. FINAL's deviation paragraph quotes the deviation numbers correctly.
- **011 timing:** the 011 PLAN was written after the deviation 010 run and quotes its numbers. That is consistent with its own "written after experiment 010's results" statement.
- **Statistics:** `stats.holm` is a correct step-down with monotonicity, and the 010 and 012 Holm columns were reproduced by hand. `verdict()` matches the 010 PLAN rules, including the SESOI flag and strict equivalence. The 011 rules in `run.py` match the 011 PLAN. Bootstrap is a seeded percentile bootstrap over seeds; d_z uses ddof = 1.
- **Numbers:** every number in FINAL's tables matches `reports/010`, `011` and `012` `tables.md`, `steer_check.csv` (48 runs per cell; the steering-off cells for ±0.3 are identical, as expected) and `docs/play_teach.json`.
- **Data hygiene:** across the history of all branches, there are no `.npz`, data, feather, parquet or `.env` files and no `7205759…` root IDs in git. `.env`, `data/` and `play_data/` are gitignored. The largest tracked file is 1.4 MB (a results CSV). `null_stats.csv` and `diagnostics.csv` hold only summary statistics.
