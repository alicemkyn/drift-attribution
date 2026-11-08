# E6: semi-synthetic MIMIC-IV experiment

Task E6 in the team to-do: real covariates and outcomes for a deterioration
task, a simulated alert policy and treatment effect on top, Experiments A and C
repeated. The credentialed run was done on MIMIC-IV v3.1 on the machine that
holds the data, first on 28 October 2026 and again on 3 November with the
corrected ward definition and whole-pool refits ("Cohort", "Design"); the
results are below ("Results") and in the manuscript (F7, the E6 appendix,
the last row of Table `tab:prevalence`).
`docs/NEXT_STEPS.md` has the checklist.

## Data use

MIMIC-IV is credentialed data. The PhysioNet data use agreement does not allow
sharing it with third parties, and PhysioNet's guidance on online services
extends that to sending it to hosted AI tools. Run the steps below yourself,
keep the tables and the cohort file outside git (`~/physionet`, `data/`), and
commit only aggregate outputs: `figures/merged_expE6*.json`,
`figures/fig7_mimic*.pdf`, `figures/performance_drop.json`, their copies in
`aaai/figures/`, `aaai/tables/e6_*.tex` and `aaai/tables/prevalence.tex`.
These hold summary statistics over thousands of admissions and no
patient-level rows.

Every script prints counts, rates and estimates only. One exception needed
handling: DuckDB quotes the offending CSV row in conversion and parsing errors.
`e6_mimic_cohort.py` therefore reads every column as text and casts with
`TRY_CAST` (a bad value becomes NULL), and if extraction still fails it prints
only the failing step and the exception type; the full message goes to
`data/e6_cohort.error.log`, which must stay local. `--show-errors` prints it,
for the open demo and the fixture only. The experiment script refuses to write
into `figures/` from the fixture or from a cohort under 5,000 admissions (such
as the demo).

## Run

`sim2/run_e6.sh` wraps the steps; each can be run on its own.

```sh
sim2/run_e6.sh demo                      # optional: open MIMIC-IV demo, extraction only (~2 MB)
sim2/run_e6.sh download <physionet-user> # six tables of v3.1 (~3 GB) into ~/physionet/mimiciv/3.1
sim2/run_e6.sh cohort                    # data/e6_cohort.npz and the acceptance checks
.venv/bin/python sim2/e6_units.py --mimic-root ~/physionet/mimiciv/3.1   # optional: how each care unit is classified
sim2/run_e6.sh main                      # figures/merged_expE6.json and Figure 7
sim2/run_e6.sh sensitivity               # tagged runs for the appendix
sim2/run_e6.sh report                    # performance drop, figures, tables, F7 numbers, validator
```

`download` asks for the PhysioNet password once (it goes to a temporary netrc
file, not the command line), resumes partial files and checks SHA-256 sums
against the release's `SHA256SUMS.txt`. It needs about 4 GB free (the tables
are about 2.6 GB, mostly `labevents`); set `MIMIC_ROOT` to put them elsewhere
and `MIMIC_VERSION=2.2` for v2.2. PhysioNet sends the Basic-auth challenge only
to wget-style clients (other user agents get the browser's 403 page), so the
script's curl identifies itself as wget-compatible. HTTP 401 after the
password means a wrong login; 403 means the login was accepted but the account
has no access to that MIMIC-IV version yet (credentialing, the CITI training
and the project's data use agreement are all required).
`cohort` keeps DuckDB's intermediate tables in an on-disk file next to the
cohort with a memory limit (`MEMORY_LIMIT`, default 4GB), so labevents does
not need to fit in RAM; the file is deleted afterwards.

The underlying commands, if you prefer them:

```sh
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-e6.txt
.venv/bin/python sim2/e6_mimic_cohort.py --mimic-root ~/physionet/mimiciv/3.1 --out data/e6_cohort.npz
.venv/bin/python sim2/exp_E6_mimic.py --cohort data/e6_cohort.npz --workers 4
.venv/bin/python sim2/exp_E6_mimic.py --cohort data/e6_cohort.npz --tag rrr25 --rrr 0.25   # sensitivity runs
.venv/bin/python sim2/check_performance_drop.py                                   # MIMIC-IV part of performance_drop.json
.venv/bin/python sim2/make_figures2.py && .venv/bin/python sim2/make_tables.py
.venv/bin/python sim2/e6_report.py && .venv/bin/python sim2/validate_josh_results.py
```

## Cohort

- Adult admissions (age at admission 18 or older).
- One prediction time per admission, chosen at random (deterministic hash)
  among creatinine draws taken on a ward, at least 4 h after admission,
  before discharge and outside any ICU stay. Ward means a `transfers` care
  unit that is not an ICU, emergency, PACU, obstetric, newborn, psychiatric,
  discharge-lounge or unknown unit by name, and in which ICU stays begin for
  fewer than 10% of its admit and transfer events (`ICU_UNIT_SHARE`). The
  share matters: MIMIC-IV v3.1 records a handful of ICU stays on general
  wards (16 among about 192,000 Medicine events), and the first version of
  this rule, which dropped any unit that ever began an ICU stay, removed
  Medicine, Med/Surg, Neurology, Surgery/Trauma and two intermediate units
  from the cohort. Neuro Intermediate and Neuro Stepdown (65% and 70%) are
  excluded; general wards stay below 2%. `sim2/e6_units.py --mimic-root ...`
  prints the classification of every unit (counts only).
- Features: age, sex, emergency admission, hours since admission, a prior ICU
  stay in the same admission, and the last value in the preceding 24 h of
  creatinine, urea nitrogen, sodium, potassium, chloride, bicarbonate,
  glucose, anion gap, white cells, haemoglobin and platelets. Missing values
  are imputed with the training median and flagged.
- Outcome: ICU admission (`icu/icustays.intime`) or in-hospital death within
  12 h of the prediction time. The two components are stored separately.
- Periods: `anchor_year_group` 2008-2013 (early) and 2014-2019 (late);
  `--early` and `--late` change this. The cohort also stores
  `year(admittime) - anchor_year`, and `--period-by admission_year` places each
  admission by its approximate year (its anchor group shifted by that offset),
  dropping admissions whose three-year window straddles the boundary.

The cohort script prints the size, patients, event rate overall and by anchor
group, the outcome split, missingness, the prediction times by ward unit
(counts under 10 suppressed), and then the acceptance checks of
`NEXT_STEPS.md` step 1.4 as PASS/FAIL lines; it exits with status 3 if one
fails.

## What is simulated

1. Deployment of a logistic score fitted to 40% of early-period patients.
2. The alert threshold: a 10% alert rate on those patients (`--alert-rate`).
3. Clinician response: an alert is acted upon with probability 0.85 (`--p-act`).
4. The effect of the alert-triggered action: it prevents an event that would
   otherwise have occurred with probability 0.5 and never causes one (`--rrr`).
5. A randomised unalerted arm, 30% of post-deployment patients (`--control-frac`).
6. The retrain-and-redeploy loop.

Covariates, outcomes under historical care and periods are real. Potential
outcomes: Y(standard care) is the MIMIC-IV outcome; Y(alert policy) =
Y (1 - A B) with A ~ Bernoulli(p_act) for alerted patients and
B ~ Bernoulli(rrr). No pre-deployment patient received the alert-triggered
action, so the union-graph estimator faces the eps = 0 positivity failure of
Experiment B.

## Design

- Experiment A analogue. `deploy_only` draws the pre and post samples from the
  same pool of held-out early-period patients, the post sample under the alert
  policy, so the exogenous change is exactly zero and the policy term is the
  whole change (the S3 analogue). `drift_only` and `drift_and_deploy` use the
  held-out early pool before and the late pool after. Targets are exact for the
  pools in expectation over the simulated components; the X / outcome split of
  real drift has no ground truth and is reported, not scored.
- Replicates resample patients with replacement, each with all of their
  admissions, and redraw the simulated components. The monitor and the
  proposed estimator share one density-ratio fit per replicate.
- Experiment C analogue: the late period is split by patient into training
  (60%) and evaluation pools; eight rounds; fixed or rate-held threshold; keep,
  naive refit, refit on A = 0, weighted refit. Events averted are expected
  values on the evaluation pool against its historical outcomes. Each refit
  uses a bootstrap sample of the whole training pool (`--n-train 0`, the
  default since 3 November). The first run refitted on 8,000 admissions:
  about 80 events at this event rate, too few for 24 features, so every
  refit, even on untreated patients, lost to the original score with the
  alert rate held, and refit noise hid the feedback.
- `--workers` runs replicates in parallel; results do not depend on the worker
  count: rerun with 6 workers, the main run wrote a byte-identical JSON. On an
  Apple-silicon laptop with 4 workers (sharing the CPU with other jobs) the
  main run took 6 minutes and the six sensitivity runs 2.5 to 4 minutes each;
  the slow step is the download (PhysioNet served about 100 KB/s, about five
  hours for `labevents`).

## Sensitivity runs

`--tag <name>` writes `merged_expE6_<name>.json` and `fig7_mimic_<name>.pdf`
into both figure folders. `run_e6.sh sensitivity` runs `rrr25`, `rrr75`
(`--rrr 0.25/0.75`), `alert05`, `alert20` (`--alert-rate 0.05/0.20`), `admyear`
(`--period-by admission_year`) and, when the cohort has the 2020 - 2022 anchor
group (v3.x), `covid` (`--late "2020 - 2022"`), with 100 and 30 replicates.
`make_tables.py` collects them into `aaai/tables/e6_sensitivity.tex`.

## Outputs and manuscript

- `figures/merged_expE6.json`, `figures/fig7_mimic.pdf` (and mirrors).
- `aaai/tables/e6_mimic.tex` (cohort in the caption, attribution and update
  rules) and `aaai/tables/e6_sensitivity.tex`; the appendix includes both when
  present.
- The `mimic_iv` part of `figures/performance_drop.json` (Brier score, AUROC,
  observed over expected events and calibration slope before and after the
  simulated deployment, on the held-out early-period and the late-period
  admissions) and the MIMIC-IV row of `aaai/tables/prevalence.tex`. The
  validator checks that its Brier changes equal the policy contrasts of the
  main run.
- `sim2/e6_report.py` prints the numbers F7 quotes, in the exact format the
  validator checks, and a draft of the F7 result sentences whose wording
  follows the sign of the policy term.

## What to expect

Written before the run and confirmed by it, at a lower event rate than
assumed here (0.84% before and 1.04% after, mean predicted risk 0.03 among
alerted patients). With a 5 to 10% event rate, alerted patients mostly have predicted risk below
0.5. Preventing their events then lowers the Brier score (the derivative of
E[(r - Y)^2] in P(Y = 1) is 1 - 2r), so the policy term is negative. The score
still degrades as a model: AUROC falls, and it over-predicts (observed over
expected events and the calibration slope both fall). `sim2/check_performance_drop.py`
(`figures/performance_drop.json`) shows this at every prevalence of the
synthetic grid and at both hospitals of the open stand-in; only the sign of the
Brier change depends on prevalence (positive at the 40% operating point). The
attribution question is unchanged (the monitor books the policy term to the
outcome mechanism); the text should report the drop in discrimination and
calibration and the sign of the Brier change separately.

## Results (3 November 2026; MIMIC-IV v3.1)

Cohort (corrected ward definition): 368,995 ward admissions of 155,852 adult
patients; 229,280 in 2008-2013 (event rate 0.84%), 110,093 in 2014-2019
(1.04%) and 29,622 in 2020-2022 (1.13%); 30% of prediction times are on
general medicine wards. ICU admission within 12 h follows 0.89% of prediction
times, death 0.05%. All acceptance checks passed. The score (91,002
early-period admissions) has AUROC 0.747 on held-out early admissions and
0.723 late; its threshold (predicted risk 0.016) flags 9.9% and 10.4%.

- Deployment only. Policy contrast -0.00127. The monitor books -0.00128 to
  P(Y | X) and nothing to P(X); the randomised arm estimates -0.00131 (bias
  interval covers zero) with a single-run SD of 0.0005, two fifths of the term.
  The union graph with oracle weights returns -0.00215, 69% too large, and the
  same value replicate by replicate whatever the effect size. AUROC falls
  0.747 to 0.702, observed over expected 1.04 to 0.87, calibration slope 1.05
  to 0.83 (`performance_drop.json`, `mimic_iv`).
- Real drift and deployment. Under historical care the Brier score rises by
  +0.00190 between the periods; with the alert the observed change is +0.00039:
  the alert's benefit (-0.00147) hides 77% of a real deterioration, and with
  rrr 0.75 or a 20% alert rate the observed change is negative. The proposed
  decomposition recovers the policy term (-0.00154) and the exogenous change
  (+0.00193); the monitor assigns -0.00244 to P(Y | X). In the late period the
  score under-predicts under historical care (O/E 1.27) and deployment brings
  O/E to 1.07, hiding the calibration drift too.
- Bias intervals of the randomised arm cover zero in 13 of 14 runs and
  scenarios; the exception (admission-year periods with drift) is -0.00012,
  8% of the term.
- Split of the exogenous change. Not stable: in the main run the two terms
  have single-run SDs of 0.0018 and 0.0019 against a total of +0.0019, and
  with admission-year periods or 2020-2022 they reach +-0.01 to +-0.03. The
  total stays within 0.00012 of its target in every run.
- Update rules, round 8, fixed threshold: keep 0.154, naive 0.148, refit on
  A = 0 0.177, weighted 0.183 points. Refits recalibrate to the late period,
  where the original score under-predicts; naive refitting also absorbs the
  prevented events (alert rate 10.7% against 15.4%) and averts a sixth fewer
  events than refitting on A = 0. The gap is positive in every run and grows
  with the effect (0.005, 0.029, 0.079 points at rrr 0.25, 0.5, 0.75); with
  rrr 0.75 the naive refit alternates between rounds in damped form. With the
  alert rate held the two refits are within 0.006 points of each other and,
  usually, slightly below the kept score (0.01 points in the main run). The
  weighted refit is within 0.013 points of the unweighted one.

What changed on 3 November. The first run (28 October) dropped every unit in
which MIMIC-IV records any ICU stay, which removed Medicine, Med/Surg,
Neurology, Surgery/Trauma and two intermediate units (180,910 admissions),
and refitted on 8,000 admissions per round (about 80 events), so that every
refit lost to the original score with the alert rate held. The attribution
findings held in both runs; the update-rule comparison is only interpretable in
the second.

## Open stand-in (until MIMIC-IV access)

`sim2/e6_sepsis_cohort.py` builds the same cohort format from the
PhysioNet/CinC Challenge 2019 training data (open, CC BY 4.0; Reyna et al.,
Crit Care Med 2020): 40,336 ICU stays from two hospital systems, hourly vitals
and labs. The two hospitals take the place of the two periods, in both
directions (score fitted at A with a shift to B, and the reverse). One
prediction time per stay, at least 4 h into it and before sepsis onset;
outcome sepsis onset within 12 h; features age, sex, ICU type, hours in the
ICU, hours in hospital before ICU admission, and the last value in the
preceding 24 h of six vital signs and eight labs. Chloride and bicarbonate are
left out: hospital B almost never records them, so their missing indicators
identify the hospital and the density ratio between hospitals degenerates
(hospital classifier AUROC 0.98 with them, 0.79 without). 426 stays labelled
septic from their first hour have no valid prediction time; the other 39,910
are all used, and every refit uses the whole training pool (`--n-train 0`).
The files (313 MB) come from PhysioNet's open S3 mirror and are checked
against the S3 checksums; 2,000 cohort rows were rebuilt independently from
the raw files without a mismatch.

```sh
.venv/bin/python sim2/e6_sepsis_cohort.py          # fetch and build data/e6_sepsis_cohort.npz
.venv/bin/python sim2/exp_E6_mimic.py --cohort data/e6_sepsis_cohort.npz --early A --late B --n-train 0 \
    --output figures/e6_open/merged_expE6_sepsis2019_AtoB.json --figure figures/e6_open/fig_e6_sepsis2019_AtoB.pdf
.venv/bin/python sim2/exp_E6_mimic.py --cohort data/e6_sepsis_cohort.npz --early B --late A --n-train 0 \
    --output figures/e6_open/merged_expE6_sepsis2019_BtoA.json --figure figures/e6_open/fig_e6_sepsis2019_BtoA.pdf
```

`exp_E6_mimic.py` refuses to write a non-MIMIC cohort into the E6 slot; the
stand-in lives in `figures/e6_open/` and is not in the manuscript.

Results (1 October; event rate 3.6% at A, 1.8% at B):

- Deployment only. The policy contrast is -0.0033 at A and -0.0016 at B
  (deployment lowers the Brier score at these event rates, while AUROC falls
  by 0.036 and 0.040 and the score over-predicts). The monitor books the whole
  observed change to P(Y | X) (-0.0032 at A, -0.0014 at B) and nothing to P(X).
  The randomised arm recovers the policy term (-0.0032 and -0.0015, bias
  intervals covering zero). The union-graph estimator with oracle weights
  overshoots by 66% and 46%.
- Shift and deployment. The randomised arm recovers the policy term in both
  directions (-0.0007 against -0.0007; -0.0057 against -0.0057) and the
  exogenous change. Moving from B to A, the alert's benefit hides a real
  deterioration (+0.0181): the observed change is +0.0126, and the monitor
  assigns -0.0022 to P(Y | X) where the proposed decomposition finds +0.0020.
- Retraining at the new hospital, round 8, fixed threshold. At A (3.6% events)
  naive refitting averts 0.72 points and refitting on untreated patients 0.88
  (difference +0.16 [0.14, 0.18]); holding the alert rate reduces the
  difference to +0.02. At B (1.8% events) the difference is +0.017 [0.014,
  0.020]. The weighted refit falls between the two in both directions.

## Testing without MIMIC-IV

`sim2/e6_fixture.py` writes a synthetic dataset with the MIMIC-IV column
layout and a `FIXTURE_NOT_MIMIC` marker: real care-unit names, ED visits
without an admission, repeat admissions years after the anchor year, a
2020 - 2022 group, text-only lab values, quoted comments with commas and line
breaks, a urine creatinine item with the blood item's label, ICU stays in a
step-down unit that also takes ward patients, and a few ICU stays recorded
on a general ward, which must not remove that ward. Cohorts built
from it are flagged, and `exp_E6_mimic.py` refuses to write them into
`figures/`:

```sh
.venv/bin/python sim2/e6_fixture.py --out /tmp/mimic_fixture --patients 8000
.venv/bin/python sim2/e6_mimic_cohort.py --mimic-root /tmp/mimic_fixture --out /tmp/fixture_cohort.npz --show-errors
.venv/bin/python sim2/exp_E6_mimic.py --cohort /tmp/fixture_cohort.npz --reps-a 20 --reps-c 6 \
    --output /tmp/fixture_E6.json --figure /tmp/fixture_E6.pdf
.venv/bin/python sim2/e6_report.py /tmp/fixture_E6.json
```

Nothing produced from the fixture is a result.
