"""Test-level A/B results: which tests have a real winner, and how big the
gaps are compared with what pure noise would produce."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).parent))
from load import ROOT, load  # noqa: E402

RNG = np.random.default_rng(42)


def chi2_p(arms: pd.DataFrame) -> float:
    """Chi-square test: do all arms in this test share one click rate?"""
    table = np.column_stack([arms.clicks, arms.impressions - arms.clicks])
    if (table.sum(axis=0) == 0).any():
        return 1.0
    return chi2_contingency(table, correction=False)[1]


def best_worst_lift(clicks: np.ndarray, imps: np.ndarray) -> float:
    ctr = clicks / imps
    if ctr.min() == 0:
        return np.nan
    return ctr.max() / ctr.min() - 1


def run(dataset: str = "exploratory") -> dict:
    con = load(dataset)
    arms = con.sql("SELECT * FROM arms WHERE NOT bad_randomization").df()
    arms = arms[arms.groupby("test_id").headline.transform("size") >= 2]

    rows = []
    for test_id, g in arms.groupby("test_id"):
        imps = g.impressions.to_numpy().astype(np.int64)
        clicks = g.clicks.to_numpy().astype(np.int64)
        pooled = clicks.sum() / imps.sum()
        # Same test, but every arm has the pooled rate: pure noise.
        sim_clicks = RNG.binomial(imps, pooled)
        winner_rows = g[g.winner]
        rows.append({
            "test_id": test_id,
            "n_arms": len(g),
            "impressions": imps.sum(),
            "pooled_ctr": pooled,
            "p_value": chi2_p(g),
            "observed_lift": best_worst_lift(clicks, imps),
            "null_lift": best_worst_lift(sim_clicks, imps),
            "has_winner": len(winner_rows) > 0,
            "winner_is_top_ctr": (
                bool(winner_rows.ctr.max() == g.ctr.max())
                if len(winner_rows) else np.nan
            ),
        })
    tests = pd.DataFrame(rows)
    tests["q_value"] = multipletests(tests.p_value, method="fdr_bh")[1]
    tests["sig_raw"] = tests.p_value < 0.05
    tests["sig_fdr"] = tests.q_value < 0.05

    picked = tests[tests.has_winner]
    summary = {
        "dataset": dataset,
        "tests": int(len(tests)),
        "arms": int(len(arms)),
        "impressions": int(tests.impressions.sum()),
        "median_arms_per_test": float(tests.n_arms.median()),
        "median_impressions_per_test": float(tests.impressions.median()),
        "median_ctr": float(tests.pooled_ctr.median()),
        "share_sig_raw": float(tests.sig_raw.mean()),
        "share_sig_fdr": float(tests.sig_fdr.mean()),
        "median_observed_lift": float(tests.observed_lift.median()),
        "median_null_lift": float(tests.null_lift.median()),
        "tests_with_editor_winner": int(len(picked)),
        "share_winner_is_top_ctr": float(picked.winner_is_top_ctr.mean()),
        "share_editor_winner_tests_sig_fdr": float(picked.sig_fdr.mean()),
    }
    out = ROOT / "results"
    tests.to_csv(out / f"tests_{dataset}.csv", index=False)
    (out / f"ab_summary_{dataset}.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "exploratory"), indent=2))
