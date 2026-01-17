import numpy as np
import pandas as pd

from portfolio_tool.analytics import annualized_cov, annualized_mean, compute_returns, portfolio_performance


def test_annualized_mean_cov():
    prices = pd.DataFrame(
        {
            "A": [100, 101, 102, 103, 104],
            "B": [200, 198, 202, 205, 207],
        }
    )
    returns = compute_returns(prices, use_log=False)
    mean = annualized_mean(returns)
    cov = annualized_cov(returns)

    assert mean.shape[0] == 2
    assert cov.shape == (2, 2)


def test_portfolio_performance():
    mean = pd.Series([0.1, 0.2], index=["A", "B"])
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.09]], index=["A", "B"], columns=["A", "B"])
    weights = np.array([0.5, 0.5])
    perf = portfolio_performance(weights, mean, cov, risk_free_rate=0.0)
    assert np.isclose(perf["return"], 0.15)
    assert np.isclose(perf["variance"], 0.0325)
