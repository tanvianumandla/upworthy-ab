"""Headline text features. Each is simple enough to check by eye."""
import re

import pandas as pd

FEATURES = {
    "question":        lambda h: "?" in h,
    "number":          lambda h: bool(re.search(r"\d", h)),
    "you":             lambda h: bool(re.search(r"\byou(r|'re|rself|'ll)?\b", h, re.I)),
    "this_these":      lambda h: bool(re.search(r"\b(this|these)\b", h, re.I)),
    "exclamation":     lambda h: "!" in h,
    "quote":           lambda h: bool(re.search(r"[\"“”]", h)),
    "words_per_5":     lambda h: len(h.split()) / 5,   # length, in units of 5 words
}

LABELS = {
    "question": "Asks a question (?)",
    "number": "Contains a number",
    "you": "Says 'you' / 'your'",
    "this_these": "Says 'this' / 'these'",
    "exclamation": "Has an exclamation mark",
    "quote": "Has a direct quote",
    "words_per_5": "+5 words longer",
}


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for name, fn in FEATURES.items():
        df[name] = df.headline.map(fn).astype(float)
    return df
