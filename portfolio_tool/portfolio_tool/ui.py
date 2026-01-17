from __future__ import annotations

import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .main import run_study, StudyError
from .symbol_resolver import resolve_symbols
from . import data as data_module
from .persistence import list_studies, load_study
from .utils import normalize_tickers, get_logger

logger = get_logger()

TICKER_LIBRARY = {
    "ETF": {
        "Core": ["SPY", "QQQ", "IWM", "DIA", "VTI"],
        "Bonds": ["TLT", "IEF", "SHY", "LQD", "HYG"],
        "Commodities": ["GLD", "SLV", "USO"],
    },
    "Stocks": {
        "Tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META"],
        "AI": ["NVDA", "AMD", "AVGO", "SMCI", "PLTR"],
        "Healthcare": ["JNJ", "PFE", "MRK", "UNH"],
        "Finance": ["JPM", "BAC", "GS", "MS"],
        "Industry": ["CAT", "GE", "HON", "BA"],
        "Materials": ["LIN", "APD", "ECL", "FCX"],
    },
    "Crypto": {
        "Majors": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"],
        "Alt": ["ADA-USD", "XRP-USD", "DOT-USD", "AVAX-USD"],
    },
    "FX": {"Majors": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]},
}


class BrowseDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, on_add):
        super().__init__(master)
        self.title("Browse Tickers")
        self.geometry("520x420")
        self.resizable(False, False)
        self.on_add = on_add
        self.filtered = []

        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="ETF")
        self.group_var = tk.StringVar()

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=8)
        ttk.Label(search_frame, text="Search").pack(side="left")
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        ttk.Button(search_frame, text="Filter", command=self.update_list).pack(side="left")

        filters = ttk.Frame(self)
        filters.pack(fill="x", padx=10)
        ttk.Label(filters, text="Category").pack(side="left")
        ttk.Combobox(
            filters,
            textvariable=self.category_var,
            values=list(TICKER_LIBRARY.keys()),
            state="readonly",
            width=12,
        ).pack(side="left", padx=6)
        ttk.Label(filters, text="Group").pack(side="left")
        self.group_combo = ttk.Combobox(filters, textvariable=self.group_var, state="readonly", width=14)
        self.group_combo.pack(side="left", padx=6)

        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=14)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=8)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Add to list", command=self.add_selected).pack(side="left")
        ttk.Button(actions, text="Close", command=self.destroy).pack(side="right")

        self.category_var.trace_add("write", lambda *_: self.update_groups())
        self.group_var.trace_add("write", lambda *_: self.update_list())
        self.update_groups()
        self.update_list()

    def update_groups(self):
        category = self.category_var.get()
        groups = list(TICKER_LIBRARY.get(category, {}).keys())
        self.group_combo["values"] = groups
        if groups:
            self.group_var.set(groups[0])
        else:
            self.group_var.set("")

    def update_list(self):
        category = self.category_var.get()
        group = self.group_var.get()
        tickers = TICKER_LIBRARY.get(category, {}).get(group, [])
        query = self.search_var.get().strip().upper()
        if query:
            tickers = [t for t in tickers if query in t.upper()]
        self.listbox.delete(0, tk.END)
        for t in tickers:
            self.listbox.insert(tk.END, t)

    def add_selected(self):
        selected = [self.listbox.get(i) for i in self.listbox.curselection()]
        if selected:
            self.on_add(selected)


class StudyDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, studies, on_select):
        super().__init__(master)
        self.title("Load Study")
        self.geometry("360x320")
        self.resizable(False, False)
        self.on_select = on_select

        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, height=12)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for item in studies:
            self.listbox.insert(tk.END, item)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Load", command=self._load).pack(side="left")
        ttk.Button(actions, text="Close", command=self.destroy).pack(side="right")

    def _load(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.on_select(self.listbox.get(sel[0]))
        self.destroy()


class DataHorizonDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, assets_info):
        super().__init__(master)
        self.title("Data Horizon Options")
        self.geometry("520x420")
        self.resizable(False, False)
        self.result_drop = []
        self.assets_info = sorted(assets_info, key=lambda a: a["start"])

        ttk.Label(
            self,
            text="Some assets start later. Select assets to drop to extend history.",
        ).pack(fill="x", padx=10, pady=8)

        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=14, width=60)
        self.listbox.pack(fill="both", expand=True, padx=10)

        for item in self.assets_info:
            label = f"{item['yahoo_symbol']} ({item['user_symbol']}) start: {item['start']}"
            self.listbox.insert(tk.END, label)

        self.common_var = tk.StringVar()
        ttk.Label(self, textvariable=self.common_var).pack(fill="x", padx=10, pady=6)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=8)
        ttk.Button(actions, text="Keep all (use common window)", command=self._keep_all).pack(side="left")
        ttk.Button(actions, text="Apply selection", command=self._apply).pack(side="right")

        self.listbox.bind("<<ListboxSelect>>", lambda _evt: self._update_common_start())
        self._update_common_start()

    def _update_common_start(self):
        selected = set(self.listbox.curselection())
        remaining = [a for i, a in enumerate(self.assets_info) if i not in selected]
        if len(remaining) < 2:
            self.common_var.set("Need at least 2 assets after selection.")
            return
        common_start = max(a["start"] for a in remaining)
        self.common_var.set(f"Common start if applied: {common_start}")

    def _keep_all(self):
        self.result_drop = []
        self.destroy()

    def _apply(self):
        indices = self.listbox.curselection()
        self.result_drop = [self.assets_info[i]["yahoo_symbol"] for i in indices]
        self.destroy()

    def show(self):
        self.wait_window()
        return self.result_drop


class PortfolioUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Portfolio Tool - Markowitz Analyzer")
        self.geometry("1100x720")

        self._images = []
        self.report_paths = {}

        self._build_layout()

    def _build_layout(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.inputs_tab = ttk.Frame(notebook)
        self.results_tab = ttk.Frame(notebook)
        notebook.add(self.inputs_tab, text="Inputs")
        notebook.add(self.results_tab, text="Results")

        self._build_inputs(self.inputs_tab)
        self._build_results(self.results_tab)

    def _build_inputs(self, parent: ttk.Frame):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        row = 0
        ttk.Label(frame, text="Tickers (comma-separated)").grid(row=row, column=0, sticky="w")
        self.tickers_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.tickers_var, width=50).grid(row=row, column=1, sticky="w")
        ttk.Button(frame, text="Browse tickers", command=self.open_browse).grid(row=row, column=2, padx=6)

        row += 1
        ttk.Label(frame, text="Period").grid(row=row, column=0, sticky="w", pady=6)
        self.period_var = tk.StringVar(value="5y")
        ttk.Combobox(frame, textvariable=self.period_var, values=["1y", "3y", "5y", "max"], state="readonly").grid(
            row=row, column=1, sticky="w"
        )

        row += 1
        self.log_returns_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Log returns", variable=self.log_returns_var).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Risk-free rate (annual)").grid(row=row, column=0, sticky="w", pady=6)
        self.rf_var = tk.StringVar(value="0.00")
        ttk.Entry(frame, textvariable=self.rf_var, width=12).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Capital (0 = skip)").grid(row=row, column=0, sticky="w")
        self.capital_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.capital_var, width=12).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Currency").grid(row=row, column=0, sticky="w", pady=6)
        self.currency_var = tk.StringVar(value="USD")
        ttk.Entry(frame, textvariable=self.currency_var, width=12).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Monte Carlo simulations").grid(row=row, column=0, sticky="w")
        self.mc_var = tk.StringVar(value="20000")
        ttk.Entry(frame, textvariable=self.mc_var, width=12).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Benchmark ticker (Yahoo)").grid(row=row, column=0, sticky="w", pady=6)
        self.benchmark_var = tk.StringVar(value="VWCE.DE")
        ttk.Entry(frame, textvariable=self.benchmark_var, width=20).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Min weight").grid(row=row, column=0, sticky="w", pady=6)
        self.min_weight_var = tk.StringVar(value="0.03")
        ttk.Entry(frame, textvariable=self.min_weight_var, width=12).grid(row=row, column=1, sticky="w")
        ttk.Label(frame, text="Max weight").grid(row=row, column=2, sticky="w", padx=6)
        self.max_weight_var = tk.StringVar(value="0.25")
        ttk.Entry(frame, textvariable=self.max_weight_var, width=12).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frame, text="Max drawdown threshold").grid(row=row, column=0, sticky="w")
        self.max_dd_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.max_dd_var, width=12).grid(row=row, column=1, sticky="w")

        row += 1
        self.allow_short_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Allow short", variable=self.allow_short_var).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame, text="Study name").grid(row=row, column=0, sticky="w", pady=6)
        self.study_var = tk.StringVar(value="study")
        ttk.Entry(frame, textvariable=self.study_var, width=20).grid(row=row, column=1, sticky="w")

        row += 1
        actions = ttk.Frame(frame)
        actions.grid(row=row, column=0, columnspan=3, pady=12, sticky="w")
        ttk.Button(actions, text="Run analysis", command=self.run_analysis).pack(side="left")
        ttk.Button(actions, text="Load study", command=self.load_study).pack(side="left", padx=6)

        row += 1
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var, foreground="#0a5").grid(
            row=row, column=0, columnspan=3, sticky="w"
        )

    def _build_results(self, parent: ttk.Frame):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        results_notebook = ttk.Notebook(frame)
        results_notebook.pack(fill="both", expand=True)

        summary_tab = ttk.Frame(results_notebook)
        weights_tab = ttk.Frame(results_notebook)
        charts_tab = ttk.Frame(results_notebook)
        results_notebook.add(summary_tab, text="Summary")
        results_notebook.add(weights_tab, text="Weights")
        results_notebook.add(charts_tab, text="Charts")

        self.metrics_tree = ttk.Treeview(
            summary_tab,
            columns=("min_return", "min_vol", "min_sharpe", "max_return", "max_vol", "max_sharpe"),
            show="headings",
        )
        for col, label in zip(
            self.metrics_tree["columns"],
            ["MinVar Return", "MinVar Vol", "MinVar Sharpe", "MaxSharpe Return", "MaxSharpe Vol", "MaxSharpe Sharpe"],
        ):
            self.metrics_tree.heading(col, text=label)
            self.metrics_tree.column(col, width=140, anchor="center")
        self.metrics_tree.pack(fill="x", pady=6)

        self.benchmark_var_text = tk.StringVar(value="Benchmark: N/A")
        ttk.Label(summary_tab, textvariable=self.benchmark_var_text, foreground="#a35b00").pack(
            anchor="w", pady=4
        )

        self.weights_tree = ttk.Treeview(weights_tab, columns=("ticker", "min_w", "max_w"), show="headings", height=12)
        for col, label in zip(self.weights_tree["columns"], ["Ticker", "MinVar", "MaxSharpe"]):
            self.weights_tree.heading(col, text=label)
            self.weights_tree.column(col, width=140, anchor="center")
        self.weights_tree.pack(fill="both", expand=True, pady=6)

        charts_notebook = ttk.Notebook(charts_tab)
        charts_notebook.pack(fill="both", expand=True)
        self.chart_labels = {}
        self.chart_paths = {}
        for key, title in [
            ("prices", "Prices"),
            ("correlation", "Correlation"),
            ("monte_carlo", "Monte Carlo"),
            ("frontier", "Frontier"),
        ]:
            tab = ttk.Frame(charts_notebook)
            charts_notebook.add(tab, text=title)
            lbl = ttk.Label(tab, anchor="center")
            lbl.pack(fill="both", expand=True, padx=6, pady=6)
            self.chart_labels[key] = lbl

        charts_tab.bind("<Configure>", lambda _evt: self._refresh_charts())

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Save Excel As", command=self.save_excel_as).pack(side="left")
        ttk.Button(buttons, text="Open Study Folder", command=self.open_study_folder).pack(side="left", padx=6)

    def open_browse(self):
        BrowseDialog(self, self.add_tickers)

    def add_tickers(self, tickers):
        current = normalize_tickers(self.tickers_var.get())
        merged = list(dict.fromkeys(current + tickers))
        self.tickers_var.set(", ".join(merged))

    def _gather_config(self):
        max_dd = self.max_dd_var.get().strip()
        return {
            "tickers": self.tickers_var.get(),
            "period": self.period_var.get(),
            "log_returns": self.log_returns_var.get(),
            "risk_free_rate": float(self.rf_var.get()),
            "capital": float(self.capital_var.get()),
            "currency": self.currency_var.get().strip() or "USD",
            "mc_sims": int(self.mc_var.get()),
            "benchmark_enabled": True,
            "benchmark_ticker": self.benchmark_var.get().strip(),
            "min_weight": float(self.min_weight_var.get()),
            "max_weight": float(self.max_weight_var.get()),
            "max_drawdown_threshold": float(max_dd) if max_dd else None,
            "allow_short": self.allow_short_var.get(),
            "study_name": self.study_var.get().strip() or "study",
            "base_dir": str(Path.cwd()),
        }

    def run_analysis(self):
        self.status_var.set("Running analysis...")
        self._clear_results()

        def task():
            try:
                config = self._gather_config()
                assets = config.get("assets")
                if assets is None:
                    assets = [{"user_symbol": t} for t in normalize_tickers(config.get("tickers", ""))]

                base_dir = Path(config.get("base_dir", Path.cwd()))
                resolved = resolve_symbols(assets, base_dir=base_dir, target_currency=config.get("currency"))
                yahoo_symbols = [a.yahoo_symbol for a in resolved if a.yahoo_symbol]
                ranges = data_module.get_date_ranges(yahoo_symbols, period=config.get("period", "5y"))

                assets_info = []
                for asset in resolved:
                    if asset.yahoo_symbol in ranges:
                        info = ranges[asset.yahoo_symbol]
                        assets_info.append(
                            {
                                "user_symbol": asset.user_symbol,
                                "yahoo_symbol": asset.yahoo_symbol,
                                "start": info["start"],
                                "end": info["end"],
                                "name": asset.name,
                                "isin": asset.isin,
                            }
                        )

                if len(assets_info) < 2:
                    raise StudyError("Not enough valid assets after data check.")

                starts = [a["start"] for a in assets_info]
                if max(starts) != min(starts):
                    decision = {}
                    event = threading.Event()

                    def prompt():
                        dialog = DataHorizonDialog(self, assets_info)
                        decision["drop"] = dialog.show()
                        event.set()

                    self.after(0, prompt)
                    event.wait()

                    to_drop = decision.get("drop") or []
                    if to_drop:
                        assets = [
                            {
                                "user_symbol": a["user_symbol"],
                                "name": a["name"],
                                "isin": a["isin"],
                            }
                            for a in assets_info
                            if a["yahoo_symbol"] not in to_drop
                        ]
                        config["assets"] = assets

                result = run_study(config)
                self.after(0, lambda: self._update_results(result))
                self.after(0, lambda: self.status_var.set("Study completed and saved."))
            except (StudyError, Exception) as exc:
                logger.exception("Study failed")
                self.after(0, lambda: messagebox.showerror("Error", str(exc)))
                self.after(0, lambda: self.status_var.set("Failed."))

        threading.Thread(target=task, daemon=True).start()

    def _update_results(self, result):
        self._clear_results()
        min_perf = result["min_variance"].performance
        max_perf = result["max_sharpe"].performance
        self.metrics_tree.insert(
            "",
            "end",
            values=(
                f"{min_perf['return']:.4f}",
                f"{min_perf['volatility']:.4f}",
                f"{min_perf['sharpe']:.4f}",
                f"{max_perf['return']:.4f}",
                f"{max_perf['volatility']:.4f}",
                f"{max_perf['sharpe']:.4f}",
            ),
        )

        w_min = result["min_variance"].weights
        w_max = result["max_sharpe"].weights
        for ticker, wm, wx in zip(result["tickers"], w_min, w_max):
            self.weights_tree.insert("", "end", values=(ticker, f"{wm:.4f}", f"{wx:.4f}"))

        benchmark = result.get("benchmark") or {}
        if benchmark.get("status") == "OK":
            self.benchmark_var_text.set(
                "Benchmark {} | Return {:.4f} | Vol {:.4f} | Sharpe {:.4f}".format(
                    benchmark.get("ticker"),
                    benchmark.get("return", 0.0),
                    benchmark.get("volatility", 0.0),
                    benchmark.get("sharpe", 0.0),
                )
            )
        else:
            self.benchmark_var_text.set(
                f"Benchmark {benchmark.get('ticker', '')}: {benchmark.get('status', 'N/A')}"
            )

        figures = result["report_paths"].get("figures", {})
        self.chart_paths = figures
        self._refresh_charts()
        self.report_paths = result["report_paths"]

    def _clear_results(self):
        for tree in (self.metrics_tree, self.weights_tree):
            for row in tree.get_children():
                tree.delete(row)
        for lbl in self.chart_labels.values():
            lbl.configure(image="")
        self._images = []
        self.chart_paths = {}

    def _refresh_charts(self):
        if not self.chart_paths:
            return
        self._images = []
        for key, lbl in self.chart_labels.items():
            path = self.chart_paths.get(key)
            if not path:
                continue
            self._set_chart_image(lbl, path)

    def _set_chart_image(self, label: ttk.Label, path: str) -> None:
        try:
            img = tk.PhotoImage(file=path)
        except tk.TclError:
            logger.warning("Failed to load image: %s", path)
            return

        target_w = max(480, label.winfo_width())
        target_h = max(320, label.winfo_height())
        scale_w = max(1, int(img.width() / target_w))
        scale_h = max(1, int(img.height() / target_h))
        scale = max(scale_w, scale_h)
        if scale > 1:
            img = img.subsample(scale, scale)
        label.configure(image=img)
        self._images.append(img)

    def save_excel_as(self):
        excel_path = self.report_paths.get("excel")
        if not excel_path:
            messagebox.showinfo("Info", "Run a study first.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not dest:
            return
        Path(dest).write_bytes(Path(excel_path).read_bytes())
        messagebox.showinfo("Saved", f"Excel saved to {dest}")

    def open_study_folder(self):
        if not self.report_paths:
            messagebox.showinfo("Info", "Run a study first.")
            return
        folder = Path(self.report_paths.get("excel", "")).parent
        if folder.exists():
            os.startfile(folder)

    def load_study(self):
        base_dir = Path.cwd()
        _, studies = list_studies(base_dir)
        if not studies:
            messagebox.showinfo("Info", "No studies found.")
            return
        StudyDialog(self, studies, lambda choice: self._load_study(base_dir, choice))

    def _load_study(self, base_dir: Path, choice: str):
        info = load_study(base_dir, choice)
        messagebox.showinfo("Study Loaded", f"Loaded {choice}\nPath: {info['path']}")


def main():
    app = PortfolioUI()
    app.mainloop()


if __name__ == "__main__":
    main()
