"""Export what the web tool needs:
- web/effects.json: confirmatory feature effects (estimate + 95% CI)
- web/test_headlines.json: real headlines with the Python feature values,
  used to check that the JavaScript version detects features the same way.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from features import FEATURES, add_features  # noqa: E402
from load import ROOT, load  # noqa: E402

WEB = ROOT / "web"
WEB.mkdir(exist_ok=True)

res = pd.read_csv(ROOT / "results/features_confirmatory.csv")
n = json.loads((ROOT / "results/features_n_confirmatory.json").read_text())
effects = {
    "source": "Upworthy Research Archive, confirmatory set (2013-2015)",
    "comparisons": n["strata"],
    "features": [
        {
            "id": r.feature,
            "label": r.label,
            "change": round(r.ctr_change, 4),
            "low": round(r.ctr_change_lo, 4),
            "high": round(r.ctr_change_hi, 4),
            "significant": bool(r.p_holm < 0.05),
        }
        for r in res.itertuples()
    ],
}
(WEB / "effects.json").write_text(json.dumps(effects, indent=2))

# Test cases: a sample that includes every feature, plus some tricky ones.
df = add_features(load("exploratory").sql(
    "SELECT DISTINCT headline FROM headline_strata").df())
parts = [df.sample(150, random_state=0)]
for f in FEATURES:
    if f != "words_per_5":
        parts.append(df[df[f] > 0].sample(15, random_state=1))
cases = pd.concat(parts).drop_duplicates("headline")
cases["word_count"] = (cases.words_per_5 * 5).round().astype(int)
out = [
    {"headline": r.headline,
     "expected": {f: bool(getattr(r, f)) for f in FEATURES if f != "words_per_5"}
     | {"word_count": int(r.word_count)}}
    for r in cases.itertuples()
]
(WEB / "test_headlines.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"wrote effects.json ({len(effects['features'])} features) and "
      f"test_headlines.json ({len(out)} headlines)")
