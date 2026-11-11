"""Make the README figures from the files in results/."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from load import ROOT  # noqa: E402

# Palette: two categorical slots, checked for colorblind separation.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False,
})
FIG = ROOT / "figures"


def forest():
    exp = pd.read_csv(ROOT / "results/features_exploratory.csv")
    con = pd.read_csv(ROOT / "results/features_confirmatory.csv")
    order = con.sort_values("ctr_change").feature.tolist()
    y = {f: i for i, f in enumerate(order)}

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.axvline(0, color=INK2, lw=1)
    for df, color, marker, dy, name in [
        (exp, BLUE, "o", 0.17, "Exploratory (found here)"),
        (con, ORANGE, "s", -0.17, "Confirmatory (checked on new data)"),
    ]:
        ys = [y[f] + dy for f in df.feature]
        ax.hlines(ys, df.ctr_change_lo * 100, df.ctr_change_hi * 100,
                  color=color, lw=2)
        ax.scatter(df.ctr_change * 100, ys, color=color, marker=marker, s=50,
                   zorder=3, edgecolor=SURFACE, linewidth=1.5, label=name)
    for _, r in con.iterrows():
        ax.annotate(f"{r.ctr_change * 100:+.1f}%", (r.ctr_change_hi * 100, y[r.feature] - 0.17),
                    xytext=(6, 0), textcoords="offset points", va="center",
                    fontsize=9, color=INK2)
    labels = con.set_index("feature").label
    ax.set_yticks(range(len(order)), [labels[f] for f in order])
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Change in click rate vs. other headlines in the same test (%)")
    ax.set_title("What headline features change clicks?", loc="left",
                 fontsize=13, fontweight="bold", pad=24)
    ax.text(0, 1.025, "Dots = estimate, lines = 95% CI. Same story and image, only the headline differs.",
            transform=ax.transAxes, fontsize=9, color=INK2)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "feature_effects.png", dpi=200)
    plt.close(fig)


def lift_vs_noise():
    t = pd.read_csv(ROOT / "results/tests_confirmatory.csv")
    obs = (t.observed_lift.dropna() * 100).clip(upper=300)
    null = (t.null_lift.dropna() * 100).clip(upper=300)
    bins = np.arange(0, 305, 10)

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.hist(null, bins=bins, histtype="step", lw=2, color=BLUE,
            label="Pure noise (all headlines equal, simulated)")
    ax.hist(obs, bins=bins, histtype="step", lw=2, color=ORANGE,
            label="Actual tests")
    for vals, color, text, ha, dx in [(null, BLUE, "noise", "right", -3),
                                      (obs, ORANGE, "actual", "left", 3)]:
        m = vals.median()
        ax.axvline(m, color=color, lw=1, ls="--")
        ax.text(m + dx, ax.get_ylim()[1] * 0.90, f"median {text}: {m:.0f}%",
                color=INK2, fontsize=9, ha=ha)
    ax.set_xticks([0, 50, 100, 150, 200, 250, 300],
                  ["0", "50", "100", "150", "200", "250", "300+"])
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Best headline's click rate vs. worst headline's (% higher, capped at 300)")
    ax.set_ylabel("Number of tests")
    ax.set_title("About half of a typical 'winning' gap is noise", loc="left",
                 fontsize=13, fontweight="bold", pad=24)
    ax.text(0, 1.025, f"{len(t):,} confirmatory tests", transform=ax.transAxes,
            fontsize=9, color=INK2)
    ax.legend(loc="upper right", frameon=False, fontsize=9,
              bbox_to_anchor=(1, 0.85))
    fig.tight_layout()
    fig.savefig(FIG / "lift_vs_noise.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    forest()
    lift_vs_noise()
    print("saved", sorted(p.name for p in FIG.glob("*.png")))
