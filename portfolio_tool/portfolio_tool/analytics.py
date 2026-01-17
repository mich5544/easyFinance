from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .utils import get_logger

logger = get_logger()

TRADING_DAYS = 252


@dataclass
class RiskMetrics:
    max_drawdown: float
    var_95: float
    cvar_95: float


def compute_returns(prices: pd.DataFrame, use_log: bool) -> pd.DataFrame:
    if use_log:
        returns = np.log(prices / prices.shift(1)).dropna()
    else:
        returns = prices.pct_change().dropna()
    return returns


def annualized_mean(returns: pd.DataFrame) -> pd.Series:
    return returns.mean() * TRADING_DAYS


def annualized_cov(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.cov() * TRADING_DAYS


def shrink_covariance(cov: pd.DataFrame, shrinkage: float) -> pd.DataFrame:
    if shrinkage <= 0:
        return cov
    shrink = min(max(shrinkage, 0.0), 1.0)
    diag = pd.DataFrame(np.diag(np.diag(cov.values)), index=cov.index, columns=cov.columns)
    return (1 - shrink) * cov + shrink * diag


def portfolio_performance(
    weights: np.ndarray,
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
) -> Dict[str, float]:
    w = np.asarray(weights)
    port_return = float(w @ mean_returns.values)
    port_var = float(w @ cov_matrix.values @ w)
    port_vol = float(np.sqrt(port_var))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else np.nan
    return {
        "return": port_return,
        "volatility": port_vol,
        "variance": port_var,
        "sharpe": sharpe,
    }


def max_drawdown(series: pd.Series) -> float:
    cumulative = (1 + series).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return float(drawdown.min())


def var_cvar(returns: pd.Series, alpha: float = 0.95) -> RiskMetrics:
    if returns.empty:
        return RiskMetrics(max_drawdown=0.0, var_95=0.0, cvar_95=0.0)
    var_level = np.quantile(returns, 1 - alpha)
    tail = returns[returns <= var_level]
    cvar = tail.mean() if not tail.empty else var_level
    return RiskMetrics(max_drawdown=max_drawdown(returns), var_95=float(var_level), cvar_95=float(cvar))
