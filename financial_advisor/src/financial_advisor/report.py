"""Generate a monthly budget report as Markdown with Mermaid charts."""

import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

REPORTS_DIR = Path("/reports")
CATEGORIZED_FILE = REPORTS_DIR / "categorized_transactions.json"
CATEGORIES_FILE = REPORTS_DIR / "categories.json"
ACCOUNTS_FILE = REPORTS_DIR / "accounts.json"

# Excluded from income/expense analysis — money moving between accounts
TRANSFER_CATEGORIES = {"Internal transfers", "Swish transfers", "Family transfers"}
INCOME_CATEGORIES = {"Salary", "Tax refund", "Children & allowances", "Study allowance", "Interest"}


def fmt(amount: float) -> str:
    """Format as Swedish-style SEK amount: '23 527 kr'."""
    return f"{abs(amount):,.0f} kr".replace(",", " ")


def parse_ym(date_str: str) -> tuple[int, int]:
    d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    return d.year, d.month


def last_complete_month() -> tuple[int, int]:
    today = date.today()
    return (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)


def slug(text: str) -> str:
    s = text.lower().replace("&", "and")
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def theme_link(theme: str) -> str:
    return f"[{theme}](#theme-{slug(theme)})"


def cat_link(cat: str) -> str:
    return f"[{cat}](#cat-{slug(cat)})"


def resolve_account(description: str, account_map: dict[str, str]) -> str:
    """Return the display name for an account number embedded in a description, or the raw description."""
    key = re.sub(r"\s+", "", description)
    return account_map.get(key, description)


def main():
    if not CATEGORIZED_FILE.exists():
        print(f"ERROR: {CATEGORIZED_FILE} not found — run 'make categorize' first.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        try:
            t = datetime.strptime(sys.argv[1], "%Y-%m")
            report_year, report_month = t.year, t.month
        except ValueError:
            print(f"ERROR: use YYYY-MM format, got '{sys.argv[1]}'", file=sys.stderr)
            sys.exit(1)
    else:
        report_year, report_month = last_complete_month()

    month_label = f"{report_year}-{report_month:02d}"
    month_name = datetime(report_year, report_month, 1).strftime("%B %Y")

    accounts = json.loads(CATEGORIZED_FILE.read_text())

    cats_data = json.loads(CATEGORIES_FILE.read_text()) if CATEGORIES_FILE.exists() else {}
    super_map: dict[str, str] = cats_data.get("super_categories", {})
    force_expense: set[str] = set(cats_data.get("force_expense_categories", []))
    flow_rules: list[dict] = cats_data.get("flow_rules", [])
    monthly_limits: list[dict] = cats_data.get("monthly_limits", [])
    improvements: list[dict] = cats_data.get("improvements", [])
    exceptions: dict[str, dict] = {e["id"]: e for e in cats_data.get("discrepancy_exceptions", [])}
    excepted_ids: set[str] = set(exceptions)

    account_map: dict[str, str] = json.loads(ACCOUNTS_FILE.read_text()) if ACCOUNTS_FILE.exists() else {}

    def super_cat(category: str) -> str:
        return super_map.get(category, category)

    def account_link(name: str) -> str:
        return f"[{name}](#account-{slug(name)})"

    # Aggregate across all accounts for the target month
    income: dict[str, float] = defaultdict(float)
    expenses: dict[str, float] = defaultdict(float)
    super_expenses: dict[str, float] = defaultdict(float)
    account_summaries = []
    all_transactions = []   # budget transactions (income + expenses)
    all_transfers = []      # transfer transactions (excluded from budget)

    for account in accounts:
        acc_income = acc_expenses = acc_transfers = 0.0
        acc_cats: dict[str, float] = defaultdict(float)
        account_short = account["account"]

        for tx in account["transactions"]:
            if parse_ym(tx["date"]) != (report_year, report_month):
                continue
            amount = tx.get("amount") or 0.0
            category = tx.get("category", "Uncategorized")

            row = {
                "id": tx.get("id", ""),
                "date": tx["date"],
                "account": account_short,
                "merchant": tx.get("merchant") or tx.get("description", ""),
                "category": category,
                "super_category": super_cat(category),
                "amount": amount,
            }

            if category in TRANSFER_CATEGORIES:
                acc_transfers += amount
                all_transfers.append(row)
            elif category in INCOME_CATEGORIES and amount >= 0:
                income[category] += amount
                acc_income += amount
                all_transactions.append(row)
            elif category in force_expense or amount < 0:
                # force_expense categories are always expenses regardless of sign
                amt = -abs(amount)
                expenses[category] += amt
                super_expenses[super_cat(category)] += amt
                acc_cats[category] += amt
                acc_expenses += amt
                all_transactions.append(row)
            else:
                # Positive amount not recognised as income — treat as other inflow (transfer)
                acc_transfers += amount
                all_transfers.append(row)

        account_summaries.append({
            "name": account["account"],
            "income": acc_income,
            "expenses": acc_expenses,
            "transfers": acc_transfers,
            "categories": dict(acc_cats),
        })

    all_transactions.sort(key=lambda x: x["date"])

    total_income = sum(income.values())
    total_expenses = sum(expenses.values())
    net = total_income + total_expenses

    # Most negative first
    sorted_expenses = sorted(expenses.items(), key=lambda x: x[1])
    sorted_income = sorted(income.items(), key=lambda x: -x[1])

    # Collect ordered theme and category lists for the navigation index
    ordered_themes = [t for t, _ in sorted(super_expenses.items(), key=lambda x: x[1])]
    ordered_cats = [c for c, _ in sorted_expenses]

    def tx_row(tx: dict) -> str:
        sign = "" if tx["amount"] >= 0 else "−"
        return (
            f"| `{tx.get('id', '')}` | {tx['date']} | {account_link(tx['account'])} | {tx['merchant']} "
            f"| {theme_link(tx['super_category'])} | {cat_link(tx['category'])} | {sign}{fmt(tx['amount'])} |"
        )

    tx_header = ["| ID | Date | Account | Description | Theme | Category | SEK |", "|---|---|---|---|---|---|---|"]

    # Compute discrepancies before building output
    discrepancies: list[dict] = []

    for tx in all_transfers:
        if tx.get("id", "") in excepted_ids:
            continue
        if tx["amount"] >= 0:
            source = resolve_account(tx["merchant"], account_map)
            destination = tx["account"]
        else:
            source = tx["account"]
            destination = resolve_account(tx["merchant"], account_map)
        for rule in flow_rules:
            dest_check = rule.get("destination_contains", "").lower()
            if dest_check and dest_check not in destination.lower():
                continue
            allowed = rule.get("allowed_sources", [])
            if allowed and not any(s.lower() in source.lower() for s in allowed):
                discrepancies.append({
                    "kind": "unexpected_transfer",
                    "rule": rule["name"],
                    "detail": rule["description"],
                    "id": tx.get("id", ""),
                    "date": tx["date"],
                    "source": source,
                    "destination": destination,
                    "amount": tx["amount"],
                })

    for tx in all_transactions:
        if tx["category"] == "Uncategorized":
            discrepancies.append({
                "kind": "uncategorized",
                "rule": "Uncategorized transaction",
                "detail": "",
                "id": tx.get("id", ""),
                "date": tx["date"],
                "merchant": tx["merchant"],
                "account": tx["account"],
                "amount": tx["amount"],
            })

    for limit in monthly_limits:
        cat = limit["category"]
        cat_txs = [tx for tx in all_transactions if tx["category"] == cat and tx.get("id", "") not in excepted_ids]
        actual = abs(sum(tx["amount"] for tx in cat_txs))
        max_allowed = limit["max"]
        if actual > max_allowed:
            overage = actual - max_allowed
            discrepancies.append({
                "kind": "limit_exceeded",
                "rule": f"Monthly limit — {cat}",
                "detail": limit["description"],
                "category": cat,
                "actual": actual,
                "max": max_allowed,
                "overage": overage,
                "txs": cat_txs,
            })

    out = [f"# Budget — {month_name}", ""]

    # Discrepancies section — shown at the top so problems are visible immediately
    if discrepancies:
        out += [f"## Discrepancies — {len(discrepancies)} issue(s)", ""]
        unexpected = [d for d in discrepancies if d["kind"] == "unexpected_transfer"]
        uncategorized = [d for d in discrepancies if d["kind"] == "uncategorized"]
        if unexpected:
            out += ["### Unexpected transfers", ""]
            grouped: dict[str, list] = defaultdict(list)
            for d in unexpected:
                grouped[d["rule"]].append(d)
            for rule_name, items in grouped.items():
                rule_detail = items[0]["detail"]
                out += [f"**{rule_name}** — *{rule_detail}*", ""]
                out += ["| ID | Date | Source | Destination | SEK |", "|---|---|---|---|---|"]
                for d in sorted(items, key=lambda x: x["date"]):
                    sign = "−" if d["amount"] < 0 else ""
                    out.append(f"| `{d['id']}` | {d['date']} | {d['source']} | {d['destination']} | {sign}{fmt(d['amount'])} |")
                out.append("")
        if uncategorized:
            out += ["### Uncategorized transactions", ""]
            out += ["| ID | Date | Account | Merchant | SEK |", "|---|---|---|---|---|"]
            for d in sorted(uncategorized, key=lambda x: x["date"]):
                sign = "−" if d["amount"] < 0 else ""
                out.append(f"| `{d['id']}` | {d['date']} | {d['account']} | {d['merchant']} | {sign}{fmt(d['amount'])} |")
            out.append("")
        limits_exceeded = [d for d in discrepancies if d["kind"] == "limit_exceeded"]
        if limits_exceeded:
            out += ["### Monthly limits exceeded", ""]
            for d in limits_exceeded:
                out += [
                    f"**{d['rule']}** — *{d['detail']}*",
                    "",
                    f"Limit: {fmt(d['max'])} · Actual: {fmt(d['actual'])} · Over by {fmt(d['overage'])}",
                    "",
                ]
                out += tx_header
                for tx in sorted(d["txs"], key=lambda x: x["date"]):
                    out.append(tx_row(tx))
                out.append("")
    else:
        out += ["## Discrepancies", "", "*No issues found.*", ""]

    # Improvements section
    if improvements:
        tx_by_id = {tx["id"]: tx for tx in all_transactions + all_transfers if tx.get("id")}
        out += ["## Improvements", ""]
        for item in improvements:
            tx = tx_by_id.get(item["id"])
            if tx:
                sign = "−" if tx["amount"] < 0 else ""
                out.append(
                    f"- [ ] **{item['action']}** — `{item['id']}` {tx['date']} "
                    f"{account_link(tx['account'])} · {tx['merchant']} · {sign}{fmt(tx['amount'])}"
                )
            else:
                out.append(f"- [ ] **{item['action']}** — `{item['id']}`")
        out.append("")

    # Overview table
    net_prefix = "+" if net >= 0 else "−"
    out += [
        "## Overview",
        "",
        "| | SEK |",
        "|---|---|",
        f"| Income | {fmt(total_income)} |",
        f"| Expenses | −{fmt(total_expenses)} |",
        f"| **Net** | **{net_prefix}{fmt(net)}** |",
        "",
    ]

    # Navigation index — themes
    if ordered_themes:
        theme_links = " · ".join(theme_link(t) for t in ordered_themes)
        out += [f"**Themes:** {theme_links}", ""]

    # Navigation index — categories
    if ordered_cats:
        cat_links = " · ".join(cat_link(c) for c in ordered_cats)
        out += [f"**Categories:** {cat_links}", ""]

    # Zoomed-out: super-category chart + table
    sorted_super = sorted(super_expenses.items(), key=lambda x: x[1])
    if sorted_super:
        out += ["## Expenses by theme", "", "```mermaid", f'pie title Expenses by theme — {month_name}']
        for cat, amt in sorted_super:
            out.append(f'    "{cat.replace(chr(34), chr(39))}" : {abs(amt):.2f}')
        out += ["```", ""]
        out += ["| Theme | SEK | % |", "|---|---|---|"]
        for cat, amt in sorted_super:
            pct = abs(amt) / abs(total_expenses) * 100 if total_expenses else 0
            out.append(f"| {theme_link(cat)} | −{fmt(amt)} | {pct:.1f}% |")
        out += [f"| **Total** | **−{fmt(total_expenses)}** | |", ""]

    # Detailed: per-category chart + table
    if sorted_expenses:
        out += ["## Expenses by category", "", "```mermaid", f'pie title Expenses — {month_name}']
        for cat, amt in sorted_expenses[:12]:
            out.append(f'    "{cat.replace(chr(34), chr(39))}" : {abs(amt):.2f}')
        out += ["```", ""]

    # Expense breakdown table
    out += ["## Category breakdown", "", "| Category | Theme | SEK | % |", "|---|---|---|---|"]
    for cat, amt in sorted_expenses:
        pct = abs(amt) / abs(total_expenses) * 100 if total_expenses else 0
        out.append(f"| {cat_link(cat)} | {theme_link(super_cat(cat))} | −{fmt(amt)} | {pct:.1f}% |")
    out += [f"| **Total** | | **−{fmt(total_expenses)}** | |", ""]

    # Income breakdown table
    if sorted_income:
        out += ["## Income breakdown", "", "| Category | SEK |", "|---|---|"]
        for cat, amt in sorted_income:
            out.append(f"| {cat} | {fmt(amt)} |")
        out += [f"| **Total** | **{fmt(total_income)}** |", ""]

    # Per-account section
    out += ["## Per account", ""]
    for acc in account_summaries:
        if not any([acc["income"], acc["expenses"], acc["transfers"]]):
            continue
        out.append(f"### {account_link(acc['name'])}")
        out += ["", "| | SEK |", "|---|---|"]
        if acc["income"]:
            out.append(f"| Income | {fmt(acc['income'])} |")
        if acc["expenses"]:
            out.append(f"| Expenses | −{fmt(abs(acc['expenses']))} |")
        if acc["transfers"]:
            label = "Transfers in" if acc["transfers"] >= 0 else "Transfers out"
            out.append(f"| {label} | {fmt(acc['transfers'])} |")
        if acc["categories"]:
            out += ["", "| Category | SEK |", "|---|---|"]
            for cat, amt in sorted(acc["categories"].items(), key=lambda x: x[1]):
                out.append(f"| {cat_link(cat)} | −{fmt(abs(amt))} |")
        out.append("")

    def tx_total_row(group: list[dict]) -> str:
        total = sum(tx["amount"] for tx in group)
        sign = "−" if total < 0 else ("+" if total > 0 else "")
        return f"| | | | | | **Total** | **{sign}{fmt(total)}** |"

    # All transactions — by date (budget + transfers combined, sorted by date)
    all_combined = sorted(all_transactions + all_transfers, key=lambda x: x["date"])
    out += ["## All transactions — by date", ""] + tx_header
    for tx in all_combined:
        out.append(tx_row(tx))
    out.append(tx_total_row(all_combined))
    out.append("")

    # Full bank statements per account
    out += ["## Accounts", ""]
    for acc_data in accounts:
        acc_name = acc_data.get("account") or ""
        month_txs = [
            tx for tx in acc_data["transactions"]
            if parse_ym(tx["date"]) == (report_year, report_month)
        ]
        if not month_txs:
            continue
        month_txs.sort(key=lambda x: x["date"])
        has_balance = any(tx.get("balance") is not None for tx in month_txs)
        anchor = f'<a id="account-{slug(acc_name)}"></a>'
        out += [anchor, f"### {acc_name}", ""]
        if has_balance:
            out += ["| ID | Date | Description | Category | SEK | Balance |", "|---|---|---|---|---|---|"]
        else:
            out += ["| ID | Date | Description | Category | SEK |", "|---|---|---|---|---|"]
        for tx in month_txs:
            amt = tx.get("amount") or 0.0
            sign = "−" if amt < 0 else ""
            cat = tx.get("category", "Uncategorized")
            desc = tx.get("merchant") or tx.get("description", "")
            tx_id = tx.get("id", "")
            if has_balance:
                bal = tx["balance"]
                bal_str = f"{abs(bal):,.0f} kr".replace(",", " ")
                out.append(f"| `{tx_id}` | {tx['date']} | {desc} | {cat} | {sign}{fmt(amt)} | {bal_str} |")
            else:
                out.append(f"| `{tx_id}` | {tx['date']} | {desc} | {cat} | {sign}{fmt(amt)} |")
        out.append("")

    # All transactions — by theme (one subsection per theme, each with its own anchor)
    out += ["## All transactions — by theme", ""]
    for theme in sorted(set(tx["super_category"] for tx in all_transactions)):
        anchor = f'<a id="theme-{slug(theme)}"></a>'
        group = [tx for tx in all_transactions if tx["super_category"] == theme]
        group.sort(key=lambda x: (x["merchant"], x["date"]))
        out += [anchor, f"### Theme: {theme}", ""] + tx_header
        for tx in group:
            out.append(tx_row(tx))
        out.append(tx_total_row(group))
        out.append("")

    # All transactions — by category (one subsection per category, each with its own anchor)
    out += ["## All transactions — by category", ""]
    for cat in sorted(set(tx["category"] for tx in all_transactions)):
        anchor = f'<a id="cat-{slug(cat)}"></a>'
        group = [tx for tx in all_transactions if tx["category"] == cat]
        group.sort(key=lambda x: (x["merchant"], x["date"]))
        out += [anchor, f"### Category: {cat}", ""] + tx_header
        for tx in group:
            out.append(tx_row(tx))
        out.append(tx_total_row(group))
        out.append("")

    # Transfers section — excluded from budget, shown for reference
    transfer_header = ["| ID | Date | Source | Destination | Category | SEK | Documentation |", "|---|---|---|---|---|---|---|"]

    def transfer_row(tx: dict) -> str:
        if tx["amount"] >= 0:
            source = resolve_account(tx["merchant"], account_map)
            destination = tx["account"]
        else:
            source = tx["account"]
            destination = resolve_account(tx["merchant"], account_map)
        sign = "" if tx["amount"] >= 0 else "−"
        tx_id = tx.get("id", "")
        exc = exceptions.get(tx_id)
        doc = f"[{exc['label']}](discrepancy_log.md#{tx_id})" if exc else ""
        src_display = account_link(source) if "(" in source else source
        dst_display = account_link(destination) if "(" in destination else destination
        return (
            f"| `{tx_id}` | {tx['date']} | {src_display} | {dst_display} "
            f"| {tx['category']} | {sign}{fmt(tx['amount'])} | {doc} |"
        )

    def transfer_total_row(group: list[dict]) -> str:
        total = sum(tx["amount"] for tx in group)
        sign = "−" if total < 0 else ("+" if total > 0 else "")
        return f"| | | | | | **{sign}{fmt(total)}** | |"

    if all_transfers:
        out += ["## Transfers", "*(excluded from budget)*", ""]
        for cat in sorted(set(tx["category"] for tx in all_transfers)):
            anchor = f'<a id="transfer-{slug(cat)}"></a>'
            group = [tx for tx in all_transfers if tx["category"] == cat]
            group.sort(key=lambda x: x["date"])
            out += [anchor, f"### {cat}", ""] + transfer_header
            for tx in group:
                out.append(transfer_row(tx))
            out.append(transfer_total_row(group))
            out.append("")

    out += ["---", f"*Generated {date.today()} · {len(accounts)} accounts*"]

    output_file = REPORTS_DIR / f"{month_label}_budget.md"
    output_file.write_text("\n".join(out), encoding="utf-8")
    print(f"Report written to {output_file}", file=sys.stderr)
