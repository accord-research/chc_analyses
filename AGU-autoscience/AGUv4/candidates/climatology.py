"""climatology.py — the trivial forecast: equal tercile probabilities, always.

This is the harness's self-test, not a research candidate. RPSS is defined as skill
relative to exactly this forecast, so it MUST score 0.0000 on every target, every
protocol, and every shuffle seed. Any other value means bench.py is wrong, and every
other number on the leaderboard is void until it is fixed.
"""
import numpy as np


def fit_predict(ctx):
    return np.full((len(ctx.test_years), 3), 1.0 / 3.0)
