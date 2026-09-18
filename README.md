# 💰 FinBot — Your Personal Finance Assistant

A terminal-based personal finance assistant built in Python. FinBot tracks your stock portfolio with live prices via `yfinance`, manages savings goals, subscriptions, and budgets, logs expenses, and generates matplotlib charts — all through a friendly, `rich`-powered command-line interface.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Commands Reference](#commands-reference)
5. [Data Storage](#data-storage)
6. [Code Explanation](#code-explanation)
7. [Sample Output](#sample-output)
8. [Notes & Limitations](#notes--limitations)

---

## Features

- 📈 **Live stock charts** — candlestick-style price + volume charts with 20/50-day moving averages, saved as PNGs
- 💹 **Live quotes** — current price, change %, market cap, and volume for any ticker
- 📊 **Portfolio tracking** — live profit & loss on every holding, with totals
- 💵 **Savings goals** — track multiple named savings goals and their combined total
- 📦 **Subscription tracker** — monthly/yearly subscriptions normalized to monthly cost, plus annual projection
- 📋 **Budgeting** — per-category monthly budgets with live spend tracking and status (on track / near limit / over budget)
- 🧾 **Expense logging** — quick expense entries with category, amount, date, and optional note
- 📉 **Monthly spending reports** — category breakdown table plus a horizontal bar chart
- 💼 **Full financial summary** — a single dashboard view combining savings, portfolio, subscriptions, and monthly spend into a net worth estimate
- 💾 **Persistent local storage** — all data saved to a local JSON file between sessions

---

## Installation

**Requirements:** Python 3.8+

Install the dependencies:

```bash
pip install yfinance pandas matplotlib rich
```

Save the script as `finance_assistant.py`, then run:

```bash
python finance_assistant.py
```

---

## Usage

On first run, FinBot will ask for your name and create a local `finbot_data.json` file to persist your data between sessions:
$ python finance_assistant.py

╔══════════════════════════════════════════════════╗
║     💰 FinBot — Your Personal Finance Assistant  ║
║            Type help to see all commands         ║
╚══════════════════════════════════════════════════╝

Hi! I'm FinBot. What's your name? → Alex

Nice to meet you, Alex! Let's get your finances organised. 🚀

Type help to see all commands.

FinBot ›


From there, type commands at the `FinBot ›` prompt. Type `help` at any time to see the full command list.

---

## Commands Reference

| Command | Description |
|---|---|
| `stock <TICKER>` | Plot a stock chart (default 6-month period) |
| `stock <TICKER> <PERIOD>` | Plot with a specific period: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `ytd`, `max` |
| `quote <TICKER>` | Get a live price snapshot + key stats |
| `add <TICKER> <SHARES> <BUY_PRICE>` | Add a stock to your portfolio |
| `remove <TICKER>` | Remove a stock from your portfolio |
| `portfolio` | Show your portfolio with live profit & loss |
| `savings` | View all savings goals |
| `savings add <NAME> <AMOUNT>` | Add or update a savings goal |
| `savings remove <NAME>` | Remove a savings goal |
| `subs` | View all subscriptions |
| `subs add <NAME> <AMOUNT> <monthly\|yearly>` | Add a subscription |
| `subs remove <NAME>` | Remove a subscription |
| `budget` | View budget categories and current spend |
| `budget set <CATEGORY> <AMOUNT>` | Set a monthly budget for a category |
| `expense <CATEGORY> <AMOUNT> [NOTE]` | Log an expense |
| `report` | Generate a monthly spending report + chart |
| `summary` | Show a full financial summary |
| `name` | Change your saved name |
| `clear` | Clear the terminal screen |
| `exit` / `quit` / `q` | Exit FinBot |

**Examples:**
```
FinBot › add AAPL 10 150
FinBot › stock TSLA 1y
FinBot › quote MSFT
FinBot › savings add Emergency Fund 5000
FinBot › subs add Netflix 15.99 monthly
FinBot › budget set Food 500
FinBot › expense Food 45.50 grocery run
FinBot › summary

```

---

## Data Storage

All data is saved locally to `finbot_data.json` in the same directory as the script, and reloaded automatically the next time you run FinBot. It has the following structure:

```json
{
  "name": "Alex",
  "portfolio": {
    "AAPL": { "shares": 10.0, "buy_price": 150.0 }
  },
  "savings": {
    "Emergency Fund": 10000.0
  },
  "subscriptions": {
    "Netflix": { "amount": 15.99, "billing": "monthly" }
  },
  "budget": {
    "Food": 500.0
  },
  "expenses": [
    { "category": "Food", "amount": 45.5, "date": "2026-03-30", "note": "grocery run" }
  ]
}
```

> ⚠️ This file is saved in plain text with no encryption. Don't commit it to version control if it contains real financial data — consider adding `finbot_data.json` to your `.gitignore`.

---

## Code Explanation

### Imports & Setup

The script wraps all third-party imports (`yfinance`, `pandas`, `matplotlib`, `rich`) in a `try/except ImportError` block. If any are missing, it prints a clear install instruction and exits via `sys.exit(1)` rather than crashing with a raw traceback — a friendlier failure mode for a CLI tool aimed at non-developers.

Three globals are defined: a shared `rich` `Console()` instance used for all styled output, a `Path` pointing to the local JSON save file (`finbot_data.json`), and the bot's display name (`BOT_NAME`). A `BANNER` string using `rich`'s markup syntax (`[bold cyan]...[/bold cyan]`) is pre-built for the welcome screen.

### Persistent Data Helpers

`load_data()` checks whether `finbot_data.json` exists; if so, it loads and returns the parsed JSON. If not, it returns a default dictionary skeleton with empty `portfolio`, `savings`, `subscriptions`, `budget`, and `expenses` — establishing the schema the rest of the app relies on. `save_data()` is the mirror function, dumping the current in-memory `data` dict back to disk with `indent=2` for human-readable formatting. Every mutating command in the app calls `save_data()` immediately after changing state, so there's no separate "save" command — changes persist as soon as they happen.

### Greeting

`greet()` prints the banner, then checks `data["name"]`. On a returning user it prints a personalized welcome; on a first-time user it prompts for a name via `console.input()`, defaults to `"Friend"` if left blank, saves it immediately, and prints a confirmation. This is the only place user onboarding happens — from here on, `data["name"]` is assumed to exist.

### Command Registry & Help

`COMMANDS` is a dictionary mapping each command syntax string to a human-readable description. `show_help()` doesn't hardcode a help table — it iterates over `COMMANDS` and builds a `rich` `Table` dynamically, meaning any future command added to the dictionary automatically appears in `help` output without touching the display logic.

### Stock Helpers

`fetch_ticker()` is a one-line wrapper around `yf.Ticker(symbol.upper())`, centralizing the uppercase-normalization so every other function doesn't need to repeat it.

`plot_stock()` is the most involved function in the script:
1. Validates the requested `period` against a `VALID_PERIODS` set before making any network call, failing fast with a clear error listing valid options.
2. Downloads price history via `ticker.history(period=period)`; if the returned DataFrame is empty (e.g. an invalid ticker), it reports that and returns early rather than plotting garbage.
3. Builds a two-panel matplotlib figure (price on top, volume below) using a dark GitHub-style color scheme (`#0d1117` background).
4. Colors the price line green or red depending on whether the stock is up or down over the period, and shades the area under the line for visual weight.
5. Overlays 20-day and 50-day moving averages *only if* there's enough history to compute them (`len(close) >= 20` / `>= 50`), preventing errors on short time ranges like `1mo`.
6. Annotates the highest and lowest closing prices directly on the chart.
7. Colors each volume bar green/red based on whether that day closed up or down versus its open.
8. Saves the chart as `<SYMBOL>_chart.png` at 130 DPI before displaying it with `plt.show()`.

`show_quote()` pulls `ticker.fast_info` (a lighter-weight, faster-to-fetch snapshot than the full `.info` dict), computes the price change and percentage, and renders it all as a `rich` table with color-coded change values. It's wrapped in a `try/except` because `fast_info` fields aren't always populated for every ticker, and a failure here shouldn't crash the whole app.

### Portfolio

`show_portfolio()` iterates over every held position, fetches a **live** current price for each via `fast_info.last_price`, and falls back to the original `buy_price` if that fetch fails (e.g. due to a network hiccup) — this keeps the portfolio view usable even when offline, rather than crashing. It computes per-position value, profit/loss, and return %, color-coding each row green or red, then adds a totals row summing everything via `table.add_section()` for a visual divider.

`add_stock()` and `remove_stock()` are straightforward dictionary mutations against `data["portfolio"]`, each followed by `save_data()` and a confirmation message.

### Savings, Subscriptions, Budget & Expenses

These four sections follow the same consistent pattern: a `show_*()` function that renders a `rich` table (with a running total row), and `*_add()`/`*_remove()` functions that mutate the relevant dictionary and persist immediately.

Two are worth calling out specifically:
- **`subs_add()`** validates that `billing` is either `"monthly"` or `"yearly"` before saving, and `show_subs()` normalizes yearly subscriptions to a monthly-equivalent cost (`amount / 12`) so they can be summed meaningfully against monthly ones in the total.
- **`show_budget()`** cross-references `data["budget"]` against `data["expenses"]`, filtering expenses down to the *current calendar month only* (matching both `year` and `month` against `datetime.now()`), then computes a status per category: green "On track" under 70% spent, yellow "Near limit" under 100%, red "Over budget" at or above 100%.

`log_expense()` appends a new expense dict (with today's date auto-generated via `datetime.date.today().isoformat()`) to the `expenses` list — expenses are never edited or removed in this version, only added, so the list grows as an append-only log.

### Reports & Summary

`monthly_report()` filters `data["expenses"]` to the current month (same pattern as the budget view), aggregates spend per category into a `totals` dict, renders it as a sorted `rich` table (highest spend first), and then builds a horizontal bar chart of the same data with matplotlib, saved as `spending_report.png`.

`full_summary()` is the "everything at once" view: it sums savings, normalizes and sums subscription costs to a monthly figure, sums current-month expenses, and computes portfolio value (with the same live-price-with-fallback pattern used in `show_portfolio()`). All of this is composed into a single `rich` `Panel` with manually formatted text — including a rough **net worth estimate** as `total_savings + portfolio_value` (note: this does not subtract any debts or liabilities, since the app doesn't track those).

### Command Dispatcher

`dispatch()` is the router: it splits the raw input line on whitespace, lowercases the first token as the command name, and runs an `if/elif` chain matching it against every supported command. Several commands (like `savings add <NAME> <AMOUNT>`) support multi-word names — this is handled by taking the *last* token as the numeric amount and joining everything in between as the name (`" ".join(parts[2:-1])`), rather than assuming the name is always a single word. Malformed input (wrong argument count, non-numeric values) is caught with `try/except (IndexError, ValueError)` around each parse, producing a usage hint rather than a crash.

### Entry Point

`main()` loads persisted data, greets the user, and enters an infinite `while True:` read-eval loop, reading a line from `console.input()` and passing it to `dispatch()`. `KeyboardInterrupt` and `EOFError` (Ctrl+C / Ctrl+D) are caught explicitly to print a friendly goodbye instead of an ugly traceback when the user exits that way, in addition to the explicit `exit`/`quit`/`q` commands handled inside `dispatch()`.

---

## Sample Output

**`portfolio` command:**
                     📊 Your Portfolio
                     ```
FinBot › add AAPL 10 150
FinBot › stock TSLA 1y
FinBot › quote MSFT
FinBot › savings add Emergency Fund 5000
FinBot › subs add Netflix 15.99 monthly
FinBot › budget set Food 500
FinBot › expense Food 45.50 grocery run
FinBot › summary

┌────────┬────────┬───────────┬─────────┬───────────┬─────────┬──────────┐
│ Ticker │ Shares │ Buy Price │ Current │ Value     │ P&L     │ Return % │
├────────┼────────┼───────────┼─────────┼───────────┼─────────┼──────────┤
│ AAPL   │ 10     │ $150.00   │ $172.40 │ $1,724.00 │ +224.00 │ +14.9%   │
│ TSLA   │ 5      │ $200.00   │ $184.20 │ $921.00   │ -79.00  │ -7.9%    │
│ MSFT   │ 8      │ $310.00   │ $338.15 │ $2,705.20 │ +225.20 │ +7.3%    │
├────────┼────────┼───────────┼─────────┼───────────┼─────────┼──────────┤
│ TOTAL  │        │           │         │ $5,350.20 │ +370.20 │ +7.4%    │
└────────┴────────┴───────────┴─────────┴───────────┴─────────┴──────────┘

```
  
**`summary` command:**
```
╭──────────────────────── Overview ────────────────────────╮
│ 👤 Name: Alex                                           │
│ 💵 Total Savings: $10,000.00                             │
│ 📊 Portfolio Value: $5,350.20 (+$370.20)                 │
│ 📦 Monthly Subs: $27.57 ($330.84/yr)                     │
│ 🧾 This Month: $300.00 spent                              │
│                                                          │
│ 💰 Net Worth Est: $15,350.20                             │
╰─────────────────────────────────────────────────────────╯

```

**`stock TSLA 6mo` command:**

Fetches 6 months of TSLA price history and saves a two-panel chart (`TSLA_chart.png`) showing the closing price with 20/50-day moving averages on top, and color-coded daily volume bars below.

---

## Notes & Limitations

- Live prices depend entirely on `yfinance`, which scrapes Yahoo Finance — it can occasionally rate-limit or return incomplete data; the app falls back to your original buy price in the portfolio/summary views when a live fetch fails.
- Expenses can only be added, not edited or deleted, in the current version.
- Net worth calculation does not account for debts, liabilities, or illiquid assets.
- `finbot_data.json` is stored in plain text with no encryption — treat it accordingly if used with real data.
- The app is single-user and single-session; there's no multi-profile support.

---

## License

This project is provided as-is for personal/educational use.               
