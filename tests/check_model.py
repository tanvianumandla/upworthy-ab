"""Sanity check: the fast Poisson fixed-effects model should agree with a
standard logistic regression with one dummy per stratum (slow, so exploratory
data only)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from feature_model import run  # noqa: E402
from features import FEATURES, add_features  # noqa: E402
from load import load  # noqa: E402

fast = run("exploratory").set_index("feature")

con = load("exploratory")
df = add_features(con.sql("SELECT * FROM headline_strata").df())
df["stratum"] = df.test_id + "_" + df.image_id.fillna("none")
feats = list(FEATURES)
dummies = pd.get_dummies(df.stratum, drop_first=True, dtype=float)
X = sm.add_constant(pd.concat([df[feats], dummies], axis=1))
y = np.column_stack([df.clicks, df.impressions - df.clicks]).astype(float)
fit = sm.GLM(y, X, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(df.test_id)[0]})

cmp = pd.DataFrame({
    "fast_poisson_fe": fast.ctr_change,
    "logit_dummies": np.exp(fit.params[feats]) - 1,
    "fast_p": fast.p_value,
    "logit_p": fit.pvalues[feats],
})
print(cmp.round(4))
assert np.allclose(cmp.fast_poisson_fe, cmp.logit_dummies, atol=0.01), "models disagree"
print("OK: models agree within 1 percentage point")
