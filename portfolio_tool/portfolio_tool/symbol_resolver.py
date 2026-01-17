from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yfinance as yf

from .utils import get_logger

logger = get_logger()


@dataclass
class ResolvedAsset:
    user_symbol: str
    yahoo_symbol: str
    source: str
    exchange: str
    currency: str
    name: str | None = None
    isin: str | None = None


EU_EXCHANGES = {
    "MIL",
    "PAR",
    "XETRA",
    "LSE",
    "AMS",
    "SWX",
    "BME",
    "BIT",
}

SUFFIXES = [".L", ".DE", ".MI", ".PA", ".AS", ".SW", ".MC", ".ST"]


def _load_cache(cache_path: Path) -> Dict[str, Dict[str, str]]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="ascii"))
    except json.JSONDecodeError:
        logger.warning("Invalid symbol cache, ignoring: %s", cache_path)
        return {}


def _save_cache(cache_path: Path, cache: Dict[str, Dict[str, str]]) -> None:
    cache_path.write_text(json.dumps(cache, indent=2), encoding="ascii")


def _search_candidates(query: str) -> List[Dict]:
    try:
        search = yf.Search(query, max_results=10)
    except Exception as exc:
        logger.warning("Yahoo search failed for %s: %s", query, exc)
        return []
    return list(search.quotes or [])


def _is_valid_symbol(symbol: str) -> bool:
    try:
        hist = yf.Ticker(symbol).history(period="1mo", auto_adjust=False)
    except Exception:
        return False
    return hist is not None and not hist.empty


def _score_candidate(
    candidate: Dict,
    target_currency: Optional[str],
    prefer_ucits: bool,
    user_symbol: str,
) -> int:
    score = 0
    currency = str(candidate.get("currency") or "").upper()
    exchange = str(candidate.get("exchange") or "").upper()
    name = str(candidate.get("shortname") or candidate.get("longname") or "").upper()
    symbol = str(candidate.get("symbol") or "").upper()

    if target_currency and currency == target_currency.upper():
        score += 10
    if symbol == user_symbol.upper():
        score += 8
    if prefer_ucits and "UCITS" in name and exchange in EU_EXCHANGES:
        score += 5
    if exchange in EU_EXCHANGES:
        score += 2
    return score


def resolve_symbols(
    assets: List[Dict],
    base_dir: Path,
    target_currency: Optional[str] = None,
) -> List[ResolvedAsset]:
    cache_path = base_dir / "symbol_cache.json"
    cache = _load_cache(cache_path)
    resolved: List[ResolvedAsset] = []

    for asset in assets:
        user_symbol = str(asset.get("user_symbol") or "").strip().upper()
        isin = str(asset.get("isin") or "").strip().upper() or None
        name = str(asset.get("name") or "").strip() or None
        cache_key = isin or user_symbol

        if cache_key in cache:
            cached = cache[cache_key]
            resolved.append(
                ResolvedAsset(
                    user_symbol=user_symbol,
                    yahoo_symbol=cached["yahoo_symbol"],
                    source=cached.get("source", "CACHE"),
                    exchange=cached.get("exchange", ""),
                    currency=cached.get("currency", ""),
                    name=name,
                    isin=isin,
                )
            )
            continue

        if user_symbol and _is_valid_symbol(user_symbol):
            resolved_asset = ResolvedAsset(
                user_symbol=user_symbol,
                yahoo_symbol=user_symbol,
                source="DIRECT",
                exchange="",
                currency="",
                name=name,
                isin=isin,
            )
            resolved.append(resolved_asset)
            cache[cache_key] = {
                "yahoo_symbol": user_symbol,
                "source": "DIRECT",
                "exchange": "",
                "currency": "",
            }
            continue

        candidates: List[Dict] = []
        source = ""
        if isin:
            candidates = _search_candidates(isin)
            source = "ISIN"
        if not candidates and name:
            candidates = _search_candidates(name)
            source = "NAME"

        prefer_ucits = bool(name and "UCITS" in name.upper())
        valid_candidates = []
        for cand in candidates:
            symbol = cand.get("symbol")
            if not symbol:
                continue
            if _is_valid_symbol(symbol):
                valid_candidates.append(cand)

        if valid_candidates:
            scored = sorted(
                valid_candidates,
                key=lambda c: (
                    -_score_candidate(c, target_currency, prefer_ucits, user_symbol),
                    str(c.get("symbol") or ""),
                ),
            )
            best = scored[0]
            yahoo_symbol = str(best.get("symbol"))
            resolved_asset = ResolvedAsset(
                user_symbol=user_symbol,
                yahoo_symbol=yahoo_symbol,
                source=source,
                exchange=str(best.get("exchange") or ""),
                currency=str(best.get("currency") or ""),
                name=name,
                isin=isin,
            )
            resolved.append(resolved_asset)
            if resolved_asset.yahoo_symbol != user_symbol:
                logger.warning(
                    "Resolved %s to %s via %s",
                    user_symbol,
                    resolved_asset.yahoo_symbol,
                    source,
                )
            cache[cache_key] = {
                "yahoo_symbol": yahoo_symbol,
                "source": source,
                "exchange": resolved_asset.exchange,
                "currency": resolved_asset.currency,
            }
            continue

        # Fallback: try suffixes on the user symbol.
        if user_symbol:
            for suffix in SUFFIXES:
                candidate = f"{user_symbol}{suffix}"
                if _is_valid_symbol(candidate):
                    resolved_asset = ResolvedAsset(
                        user_symbol=user_symbol,
                        yahoo_symbol=candidate,
                        source="SUFFIX",
                        exchange="",
                        currency="",
                        name=name,
                        isin=isin,
                    )
                    resolved.append(resolved_asset)
                    logger.warning("Resolved %s to %s via SUFFIX", user_symbol, candidate)
                    cache[cache_key] = {
                        "yahoo_symbol": candidate,
                        "source": "SUFFIX",
                        "exchange": "",
                        "currency": "",
                    }
                    break
            else:
                logger.warning("Unable to resolve %s", user_symbol)

    _save_cache(cache_path, cache)
    return resolved
