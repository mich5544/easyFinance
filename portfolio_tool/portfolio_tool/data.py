from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

from .utils import get_logger

logger = get_logger()


class DataDownloadError(Exception):
    pass


def download_price_series(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
) -> pd.Series | None:
    if not ticker:
        return None
    try:
        df = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            threads=False,
            progress=False,
        )
    except Exception as exc:
        logger.warning("Benchmark download failed for %s: %s", ticker, exc)
        return None

    if df is None or df.empty:
        return None
    if "Adj Close" in df.columns:
        series = df["Adj Close"].copy()
        series.name = ticker
    elif "Close" in df.columns:
        series = df["Close"].copy()
        series.name = ticker
        logger.warning("Adj Close not available for %s; using Close.", ticker)
    else:
        return None

    series = series.dropna()
    return series if not series.empty else None


def get_date_ranges(
    tickers: List[str],
    period: str = "5y",
    interval: str = "1d",
) -> Dict[str, Dict[str, str]]:
    if not tickers:
        return {}

    df = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    ranges: Dict[str, Dict[str, str]] = {}
    for ticker in tickers:
        if len(tickers) == 1:
            sub = df
        else:
            if df.empty or ticker not in df.columns.get_level_values(0):
                continue
            sub = df[ticker]

        if sub is None or sub.empty:
            retry = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                auto_adjust=False,
                threads=False,
                progress=False,
            )
            sub = retry

        if sub is None or sub.empty:
            continue

        if "Adj Close" in sub.columns:
            series = sub["Adj Close"].copy()
            series.name = ticker
        elif "Close" in sub.columns:
            series = sub["Close"].copy()
            series.name = ticker
        else:
            continue

        series = series.dropna()
        if series.empty:
            continue

        ranges[ticker] = {
            "start": str(series.index.min().date()),
            "end": str(series.index.max().date()),
        }

    return ranges


def download_prices(
    tickers: List[str],
    period: str = "5y",
    interval: str = "1d",
) -> Tuple[pd.DataFrame, List[str]]:
    if not tickers:
        raise DataDownloadError("No tickers provided.")

    logger.info("Downloading data for %s", ", ".join(tickers))
    df = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    if df.empty:
        raise DataDownloadError("No data returned from Yahoo Finance.")

    prices = pd.DataFrame()
    valid_tickers: List[str] = []
    skipped: List[str] = []

    for ticker in tickers:
        if len(tickers) == 1:
            sub = df
        else:
            if ticker not in df.columns.get_level_values(0):
                logger.warning("Ticker %s not found in response.", ticker)
                skipped.append(f"{ticker} (not found)")
                continue
            sub = df[ticker]

        if sub is None or sub.empty:
            # Yahoo can fail in multi-ticker mode; retry single ticker.
            logger.warning("Retrying %s as single download.", ticker)
            retry = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                auto_adjust=False,
                threads=False,
                progress=False,
            )
            if retry is None or retry.empty:
                logger.warning("No data returned for %s on retry.", ticker)
                skipped.append(f"{ticker} (empty)")
                continue
            sub = retry

        if "Adj Close" in sub.columns:
            series = sub["Adj Close"].copy()
            series.name = ticker
        elif "Close" in sub.columns:
            series = sub["Close"].copy()
            series.name = ticker
            logger.warning("Adj Close not available for %s; using Close.", ticker)
        else:
            logger.warning("No price field for %s; skipping.", ticker)
            skipped.append(f"{ticker} (no price field)")
            continue

        series = series.dropna()
        if series.shape[0] < 5:
            logger.warning("Not enough data for %s; skipping.", ticker)
            skipped.append(f"{ticker} (insufficient data)")
            continue

        prices = pd.concat([prices, series], axis=1)
        valid_tickers.append(ticker)

    if prices.empty or len(valid_tickers) < 2:
        detail = ""
        if skipped:
            detail = f" Skipped: {', '.join(skipped)}."
        raise DataDownloadError(
            "Not enough valid tickers with data. Need at least 2 assets." + detail
        )

    prices = prices.dropna(how="any")
    dropped = set(valid_tickers) - set(prices.columns)
    if dropped:
        logger.warning("Dropped tickers after alignment: %s", ", ".join(dropped))

    logger.info("Aligned price data shape: %s", prices.shape)
    return prices, list(prices.columns)
