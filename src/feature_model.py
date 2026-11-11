"""Which headline features change click rate?

Only compares headlines inside the same test with the same image, so the
story and picture are held fixed.

Model: Poisson regression of clicks with log(impressions) as an offset and one
fixed effect per (test, image) stratum. The stratum effects are solved out in
closed form, which leaves a multinomial model: given how many clicks a stratum
got in total, which headlines got them? exp(coef) - 1 is the % change in click
rate. Standard errors are clustered by test.

With click rates around 1%, this matches a logistic regression with stratum
dummies (checked in tests/check_model.py) but runs in seconds on 40k+ arms.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).parent))
from features import FEATURES, LABELS, add_features  # noqa: E402
from load import ROOT, load  # noqa: E402


def fit_poisson_fe(X, clicks, imps, strata, clusters):
    """Return coefficients and cluster-robust covariance."""
    s_idx = pd.factorize(strata)[0]
    g_idx = pd.factorize(clusters)[0]
    n_s, k = s_idx.max() + 1, X.shape[1]
    C = np.bincount(s_idx, weights=clicks, minlength=n_s)  # clicks per stratum
    log_imps = np.log(imps)

    def parts(b):
        eta = X @ b + log_imps
        # subtract the stratum max before exp() to avoid overflow
        m = np.exp(eta - pd.Series(eta).groupby(s_idx).transform("max").values)
        W = np.bincount(s_idx, weights=m, minlength=n_s)
        p = m / W[s_idx]                       # share of stratum clicks expected
        return p

    def centered(p):
        # X minus its click-share-weighted mean within each stratum
        xbar = np.zeros((n_s, k))
        for j in range(k):
            xbar[:, j] = np.bincount(s_idx, weights=p * X[:, j], minlength=n_s)
        return X - xbar[s_idx]

    # Newton's method: gradient and Hessian are exact, so this converges fast.
    b = np.zeros(k)
    converged = False
    for _ in range(50):
        p = parts(b)
        Xc = centered(p)
        grad = Xc.T @ (clicks - C[s_idx] * p)
        H = (Xc * (C[s_idx] * p)[:, None]).T @ Xc   # negative Hessian
        step = np.linalg.solve(H, grad)
        b = b + step
        if np.max(np.abs(step)) < 1e-10:
            converged = True
            break
    p = parts(b)
    Xc = centered(p)
    H = (Xc * (C[s_idx] * p)[:, None]).T @ Xc

    # Scores per observation, summed by cluster (test)
    score = Xc * (clicks - C[s_idx] * p)[:, None]
    n_g = g_idx.max() + 1
    S = np.zeros((n_g, k))
    for j in range(k):
        S[:, j] = np.bincount(g_idx, weights=score[:, j], minlength=n_g)
    Hinv = np.linalg.inv(H)
    V = Hinv @ (S.T @ S) @ Hinv * n_g / (n_g - 1)
    return b, V, converged


def run(dataset: str = "exploratory") -> pd.DataFrame:
    con = load(dataset)
    df = add_features(con.sql("SELECT * FROM headline_strata").df())
    df["stratum"] = df.test_id + "_" + df.image_id.fillna("none")
    feats = list(FEATURES)

    b, V, ok = fit_poisson_fe(df[feats].to_numpy(), df.clicks.to_numpy(float),
                              df.impressions.to_numpy(float), df.stratum,
                              df.test_id)
    assert ok, "optimizer did not converge"
    se = np.sqrt(np.diag(V))
    z = b / se
    res = pd.DataFrame({
        "feature": feats,
        "label": [LABELS[f] for f in feats],
        "share_of_headlines": [df[f].gt(0).mean() if f != "words_per_5"
                               else np.nan for f in feats],
        "coef": b,
        "se": se,
        "p_value": 2 * norm.sf(np.abs(z)),
        "ctr_change": np.exp(b) - 1,
        "ctr_change_lo": np.exp(b - 1.96 * se) - 1,
        "ctr_change_hi": np.exp(b + 1.96 * se) - 1,
    })
    res["p_holm"] = multipletests(res.p_value, method="holm")[1]
    res["dataset"] = dataset
    n = {"arms": len(df), "strata": int(df.stratum.nunique()),
         "tests": int(df.test_id.nunique()),
         "impressions": int(df.impressions.sum())}
    out = ROOT / "results"
    res.to_csv(out / f"features_{dataset}.csv", index=False)
    (out / f"features_n_{dataset}.json").write_text(json.dumps(n))
    res.attrs["n"] = n
    return res


if __name__ == "__main__":
    ds = sys.argv[1] if len(sys.argv) > 1 else "exploratory"
    r = run(ds)
    print(r.attrs["n"])
    with pd.option_context("display.width", 200, "display.float_format", "{:.4f}".format):
        print(r[["feature", "share_of_headlines", "ctr_change", "ctr_change_lo",
                 "ctr_change_hi", "p_value", "p_holm"]])
