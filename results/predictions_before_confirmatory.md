# Predictions locked before running the confirmatory data

Written: 2026-11-10 23:34 UTC, after the exploratory analysis and before
`python src/feature_model.py confirmatory` was ever run.

Each feature that passed Holm correction (p < 0.05) on the exploratory set is a
prediction. It "replicates" if the confirmatory estimate has the same sign and
Holm-corrected p < 0.05.

| Feature | Exploratory effect on CTR | Prediction |
|---|---|---|
| Asks a question (?) | -9.4% | lowers CTR |
| Has an exclamation mark | -12.1% | lowers CTR |
| Contains a number | +5.3% | raises CTR |
| Says 'this' / 'these' | +3.9% | raises CTR |
| +5 words longer | +6.4% | raises CTR |
| Says 'you' / 'your' | -0.2% (n.s.) | no prediction |
| Has a direct quote | -0.1% (n.s.) | no prediction |
