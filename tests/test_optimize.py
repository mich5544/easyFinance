import numpy as np
import pandas as pd

from portfolio_tool.optimize import min_variance, max_sharpe


def test_min_variance_long_only():
    mean = pd.Series([0.1, 0.2], index=["A", "B"])
    cov = pd.DataFrame([[0.05, 0.0], [0.0, 0.2]], index=["A", "B"], columns=["A", "B"])
    res = min_variance(mean, cov, allow_short=False)
    assert np.isclose(res.weights.sum(), 1.0)
    assert (res.weights >= 0).all()


def test_max_sharpe_long_only():
    mean = pd.Series([0.1, 0.2], index=["A", "B"])
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.09]], index=["A", "B"], columns=["A", "B"])
    res = max_sharpe(mean, cov, risk_free_rate=0.0, allow_short=False)
    assert np.isclose(res.weights.sum(), 1.0)
    assert (res.weights >= 0).all()
