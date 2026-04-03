"""
╔══════════════════════════════════════════════════════╗
║          FINBOT - Your Personal Finance Assistant     ║
║          Built with Python, yfinance, matplotlib      ║
╚══════════════════════════════════════════════════════╝

Install dependencies before running:
    pip install yfinance pandas matplotlib rich

Run:
    python finance_assistant.py
"""

import json
import os
import sys
import datetime
from pathlib import Path

# ── Third-party (install via pip) ──────────────────────────────────────────────
try:
    import yfinance as yf
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError as e:
    print(f"\n[ERROR] Missing library: {e}")
    print("Please run:  pip install yfinance pandas matplotlib rich\n")
    sys.exit(1)

# ── Globals ────────────────────────────────────────────────────────────────────
console = Console()
DATA_FILE = Path("finbot_data.json")
BOT_NAME  = "FinBot"

BANNER = f"""
[bold cyan]╔══════════════════════════════════════════════════╗
║   💰  {BOT_NAME} — Your Personal Finance Assistant  ║
║        Type [yellow]help[/yellow] to see all commands             [bold cyan]║
╚══════════════════════════════════════════════════╝[/bold cyan]
"""

# ── Persistent data helpers ────────────────────────────────────────────────────

def load_data() -> dict:
    """Load user data from local JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "name": None,
        "portfolio": {},          # {"AAPL": {"shares": 10, "buy_price": 150.0}}
        "savings": {},            # {"Emergency Fund": 5000.0}
        "subscriptions": {},      # {"Netflix": {"amount": 15.99, "billing": "monthly"}}
        "budget": {},             # {"Food": 500.0, "Rent": 1200.0}
        "expenses": [],           # [{"category": "Food", "amount": 45.0, "date": "2024-01-01", "note": ""}]
    }

def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Greeting ───────────────────────────────────────────────────────────────────

def greet(data: dict) -> None:
    console.print(BANNER)
    if data["name"]:
        console.print(f"[bold green]Welcome back, {data['name']}! 👋[/bold green]\n")
    else:
        name = console.input("[bold yellow]Hi! I'm FinBot. What's your name? → [/bold yellow]").strip()
        data["name"] = name or "Friend"
        save_data(data)
        console.print(f"\n[bold green]Nice to meet you, {data['name']}! Let's get your finances organised. 🚀[/bold green]\n")

# ── Help ───────────────────────────────────────────────────────────────────────

COMMANDS = {
    "stock  <TICKER>":          "Plot a stock chart (e.g. stock AAPL)",
    "stock  <TICKER> <PERIOD>": "Plot with period: 1mo 3mo 6mo 1y 2y 5y (e.g. stock TSLA 6mo)",
    "quote  <TICKER>":          "Get live price + key stats",
    "add    <TICKER> <SHARES> <BUY_PRICE>": "Add stock to your portfolio",
    "remove <TICKER>":          "Remove stock from portfolio",
    "portfolio":                "Show your portfolio with live P&L",
    "savings":                  "View all savings goals",
    "savings add <NAME> <AMOUNT>": "Add / update a savings goal",
    "savings remove <NAME>":    "Remove a savings goal",
    "subs":                     "View all subscriptions",
    "subs add <NAME> <AMOUNT> <monthly|yearly>": "Add a subscription",
    "subs remove <NAME>":       "Remove a subscription",
    "budget":                   "View budget categories",
    "budget set <CATEGORY> <AMOUNT>": "Set a monthly budget",
    "expense <CATEGORY> <AMOUNT> [NOTE]": "Log an expense",
    "report":                   "Monthly spending report",
    "summary":                  "Full financial summary",
    "name":                     "Change your name",
    "clear":                    "Clear the screen",
    "exit / quit":              "Exit FinBot",
}

def show_help() -> None:
    table = Table(title="📖 FinBot Commands", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    table.add_column("Command", style="yellow", no_wrap=True)
    table.add_column("Description", style="white")
    for cmd, desc in COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)

# ── Stock helpers ──────────────────────────────────────────────────────────────

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"}

def fetch_ticker(symbol: str):
    """Return yfinance Ticker object."""
    return yf.Ticker(symbol.upper())

def plot_stock(symbol: str, period: str = "6mo") -> None:
    """Download history and plot a candlestick-style chart."""
    symbol = symbol.upper()
    if period not in VALID_PERIODS:
        console.print(f"[red]Unknown period '{period}'. Choose from: {', '.join(sorted(VALID_PERIODS))}[/red]")
        return

    console.print(f"[cyan]Fetching {symbol} ({period})...[/cyan]")
    ticker = fetch_ticker(symbol)
    hist = ticker.history(period=period)

    if hist.empty:
        console.print(f"[red]No data found for '{symbol}'. Check the ticker symbol.[/red]")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                   gridspec_kw={"height_ratios": [3, 1]},
                                   facecolor="#0d1117")
    fig.suptitle(f"{symbol}  —  {period}", color="white", fontsize=15, fontweight="bold")

    for ax in (ax1, ax2):
        ax.set_facecolor("#0d1117")
        ax.tick_params(colors="gray")
        ax.spines[:].set_color("#30363d")

    close = hist["Close"]
    dates = hist.index

    # Price line with fill
    color_line = "#3fb950" if close.iloc[-1] >= close.iloc[0] else "#f85149"
    ax1.plot(dates, close, color=color_line, linewidth=1.5, label="Close")
    ax1.fill_between(dates, close, close.min() * 0.98, alpha=0.15, color=color_line)

    # Moving averages
    if len(close) >= 20:
        ax1.plot(dates, close.rolling(20).mean(), color="#58a6ff", linewidth=0.9,
                 linestyle="--", label="MA20", alpha=0.8)
    if len(close) >= 50:
        ax1.plot(dates, close.rolling(50).mean(), color="#d29922", linewidth=0.9,
                 linestyle="--", label="MA50", alpha=0.8)

    # Annotations
    high_val = close.max()
    low_val  = close.min()
    ax1.annotate(f"H: ${high_val:.2f}", xy=(dates[close.argmax()], high_val),
                 color="#3fb950", fontsize=8, ha="center")
    ax1.annotate(f"L: ${low_val:.2f}", xy=(dates[close.argmin()], low_val),
                 color="#f85149", fontsize=8, ha="center")

    ax1.set_ylabel("Price (USD)", color="gray", fontsize=10)
    ax1.legend(loc="upper left", framealpha=0.3, fontsize=8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

    # Volume bars
    vol_colors = ["#3fb950" if c >= o else "#f85149"
                  for c, o in zip(hist["Close"], hist["Open"])]
    ax2.bar(dates, hist["Volume"], color=vol_colors, alpha=0.7, width=1)
    ax2.set_ylabel("Volume", color="gray", fontsize=9)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))

    plt.tight_layout()
    plt.savefig(f"{symbol}_chart.png", dpi=130, bbox_inches="tight", facecolor="#0d1117")
    plt.show()
    console.print(f"[green]Chart saved as [bold]{symbol}_chart.png[/bold][/green]")

def show_quote(symbol: str) -> None:
    symbol = symbol.upper()
    console.print(f"[cyan]Fetching quote for {symbol}...[/cyan]")
    ticker = fetch_ticker(symbol)
    info = ticker.fast_info

    try:
        price     = info.last_price
        prev      = info.previous_close
        change    = price - prev
        pct       = (change / prev) * 100
        mktcap    = getattr(info, "market_cap", None)
        volume    = getattr(info, "last_volume", None)

        color = "green" if change >= 0 else "red"
        arrow = "▲" if change >= 0 else "▼"

        table = Table(title=f"📈 {symbol} Live Quote", box=box.SIMPLE_HEAD, border_style="cyan")
        table.add_column("Metric", style="bold white")
        table.add_column("Value", style=color)

        table.add_row("Price",          f"${price:.2f}")
        table.add_row("Change",         f"{arrow} ${abs(change):.2f}  ({pct:+.2f}%)")
        table.add_row("Prev Close",     f"${prev:.2f}")
        table.add_row("Market Cap",     f"${mktcap/1e9:.2f}B" if mktcap else "N/A")
        table.add_row("Volume",         f"{volume:,}" if volume else "N/A")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Could not fetch quote: {e}[/red]")

# ── Portfolio ──────────────────────────────────────────────────────────────────

def show_portfolio(data: dict) -> None:
    port = data["portfolio"]
    if not port:
        console.print("[yellow]Your portfolio is empty. Use [bold]add <TICKER> <SHARES> <BUY_PRICE>[/bold] to add stocks.[/yellow]")
        return

    table = Table(title="📊 Your Portfolio", box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    for col in ("Ticker", "Shares", "Buy Price", "Current", "Value", "P&L", "Return %"):
        table.add_column(col, justify="right" if col != "Ticker" else "left")

    total_invested = 0.0
    total_value    = 0.0

    for symbol, info in port.items():
        shares    = info["shares"]
        buy_price = info["buy_price"]
        try:
            cur_price = fetch_ticker(symbol).fast_info.last_price
        except Exception:
            cur_price = buy_price  # fallback

        value    = shares * cur_price
        invested = shares * buy_price
        pl       = value - invested
        ret      = (pl / invested) * 100

        total_invested += invested
        total_value    += value

        c = "green" if pl >= 0 else "red"
        table.add_row(
            f"[bold]{symbol}[/bold]",
            str(shares),
            f"${buy_price:.2f}",
            f"${cur_price:.2f}",
            f"${value:,.2f}",
            f"[{c}]{'+'if pl>=0 else ''}{pl:,.2f}[/{c}]",
            f"[{c}]{ret:+.1f}%[/{c}]",
        )

    total_pl = total_value - total_invested
    table.add_section()
    c = "green" if total_pl >= 0 else "red"
    table.add_row(
        "[bold]TOTAL[/bold]", "", "",
        "", f"[bold]${total_value:,.2f}[/bold]",
        f"[{c}][bold]{total_pl:+,.2f}[/bold][/{c}]",
        f"[{c}][bold]{(total_pl/total_invested*100):+.1f}%[/bold][/{c}]",
    )
    console.print(table)

def add_stock(data: dict, symbol: str, shares: float, buy_price: float) -> None:
    symbol = symbol.upper()
    data["portfolio"][symbol] = {"shares": shares, "buy_price": buy_price}
    save_data(data)
    console.print(f"[green]Added {shares} shares of {symbol} @ ${buy_price:.2f} ✔[/green]")

def remove_stock(data: dict, symbol: str) -> None:
    symbol = symbol.upper()
    if symbol in data["portfolio"]:
        del data["portfolio"][symbol]
        save_data(data)
        console.print(f"[green]Removed {symbol} from portfolio ✔[/green]")
    else:
        console.print(f"[red]{symbol} not in portfolio.[/red]")

# ── Savings ────────────────────────────────────────────────────────────────────

def show_savings(data: dict) -> None:
    savings = data["savings"]
    if not savings:
        console.print("[yellow]No savings goals yet. Use [bold]savings add <NAME> <AMOUNT>[/bold].[/yellow]")
        return
    table = Table(title="💵 Savings Goals", box=box.ROUNDED, border_style="green", header_style="bold green")
    table.add_column("Goal", style="bold white")
    table.add_column("Amount", justify="right", style="green")
    total = 0.0
    for name, amt in savings.items():
        table.add_row(name, f"${amt:,.2f}")
        total += amt
    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", f"[bold]${total:,.2f}[/bold]")
    console.print(table)

def savings_add(data: dict, name: str, amount: float) -> None:
    data["savings"][name] = amount
    save_data(data)
    console.print(f"[green]Savings goal '{name}' set to ${amount:,.2f} ✔[/green]")

def savings_remove(data: dict, name: str) -> None:
    if name in data["savings"]:
        del data["savings"][name]
        save_data(data)
        console.print(f"[green]Removed savings goal '{name}' ✔[/green]")
    else:
        console.print(f"[red]Savings goal '{name}' not found.[/red]")

# ── Subscriptions ──────────────────────────────────────────────────────────────

def show_subs(data: dict) -> None:
    subs = data["subscriptions"]
    if not subs:
        console.print("[yellow]No subscriptions tracked yet. Use [bold]subs add <NAME> <AMOUNT> <monthly|yearly>[/bold].[/yellow]")
        return
    table = Table(title="📦 Subscriptions", box=box.ROUNDED, border_style="magenta", header_style="bold magenta")
    table.add_column("Service", style="bold white")
    table.add_column("Amount", justify="right")
    table.add_column("Billing")
    table.add_column("Monthly Cost", justify="right", style="yellow")

    total_monthly = 0.0
    for name, info in subs.items():
        amt     = info["amount"]
        billing = info["billing"]
        monthly = amt if billing == "monthly" else amt / 12
        total_monthly += monthly
        table.add_row(name, f"${amt:.2f}", billing, f"${monthly:.2f}")

    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", "", "", f"[bold]${total_monthly:.2f}/mo[/bold]")
    console.print(table)
    console.print(f"[dim]Annual subscription spend: [bold]${total_monthly*12:,.2f}[/bold][/dim]")

def subs_add(data: dict, name: str, amount: float, billing: str) -> None:
    billing = billing.lower()
    if billing not in ("monthly", "yearly"):
        console.print("[red]Billing must be 'monthly' or 'yearly'.[/red]")
        return
    data["subscriptions"][name] = {"amount": amount, "billing": billing}
    save_data(data)
    console.print(f"[green]Subscription '{name}' added: ${amount:.2f}/{billing} ✔[/green]")

def subs_remove(data: dict, name: str) -> None:
    if name in data["subscriptions"]:
        del data["subscriptions"][name]
        save_data(data)
        console.print(f"[green]Removed subscription '{name}' ✔[/green]")
    else:
        console.print(f"[red]Subscription '{name}' not found.[/red]")

# ── Budget & Expenses ──────────────────────────────────────────────────────────

def show_budget(data: dict) -> None:
    budget   = data["budget"]
    expenses = data["expenses"]
    if not budget:
        console.print("[yellow]No budget set. Use [bold]budget set <CATEGORY> <AMOUNT>[/bold].[/yellow]")
        return

    # Summarise current-month spend per category
    now = datetime.datetime.now()
    spent = {}
    for e in expenses:
        try:
            d = datetime.datetime.fromisoformat(e["date"])
        except Exception:
            continue
        if d.year == now.year and d.month == now.month:
            cat = e["category"]
            spent[cat] = spent.get(cat, 0) + e["amount"]

    table = Table(title=f"📋 Budget — {now.strftime('%B %Y')}", box=box.ROUNDED,
                  border_style="yellow", header_style="bold yellow")
    table.add_column("Category", style="bold white")
    table.add_column("Budget", justify="right")
    table.add_column("Spent", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Status")

    for cat, limit in budget.items():
        used      = spent.get(cat, 0)
        remaining = limit - used
        pct       = (used / limit * 100) if limit else 0
        if pct < 70:
            status = "[green]✔ On track[/green]"
        elif pct < 100:
            status = "[yellow]⚠ Near limit[/yellow]"
        else:
            status = "[red]✖ Over budget[/red]"
        table.add_row(cat, f"${limit:,.2f}", f"${used:,.2f}",
                      f"${remaining:,.2f}", status)
    console.print(table)

def budget_set(data: dict, category: str, amount: float) -> None:
    data["budget"][category] = amount
    save_data(data)
    console.print(f"[green]Budget for '{category}' set to ${amount:,.2f}/month ✔[/green]")

def log_expense(data: dict, category: str, amount: float, note: str = "") -> None:
    today = datetime.date.today().isoformat()
    data["expenses"].append({"category": category, "amount": amount,
                              "date": today, "note": note})
    save_data(data)
    console.print(f"[green]Expense logged: {category} — ${amount:.2f} on {today} ✔[/green]")

def monthly_report(data: dict) -> None:
    expenses = data["expenses"]
    now      = datetime.datetime.now()
    monthly  = [e for e in expenses
                if datetime.datetime.fromisoformat(e["date"]).year  == now.year
                and datetime.datetime.fromisoformat(e["date"]).month == now.month]

    if not monthly:
        console.print("[yellow]No expenses logged this month.[/yellow]")
        return

    totals: dict[str, float] = {}
    for e in monthly:
        totals[e["category"]] = totals.get(e["category"], 0) + e["amount"]

    table = Table(title=f"🧾 Spending Report — {now.strftime('%B %Y')}",
                  box=box.ROUNDED, border_style="cyan", header_style="bold cyan")
    table.add_column("Category", style="bold white")
    table.add_column("Spent", justify="right", style="yellow")
    for cat, amt in sorted(totals.items(), key=lambda x: -x[1]):
        table.add_row(cat, f"${amt:,.2f}")
    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", f"[bold]${sum(totals.values()):,.2f}[/bold]")
    console.print(table)

    # Bar chart via matplotlib
    fig, ax = plt.subplots(figsize=(9, 4), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    cats = list(totals.keys())
    vals = [totals[c] for c in cats]
    bars = ax.barh(cats, vals, color=["#3fb950","#58a6ff","#d29922","#bc8cff","#f85149",
                                       "#79c0ff","#ffa657"][:len(cats)])
    ax.set_xlabel("Amount ($)", color="gray")
    ax.tick_params(colors="gray")
    ax.spines[:].set_color("#30363d")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                f"${val:.0f}", va="center", color="white", fontsize=9)
    plt.title(f"Spending — {now.strftime('%B %Y')}", color="white")
    plt.tight_layout()
    plt.savefig("spending_report.png", dpi=120, bbox_inches="tight", facecolor="#0d1117")
    plt.show()
    console.print("[green]Chart saved as [bold]spending_report.png[/bold][/green]")

# ── Full Summary ───────────────────────────────────────────────────────────────

def full_summary(data: dict) -> None:
    console.rule("[bold cyan]💼 Financial Summary[/bold cyan]")

    # Savings total
    total_savings = sum(data["savings"].values())

    # Subscription monthly cost
    monthly_subs = sum(
        v["amount"] if v["billing"] == "monthly" else v["amount"] / 12
        for v in data["subscriptions"].values()
    )

    # This month expenses
    now = datetime.datetime.now()
    monthly_spend = sum(
        e["amount"] for e in data["expenses"]
        if datetime.datetime.fromisoformat(e["date"]).year  == now.year
        and datetime.datetime.fromisoformat(e["date"]).month == now.month
    )

    # Portfolio value (uses cached buy price if fetch fails)
    port_value = 0.0
    port_invested = 0.0
    for sym, info in data["portfolio"].items():
        try:
            cur = fetch_ticker(sym).fast_info.last_price
        except Exception:
            cur = info["buy_price"]
        port_value    += info["shares"] * cur
        port_invested += info["shares"] * info["buy_price"]

    panel_text = (
        f"[bold white]👤 Name:[/bold white]           {data['name']}\n"
        f"[bold white]💵 Total Savings:[/bold white]  [green]${total_savings:,.2f}[/green]\n"
        f"[bold white]📊 Portfolio Value:[/bold white] [cyan]${port_value:,.2f}[/cyan]"
        + (f"  ([green]+${port_value-port_invested:,.2f}[/green])" if port_value >= port_invested
           else f"  ([red]-${port_invested-port_value:,.2f}[/red])")
        + f"\n[bold white]📦 Monthly Subs:[/bold white]   [yellow]${monthly_subs:.2f}[/yellow]"
          f"  (${monthly_subs*12:.2f}/yr)\n"
        f"[bold white]🧾 This Month:[/bold white]     [magenta]${monthly_spend:,.2f}[/magenta] spent\n"
        f"\n[bold white]💰 Net Worth Est:[/bold white]  "
        f"[bold green]${total_savings + port_value:,.2f}[/bold green]"
    )
    console.print(Panel(panel_text, title="[bold cyan]Overview[/bold cyan]",
                        border_style="cyan", expand=False))

# ── Command dispatcher ─────────────────────────────────────────────────────────

def dispatch(line: str, data: dict) -> None:
    parts = line.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()

    # ─ help ──────────────────────────────────────────────────────────────────
    if cmd == "help":
        show_help()

    # ─ stock ─────────────────────────────────────────────────────────────────
    elif cmd == "stock":
        if len(parts) < 2:
            console.print("[red]Usage: stock <TICKER> [period][/red]")
        elif len(parts) == 2:
            plot_stock(parts[1])
        else:
            plot_stock(parts[1], parts[2])

    # ─ quote ─────────────────────────────────────────────────────────────────
    elif cmd == "quote":
        if len(parts) < 2:
            console.print("[red]Usage: quote <TICKER>[/red]")
        else:
            show_quote(parts[1])

    # ─ add stock ─────────────────────────────────────────────────────────────
    elif cmd == "add":
        try:
            add_stock(data, parts[1], float(parts[2]), float(parts[3]))
        except (IndexError, ValueError):
            console.print("[red]Usage: add <TICKER> <SHARES> <BUY_PRICE>[/red]")

    # ─ remove stock ──────────────────────────────────────────────────────────
    elif cmd == "remove":
        if len(parts) < 2:
            console.print("[red]Usage: remove <TICKER>[/red]")
        else:
            remove_stock(data, parts[1])

    # ─ portfolio ─────────────────────────────────────────────────────────────
    elif cmd == "portfolio":
        show_portfolio(data)

    # ─ savings ───────────────────────────────────────────────────────────────
    elif cmd == "savings":
        if len(parts) == 1:
            show_savings(data)
        elif parts[1] == "add" and len(parts) >= 4:
            # savings add Emergency Fund 5000  → name may be multi-word
            try:
                amount = float(parts[-1])
                name   = " ".join(parts[2:-1])
                savings_add(data, name, amount)
            except ValueError:
                console.print("[red]Usage: savings add <NAME> <AMOUNT>[/red]")
        elif parts[1] == "remove" and len(parts) >= 3:
            savings_remove(data, " ".join(parts[2:]))
        else:
            console.print("[red]Usage: savings | savings add <NAME> <AMT> | savings remove <NAME>[/red]")

    # ─ subscriptions ─────────────────────────────────────────────────────────
    elif cmd == "subs":
        if len(parts) == 1:
            show_subs(data)
        elif parts[1] == "add" and len(parts) >= 5:
            try:
                billing = parts[-1]
                amount  = float(parts[-2])
                name    = " ".join(parts[2:-2])
                subs_add(data, name, amount, billing)
            except ValueError:
                console.print("[red]Usage: subs add <NAME> <AMOUNT> <monthly|yearly>[/red]")
        elif parts[1] == "remove" and len(parts) >= 3:
            subs_remove(data, " ".join(parts[2:]))
        else:
            console.print("[red]Usage: subs | subs add <NAME> <AMT> <billing> | subs remove <NAME>[/red]")

    # ─ budget ────────────────────────────────────────────────────────────────
    elif cmd == "budget":
        if len(parts) == 1:
            show_budget(data)
        elif parts[1] == "set" and len(parts) >= 4:
            try:
                amount   = float(parts[-1])
                category = " ".join(parts[2:-1])
                budget_set(data, category, amount)
            except ValueError:
                console.print("[red]Usage: budget set <CATEGORY> <AMOUNT>[/red]")
        else:
            console.print("[red]Usage: budget | budget set <CATEGORY> <AMOUNT>[/red]")

    # ─ expense ───────────────────────────────────────────────────────────────
    elif cmd == "expense":
        try:
            # expense Food 45.50 grocery run
            amount   = float(parts[2])
            category = parts[1]
            note     = " ".join(parts[3:]) if len(parts) > 3 else ""
            log_expense(data, category, amount, note)
        except (IndexError, ValueError):
            console.print("[red]Usage: expense <CATEGORY> <AMOUNT> [NOTE][/red]")

    # ─ report ────────────────────────────────────────────────────────────────
    elif cmd == "report":
        monthly_report(data)

    # ─ summary ───────────────────────────────────────────────────────────────
    elif cmd == "summary":
        full_summary(data)

    # ─ name ──────────────────────────────────────────────────────────────────
    elif cmd == "name":
        new_name = console.input("[yellow]Enter new name → [/yellow]").strip()
        if new_name:
            data["name"] = new_name
            save_data(data)
            console.print(f"[green]Name updated to {new_name} ✔[/green]")

    # ─ clear ─────────────────────────────────────────────────────────────────
    elif cmd == "clear":
        os.system("cls" if os.name == "nt" else "clear")

    # ─ exit ──────────────────────────────────────────────────────────────────
    elif cmd in ("exit", "quit", "q"):
        console.print(f"\n[bold cyan]Goodbye, {data['name']}! Stay financially fit 💪[/bold cyan]\n")
        sys.exit(0)

    else:
        console.print(f"[red]Unknown command '{cmd}'. Type [bold]help[/bold] for a list.[/red]")

# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    data = load_data()
    greet(data)
    console.print("[dim]Type [bold]help[/bold] to see all commands.[/dim]\n")

    while True:
        try:
            line = console.input(f"[bold cyan]{BOT_NAME}[/bold cyan] [dim]›[/dim] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[bold cyan]Goodbye, {data['name']}! 👋[/bold cyan]\n")
            break
        if line:
            dispatch(line, data)

if __name__ == "__main__":
    main()
