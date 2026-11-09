"""
E5 add-on: site-cluster bootstrap for the stepped-wedge estimators.

Isaac's point 7: uncertainty must respect the rollout design. Patients are
nested in sites and sites persist across periods, so an analyst holding one
realisation of the wedge should resample SITES, not patients. This script
reuses the data-generating process and estimators of exp_G2_sites.run_seed
unchanged, and adds, for each independent seed, a cluster bootstrap that
resamples sites with replacement within each rollout cohort (preserving the
design), recomputes the retrospective DiD and the DiD-anchored X split, and
records whether the 95% percentile interval covers the simulator truth of
that realisation. Coverage is then averaged over independent seeds.

Output: figures/merged_expG2_clusterboot.json
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_G2_sites as G  # noqa: E402

B_DEFAULT = 300
KEYS = ("retro", "x_endogenous_loss_did", "x_exogenous_loss_did")


def site_level_arrays(seed, row_index, sites, n, rho, trend, triage, root_seed):
    """Re-run one wedge realisation and return per-site quantities needed for
    the cluster bootstrap. Mirrors exp_G2_sites.run_seed exactly."""
    cfg = G.make_cfg(deploy=True)
    rng = np.random.default_rng(np.random.SeedSequence([root_seed, row_index, seed]))
    z = rng.normal(size=sites)
    priority = rho * z + np.sqrt(1 - rho ** 2) * rng.normal(size=sites)
    cohort = np.empty(sites, dtype=int)
    for t, block in zip(G.COHORTS, np.array_split(np.argsort(-priority), len(G.COHORTS))):
        cohort[block] = t
    observed_loss = np.empty((sites, G.PERIODS))
    observed_x = np.empty((sites, G.PERIODS))
    patient_x, patient_loss, true_site = {}, {}, {}
    for j in range(sites):
        for t in range(G.PERIODS):
            deployed = t >= cohort[j]
            normal = rng.normal(size=(n, cfg.d))
            baseline_mean = 0.5 * z[j]
            temporal_shift = (0.10 + trend * z[j]) * t
            x_without = normal + baseline_mean + temporal_shift
            x = x_without + (triage if deployed else 0.0)
            action = rng.random(n) < G.p_treat(cfg, x, deployed)
            q0, q1 = G.response(cfg, x, z[j])
            y = rng.random(n) < np.where(action, q1, q0)
            losses = (G.r_hat(cfg, x) - y) ** 2
            observed_loss[j, t] = losses.mean()
            observed_x[j, t] = x[:, :2].mean()
            if t == cohort[j] - 1 and cohort[j] in G.COHORTS[:-1]:
                patient_x[j], patient_loss[j] = x, losses
            if t == cohort[j] and t in G.COHORTS[:-1]:
                x_pretrend = normal + baseline_mean + temporal_shift - (0.10 + trend * z[j])
                standard_at_t = G.expected_loss(cfg, x_without, z[j], False)
                shifted_standard = G.expected_loss(cfg, x, z[j], False)
                deployed_risk = G.expected_loss(cfg, x, z[j], True)
                true_site[j] = {
                    "retro": deployed_risk - standard_at_t,
                    "x_endogenous_loss_did": shifted_standard - standard_at_t,
                    "x_exogenous_loss_did": standard_at_t - G.expected_loss(cfg, x_pretrend, z[j], False),
                }
    return dict(cohort=cohort, observed_loss=observed_loss, observed_x=observed_x,
                patient_x=patient_x, patient_loss=patient_loss, true_site=true_site)


def estimates_for(sel, D):
    """Estimators of exp_G2_sites on a (possibly resampled) multiset of sites.
    `sel` is an array of site indices (with repeats allowed)."""
    cohort = D["cohort"][sel]
    L = D["observed_loss"][sel]
    X = D["observed_x"][sel]
    acc = {k: [] for k in KEYS}
    for t in G.COHORTS[:-1]:
        sw = np.flatnonzero(cohort == t)
        ct = np.flatnonzero(cohort > t)
        if len(sw) == 0 or len(ct) == 0:
            continue
        c_loss = float(np.mean(L[ct, t] - L[ct, t - 1]))
        c_x = float(np.mean(X[ct, t] - X[ct, t - 1]))
        for i in sw:
            j = sel[i]
            shift = X[i, t] - X[i, t - 1]
            total = G.shifted_observed_loss(D["patient_x"][j], D["patient_loss"][j], shift)
            acc["retro"].append(L[i, t] - L[i, t - 1] - c_loss)
            acc["x_exogenous_loss_did"].append(c_loss)
            acc["x_endogenous_loss_did"].append(total - L[i, t - 1] - c_loss)
    return {k: float(np.mean(v)) if v else np.nan for k, v in acc.items()}


def truth_for(D):
    return {k: float(np.mean([v[k] for v in D["true_site"].values()])) for k in KEYS}


def cluster_bootstrap(D, B, rng):
    """Resample sites with replacement within each rollout cohort."""
    cohort = D["cohort"]
    groups = [np.flatnonzero(cohort == t) for t in G.COHORTS]
    draws = {k: np.empty(B) for k in KEYS}
    for b in range(B):
        sel = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in groups])
        est = estimates_for(sel, D)
        for k in KEYS:
            draws[k][b] = est[k]
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)), float(np.nanstd(v)))
            for k, v in draws.items()}


def run(seeds, B, sites, n, triage, root_seed):
    # same four settings, same row order and root seed as exp_G2_sites.run
    settings = (("random_order_common_trend", 0.0, 0.0), ("random_order_site_trend", 0.0, 0.04),
                ("correlated_order_common_trend", 0.85, 0.0), ("correlated_order_site_trend", 0.85, 0.04))
    rows = []
    for row_index, (label, rho, trend) in enumerate(settings):
        cover = {k: [] for k in KEYS}
        width = {k: [] for k in KEYS}
        sd_ratio = {k: [] for k in KEYS}
        point = {k: [] for k in KEYS}
        truth_all = {k: [] for k in KEYS}
        for seed in range(seeds):
            D = site_level_arrays(seed, row_index, sites, n, rho, trend, triage, root_seed)
            full = estimates_for(np.arange(sites), D)
            tr = truth_for(D)
            ci = cluster_bootstrap(D, B, np.random.default_rng(np.random.SeedSequence([root_seed, 7, row_index, seed])))
            for k in KEYS:
                lo, hi, sd = ci[k]
                cover[k].append(lo <= tr[k] <= hi)
                width[k].append(hi - lo)
                point[k].append(full[k])
                truth_all[k].append(tr[k])
        row = {"rollout": label, "rho": rho, "trend": trend, "seeds": seeds, "B": B}
        for k in KEYS:
            pt = np.array(point[k]); tt = np.array(truth_all[k])
            row[k] = {
                "coverage": float(np.mean(cover[k])),
                "mean_width": float(np.mean(width[k])),
                "across_seed_sd_of_estimate": float(pt.std(ddof=1)),
                "mean_bootstrap_sd": float(np.mean(width[k]) / 3.92),
                "relative_bias": float((pt - tt).mean() / tt.mean()),
            }
        rows.append(row)
        print(f"{label:28s} " + " | ".join(
            f"{k}: cov {row[k]['coverage']:.2f} bootSD/seedSD {row[k]['mean_bootstrap_sd']/row[k]['across_seed_sd_of_estimate']:.2f}"
            for k in KEYS))
    return {"design": "Site-cluster bootstrap: sites resampled with replacement within each rollout "
                      "cohort, B resamples per realisation; coverage of the 95% percentile interval for the "
                      "realisation's own simulator truth, averaged over independent seeds. Estimators and DGP "
                      "are those of exp_G2_sites.py.",
            "parameters": {"seeds_per_row": seeds, "B": B, "sites": sites, "n_per_site_period": n,
                           "triage": triage, "root_seed": root_seed},
            "rows": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--B", type=int, default=B_DEFAULT)
    p.add_argument("--sites", type=int, default=48)
    p.add_argument("--n-per-site-period", type=int, default=400)
    p.add_argument("--triage", type=float, default=0.25)
    p.add_argument("--root-seed", type=int, default=2026092905)
    p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures",
                                                 "merged_expG2_clusterboot.json"))
    a = p.parse_args()
    res = run(a.seeds, a.B, a.sites, a.n_per_site_period, a.triage, a.root_seed)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
