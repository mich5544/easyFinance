from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from . import analytics, data, optimize, persistence, reporting
from .symbol_resolver import resolve_symbols
from .utils import get_logger, normalize_tickers

logger = get_logger()


class StudyError(Exception):
    pass


def run_study(config: Dict[str, Any]) -> Dict[str, Any]:
    tickers = normalize_tickers(config.get("tickers", []))
    assets = config.get("assets")
    if assets is None:
        assets = [{"user_symbol": t} for t in tickers]
    if not assets:
        raise StudyError("No tickers provided.")

    period = config.get("period", "5y")
    log_returns = bool(config.get("log_returns", False))
    risk_free_rate = float(config.get("risk_free_rate", 0.0))
    allow_short = bool(config.get("allow_short", False))
    mc_sims = int(config.get("mc_sims", 20000))
    study_name = str(config.get("study_name", "study"))
    bounds_enabled = bool(config.get("weight_bounds_enabled", True))
    min_weight = config.get("min_weight", 0.03)
    max_weight = config.get("max_weight", 0.25)
    shrinkage = float(config.get("cov_shrinkage", 0.1))
    drawdown_threshold = config.get("max_drawdown_threshold")
    w_prev = config.get("w_prev")
    turnover_lambda = float(config.get("turnover_lambda", 0.0))

    if bounds_enabled:
        min_weight = float(min_weight)
        max_weight = float(max_weight)
    else:
        min_weight = None
        max_weight = None


    base_dir = Path(config.get("base_dir", Path.cwd()))
    resolved_assets = resolve_symbols(assets, base_dir=base_dir, target_currency=config.get("currency"))
    yahoo_tickers = [a.yahoo_symbol for a in resolved_assets if a.yahoo_symbol]
    if len(yahoo_tickers) < 2:
        raise StudyError(
            "Not enough valid assets after symbol resolution. Please verify tickers."
        )

    prices, valid_tickers = data.download_prices(yahoo_tickers, period=period)
    returns = analytics.compute_returns(prices, use_log=log_returns)
    mean_returns = analytics.annualized_mean(returns)
    cov_matrix = analytics.annualized_cov(returns)
    cov_matrix = analytics.shrink_covariance(cov_matrix, shrinkage)
    corr_matrix = returns.corr()

    if bounds_enabled:
        n_assets = len(valid_tickers)
        if min_weight * n_assets > 1.0 or max_weight * n_assets < 1.0:
            raise StudyError("Weight bounds are infeasible for the number of assets.")
        if min_weight > max_weight:
            raise StudyError("min_weight cannot be greater than max_weight.")

    benchmark = {
        "enabled": bool(config.get("benchmark_enabled", True)),
        "ticker": str(config.get("benchmark_ticker", "VWCE.DE")).strip().upper(),
        "status": "Disabled",
        "return": None,
        "volatility": None,
        "sharpe": None,
        "years": None,
    }
    if benchmark["enabled"]:
        if not benchmark["ticker"]:
            benchmark["status"] = "Disabled (empty)"
        else:
            bench_series = data.download_price_series(benchmark["ticker"], period=period)
            if bench_series is None or bench_series.empty:
                benchmark["status"] = "Download failed"
            else:
                aligned = bench_series.loc[bench_series.index.intersection(prices.index)]
                if aligned.shape[0] < 5:
                    benchmark["status"] = "N/A (dati insufficienti)"
                else:
                    if isinstance(aligned, pd.DataFrame):
                        series = aligned.iloc[:, 0].rename("benchmark")
                    else:
                        series = aligned.rename("benchmark")
                    span_days = (series.index.max() - series.index.min()).days
                    bench_returns = analytics.compute_returns(
                        series.to_frame(), use_log=log_returns
                    )["benchmark"]
                    bench_return = float(bench_returns.mean() * analytics.TRADING_DAYS)
                    bench_vol = float(bench_returns.std() * np.sqrt(analytics.TRADING_DAYS))
                    bench_sharpe = (
                        (bench_return - risk_free_rate) / bench_vol if bench_vol > 0 else np.nan
                    )
                    benchmark.update(
                        {
                            "status": "OK",
                            "return": bench_return,
                            "volatility": bench_vol,
                            "sharpe": bench_sharpe,
                            "years": round(span_days / 365.25, 2),
                        }
                    )

    w_prev_arr = np.asarray(w_prev) if w_prev is not None else None
    min_var = optimize.min_variance(
        mean_returns,
        cov_matrix,
        allow_short,
        bounds_enabled=bounds_enabled,
        min_weight=min_weight,
        max_weight=max_weight,
        w_prev=w_prev_arr,
        turnover_lambda=turnover_lambda,
    )
    max_sharpe = optimize.max_sharpe(
        mean_returns,
        cov_matrix,
        risk_free_rate,
        allow_short,
        bounds_enabled=bounds_enabled,
        min_weight=min_weight,
        max_weight=max_weight,
        w_prev=w_prev_arr,
        turnover_lambda=turnover_lambda,
    )
    frontier = optimize.efficient_frontier(
        mean_returns,
        cov_matrix,
        allow_short,
        bounds_enabled=bounds_enabled,
        min_weight=min_weight,
        max_weight=max_weight,
        w_prev=w_prev_arr,
        turnover_lambda=turnover_lambda,
    )
    mc_df = optimize.monte_carlo_portfolios(
        mean_returns,
        cov_matrix,
        risk_free_rate,
        num_portfolios=mc_sims,
        allow_short=allow_short,
        bounds_enabled=bounds_enabled,
        min_weight=min_weight,
        max_weight=max_weight,
    )

    w_min = pd.Series(min_var.weights, index=valid_tickers, name="weight")
    w_max = pd.Series(max_sharpe.weights, index=valid_tickers, name="weight")

    def portfolio_series(weights: np.ndarray) -> pd.Series:
        series = returns @ weights
        if log_returns:
            series = np.exp(series) - 1
        return series

    port_min_returns = portfolio_series(min_var.weights)
    port_max_returns = portfolio_series(max_sharpe.weights)
    risk_min = analytics.var_cvar(port_min_returns)
    risk_max = analytics.var_cvar(port_max_returns)

    if drawdown_threshold is not None:
        threshold = float(drawdown_threshold)
        frontier_filtered = []
        for target, vol, weights in frontier:
            dd = analytics.max_drawdown(portfolio_series(weights))
            if dd <= threshold:
                frontier_filtered.append((target, vol, weights))
        frontier = frontier_filtered

        drawdowns = []
        for weights in mc_df["weights"]:
            dd = analytics.max_drawdown(portfolio_series(weights))
            drawdowns.append(dd)
        mc_df = mc_df.assign(max_drawdown=drawdowns)
        mc_df = mc_df[mc_df["max_drawdown"] <= threshold].reset_index(drop=True)

    output_dir = persistence.study_dir(base_dir, study_name)

    config_out = {
        **config,
        "tickers": valid_tickers,
        "period": period,
        "log_returns": log_returns,
        "risk_free_rate": risk_free_rate,
        "allow_short": allow_short,
        "mc_sims": mc_sims,
        "weight_bounds_enabled": bounds_enabled,
        "min_weight": min_weight,
        "max_weight": max_weight,
        "cov_shrinkage": shrinkage,
        "max_drawdown_threshold": drawdown_threshold,
        "turnover_lambda": turnover_lambda,
        "benchmark_enabled": benchmark["enabled"],
        "benchmark_ticker": benchmark["ticker"],
    }

    report_paths = reporting.build_reports(
        output_dir,
        config={**config_out, "resolved_assets": [a.__dict__ for a in resolved_assets]},
        prices=prices,
        returns=returns,
        cov=cov_matrix,
        corr=corr_matrix,
        mc_df=mc_df,
        frontier=frontier,
        w_min=w_min,
        w_max=w_max,
        benchmark=benchmark,
    )

    report_paths_out = {
        "figures": {k: str(v) for k, v in report_paths.get("figures", {}).items()},
        "excel": str(report_paths.get("excel", "")),
        "frontier_weights": str(report_paths.get("frontier_weights", "")),
    }

    outputs = {
        "min_variance": min_var.performance,
        "max_sharpe": max_sharpe.performance,
        "risk_metrics": {
            "min_variance": risk_min.__dict__,
            "max_sharpe": risk_max.__dict__,
        },
        "figures": report_paths_out["figures"],
        "excel": report_paths_out["excel"],
    }

    persistence.save_study(
        base_dir=base_dir,
        study_name=study_name,
        config=config_out,
        data={
            "prices": prices,
            "returns": returns,
            "cov": cov_matrix,
            "corr": corr_matrix,
            "frontier_weights": report_paths.get("frontier_weights"),
        },
        outputs=outputs,
        output_dir=output_dir,
    )

    logger.info("Study completed for %s", ", ".join(valid_tickers))
    return {
        "tickers": valid_tickers,
        "prices": prices,
        "returns": returns,
        "mean_returns": mean_returns,
        "cov": cov_matrix,
        "corr": corr_matrix,
        "min_variance": min_var,
        "max_sharpe": max_sharpe,
        "frontier": frontier,
        "mc_df": mc_df,
        "risk_metrics": {"min_variance": risk_min, "max_sharpe": risk_max},
        "report_paths": report_paths_out,
        "benchmark": benchmark,
    }
