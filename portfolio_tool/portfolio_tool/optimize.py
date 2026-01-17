from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .analytics import portfolio_performance
from .utils import get_logger

logger = get_logger()


@dataclass
class OptimizationResult:
    weights: np.ndarray
    performance: dict


def _portfolio_variance(weights: np.ndarray, cov: pd.DataFrame) -> float:
    w = np.asarray(weights)
    return float(w @ cov.values @ w)


def _constraints_sum_to_one():
    return {"type": "eq", "fun": lambda w: np.sum(w) - 1}


def _build_bounds(
    n: int,
    allow_short: bool,
    bounds_enabled: bool,
    min_weight: float | None,
    max_weight: float | None,
):
    if bounds_enabled and min_weight is not None and max_weight is not None:
        return tuple((min_weight, max_weight) for _ in range(n))
    if allow_short:
        return None
    return tuple((0.0, 1.0) for _ in range(n))


def _turnover_penalty(weights: np.ndarray, w_prev: np.ndarray | None, lam: float) -> float:
    if w_prev is None or lam <= 0:
        return 0.0
    return float(lam * np.sum(np.abs(weights - w_prev)))


def min_variance(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    allow_short: bool = False,
    bounds_enabled: bool = False,
    min_weight: float | None = None,
    max_weight: float | None = None,
    w_prev: np.ndarray | None = None,
    turnover_lambda: float = 0.0,
) -> OptimizationResult:
    n = len(mean_returns)
    bounds = _build_bounds(n, allow_short, bounds_enabled, min_weight, max_weight)
    x0 = np.repeat(1 / n, n)

    def objective(weights: np.ndarray) -> float:
        return _portfolio_variance(weights, cov_matrix) + _turnover_penalty(
            weights, w_prev, turnover_lambda
        )

    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=[_constraints_sum_to_one()],
    )
    if not res.success:
        raise ValueError(f"Min variance optimization failed: {res.message}")

    perf = portfolio_performance(res.x, mean_returns, cov_matrix, risk_free_rate=0.0)
    return OptimizationResult(weights=res.x, performance=perf)


def max_sharpe(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
    allow_short: bool = False,
    bounds_enabled: bool = False,
    min_weight: float | None = None,
    max_weight: float | None = None,
    w_prev: np.ndarray | None = None,
    turnover_lambda: float = 0.0,
) -> OptimizationResult:
    n = len(mean_returns)
    bounds = _build_bounds(n, allow_short, bounds_enabled, min_weight, max_weight)
    x0 = np.repeat(1 / n, n)

    def neg_sharpe(weights: np.ndarray) -> float:
        perf = portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
        return -perf["sharpe"] + _turnover_penalty(weights, w_prev, turnover_lambda)

    res = minimize(
        neg_sharpe,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=[_constraints_sum_to_one()],
    )
    if not res.success:
        raise ValueError(f"Max Sharpe optimization failed: {res.message}")

    perf = portfolio_performance(res.x, mean_returns, cov_matrix, risk_free_rate)
    return OptimizationResult(weights=res.x, performance=perf)


def efficient_frontier(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    allow_short: bool = False,
    bounds_enabled: bool = False,
    min_weight: float | None = None,
    max_weight: float | None = None,
    w_prev: np.ndarray | None = None,
    turnover_lambda: float = 0.0,
    num_points: int = 50,
) -> List[Tuple[float, float, np.ndarray]]:
    n = len(mean_returns)
    bounds = _build_bounds(n, allow_short, bounds_enabled, min_weight, max_weight)
    x0 = np.repeat(1 / n, n)

    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), num_points)
    frontier = []

    for target in target_returns:
        constraints = [
            _constraints_sum_to_one(),
            {"type": "eq", "fun": lambda w, t=target: (w @ mean_returns.values) - t},
        ]
        def objective(weights: np.ndarray) -> float:
            return _portfolio_variance(weights, cov_matrix) + _turnover_penalty(
                weights, w_prev, turnover_lambda
            )

        res = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if res.success:
            vol = float(np.sqrt(_portfolio_variance(res.x, cov_matrix)))
            frontier.append((float(target), vol, res.x))
        else:
            logger.warning("Frontier target %.4f infeasible: %s", target, res.message)
    return frontier


def monte_carlo_portfolios(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float,
    num_portfolios: int = 20000,
    allow_short: bool = False,
    bounds_enabled: bool = False,
    min_weight: float | None = None,
    max_weight: float | None = None,
) -> pd.DataFrame:
    n = len(mean_returns)
    if bounds_enabled and (min_weight is None or max_weight is None):
        raise ValueError("Bounds enabled but min/max weights are not set.")

    if bounds_enabled:
        if allow_short:
            raise ValueError("Bounds with allow_short are not supported in Monte Carlo.")
        min_w = float(min_weight)
        max_w = float(max_weight)
        cap = max_w - min_w
        if cap < 0:
            raise ValueError("min_weight cannot be greater than max_weight.")
        weights = np.empty((num_portfolios, n), dtype=float)
        for i in range(num_portfolios):
            w = np.full(n, min_w, dtype=float)
            remaining = 1.0 - min_w * n
            order = np.random.permutation(n)
            for idx in order:
                if remaining <= 0:
                    break
                max_add = min(cap, remaining)
                add = np.random.random() * max_add
                w[idx] += add
                remaining -= add
            if remaining > 0:
                room = max_w - w
                total_room = room.sum()
                if total_room > 0:
                    w += room * (remaining / total_room)
            weights[i] = w
    else:
        if allow_short:
            raw = np.random.normal(0, 1, size=(num_portfolios, n))
            sums = raw.sum(axis=1)
            sums[sums == 0] = 1
            weights = raw / sums[:, None]
        else:
            weights = np.random.dirichlet(np.ones(n), size=num_portfolios)

    results = []
    for w in weights:
        perf = portfolio_performance(w, mean_returns, cov_matrix, risk_free_rate)
        results.append(
            {
                "return": perf["return"],
                "volatility": perf["volatility"],
                "sharpe": perf["sharpe"],
                "weights": w,
            }
        )

    return pd.DataFrame(results)
