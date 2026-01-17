# Portfolio Tool (Markowitz)

Desktop tool for Modern Portfolio Theory using Yahoo Finance data. Main UI is Tkinter; CLI is optional for automation.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run UI (main entry point)

```bash
cd portfolio_tool
python -m portfolio_tool.ui
```

## CLI

```bash
cd portfolio_tool
python -m portfolio_tool.cli run --tickers "AAPL,MSFT,SPY" --period 5y --risk-free 0.00
python -m portfolio_tool.cli list-studies
python -m portfolio_tool.cli load --study NAME
```

## Notes

- Yahoo Finance data can be incomplete for some tickers (especially CFDs). The tool skips assets without enough data.
- Markowitz is a mathematical framework, not a guarantee of future performance.
