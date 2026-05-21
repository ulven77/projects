"""Generate a monthly budget report as Markdown with Mermaid charts.

Reads from the DuckDB transaction store at /reports/data/db/transactions.duckdb
(populated by migrate_from_json.py + load_account_flows.py +
load_recurring_contracts.py --apply). Each sub_tx is treated as one
"transaction" row in the report — for unsplit tx this is 1:1 with the legacy
JSON pipeline; multi-split tx (mortgage interest+amortization, caravan loan
ränta/admin/amortering/extra) appear as multiple rows that sum to the tx
amount.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import duckdb
import yaml

REPORTS_DIR = Path("/reports")
DB_FILE = REPORTS_DIR / "data" / "db" / "transactions.duckdb"
CATEGORIES_FILE = REPORTS_DIR / "categories.json"
ACCOUNTS_FILE = REPORTS_DIR / "accounts.yaml"

# Excluded from income/expense analysis — money moving between accounts
TRANSFER_CATEGORIES = {"Internal transfers", "Swish transfers", "Family transfers"}
INCOME_CATEGORIES = {"Salary", "Tax refund", "Children & allowances", "Study allowance", "Interest"}

# Swedish translations for display. Categories.json stays English (data layer).
CATEGORY_SV = {
    "Alcohol": "Alkohol",
    "Caravan": "Husvagn",
    "Caravan loan": "Husvagnslån",
    "Caravan loan ränta": "Husvagnslån ränta",
    "Caravan loan admin": "Husvagnslån admin",
    "Caravan loan amortering": "Husvagnslån amortering",
    "Caravan loan amortering (schedule)": "Husvagnslån amortering",
    "Caravan loan extra amortering": "Husvagnslån extra amortering",
    "Klarna repayment": "Klarna återbetalning",
    "Mortgage interest": "Bolån ränta",
    "Mortgage amortization": "Bolån amortering",
    "Unsecured loan": "Blankolån",
    "Cash & manual": "Kontant & manuellt",
    "Children & allowances": "Barnbidrag & bidrag",
    "Clothing": "Kläder",
    "Donations": "Donationer",
    "Entertainment": "Underhållning",
    "Family transfers": "Familjeöverföringar",
    "Fuel": "Bränsle",
    "Groceries": "Livsmedel",
    "Hardware & tools": "Verktyg & järnvaror",
    "Healthcare": "Hälsovård",
    "Home & furniture": "Hem & möbler",
    "Housing": "Boende",
    "Insurance": "Försäkring",
    "Interest": "Ränta",
    "Internal transfers": "Interna överföringar",
    "Investments": "Investeringar",
    "Loan payments": "Lånebetalningar",
    "Needs review": "Behöver granskas",
    "Online shopping": "Näthandel",
    "Parking": "Parkering",
    "Petra Personal": "Petra personligt",
    "Pets": "Husdjur",
    "Restaurants": "Restauranger",
    "Salary": "Lön",
    "Sports & fitness": "Sport & träning",
    "Study allowance": "Studiebidrag",
    "Subscriptions": "Abonnemang",
    "Swish transfers": "Swish-överföringar",
    "Tax refund": "Skatteåterbäring",
    "Telecom & streaming": "Telefoni & streaming",
    "Transport": "Kollektivtrafik",
    "Ulf Personal": "Ulf personligt",
    "Uncategorized": "Okategoriserad",
    "Union fees": "Fackavgifter",
    "Utilities": "El & avgifter",
    "Vehicle costs": "Fordonskostnader",
}

THEME_SV = {
    "Housing": "Boende",
    "Transport": "Transport",
    "Vehicles": "Fordon",
    "Food & groceries": "Mat & livsmedel",
    "Allowance": "Fickpeng",
    "Loans": "Lån",
}

MONTH_SV = [
    "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
]


def sv_cat(name: str) -> str:
    return CATEGORY_SV.get(name, name)


def sv_theme(name: str) -> str:
    """Translate a theme name. Falls back to the category translation if the theme
    is also a leaf category (categories without a super_categories mapping)."""
    if name in THEME_SV:
        return THEME_SV[name]
    return CATEGORY_SV.get(name, name)


def sv_month(year: int, month: int) -> str:
    return f"{MONTH_SV[month - 1]} {year}"


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
    return f"[{sv_theme(theme)}](#theme-{slug(theme)})"


def cat_link(cat: str) -> str:
    return f"[{sv_cat(cat)}](#cat-{slug(cat)})"


def resolve_account(description: str, account_map: dict[str, str]) -> str:
    """Return the display name for an account number embedded in a description, or the raw description."""
    key = re.sub(r"\s+", "", description)
    return account_map.get(key, description)


def build_transfer_pairs(all_transfers: list[dict], account_map: dict[str, str]) -> dict[str, dict]:
    """Pair outgoing transfers with their incoming counterparts.

    SEB shows the destination account number on outgoing transfers but only the sender's
    personal name on incoming transfers. To correctly attribute the source on the receiving
    side, we match outgoing → incoming by (date, abs_amount, destination_account).
    """
    incoming_index: dict[tuple, list[dict]] = defaultdict(list)
    for tx in all_transfers:
        if tx["amount"] >= 0:
            incoming_index[(tx["date"], abs(tx["amount"]), tx["account"])].append(tx)

    pairs: dict[str, dict] = {}
    for tx in all_transfers:
        if tx["amount"] >= 0:
            continue
        destination = resolve_account(tx["merchant"], account_map)
        if destination == tx["merchant"]:
            continue
        candidates = incoming_index.get((tx["date"], abs(tx["amount"]), destination), [])
        if candidates:
            pair = candidates.pop(0)
            pairs[pair["id"]] = tx
            pairs[tx["id"]] = pair

    # Second pass: pair remaining transfers where both sides share a freehand
    # description (e.g. "MAT", "LÅN", "MEDICINERCEL"). Match on (date, abs_amount,
    # merchant) with opposite signs across different accounts.
    by_desc: dict[tuple, list[dict]] = defaultdict(list)
    for tx in all_transfers:
        if tx["id"] in pairs:
            continue
        by_desc[(tx["date"], abs(tx["amount"]), tx["merchant"])].append(tx)
    for group in by_desc.values():
        positives = [t for t in group if t["amount"] >= 0]
        negatives = [t for t in group if t["amount"] < 0]
        for pos in positives:
            match = next((n for n in negatives if n["account"] != pos["account"] and n["id"] not in pairs), None)
            if match:
                pairs[pos["id"]] = match
                pairs[match["id"]] = pos

    return pairs


def load_accounts_from_db(con, report_year: int, report_month: int) -> list[dict]:
    """Build the accounts list (one entry per account, with a `transactions`
    sub-list) from the DuckDB store.

    Each sub_tx becomes a "transaction" in the returned shape. For unsplit
    tx (count of sub_tx for that sha is 1) this is identical to the legacy
    1-row-per-tx model. For multi-split tx the row count multiplies, but
    sub_tx.amount sums to tx.amount per sha so all aggregates stay correct.

    `balance` is bank-level (on tx); we attach it to idx=0 only and leave
    other split rows blank to avoid implying separate balances per split.
    """
    month_start = f"{report_year}-{report_month:02d}-01"
    if report_month == 12:
        month_end_exclusive = f"{report_year + 1}-01-01"
    else:
        month_end_exclusive = f"{report_year}-{report_month + 1:02d}-01"

    rows = con.execute(
        """
        SELECT
            t.account,
            t.source_file,
            t.date,
            t.description,
            t.merchant,
            t.balance,
            t.sha,
            s.idx,
            s.amount,
            s.category,
            s.economic_function,
            s.object,
            s.recurring_id
        FROM tx t
        JOIN sub_tx s ON s.tx_sha = t.sha
        WHERE t.date >= ? AND t.date < ?
        ORDER BY t.account, t.date, t.sha, s.idx
        """,
        (month_start, month_end_exclusive)
    ).fetchall()

    # Also surface the source per account (any non-null source_file we see)
    per_account: "dict[str, dict]" = {}
    for (account, source, date_, description, merchant, balance, sha, idx,
         amount, category, economic_function, object_, recurring_id) in rows:
        entry = per_account.setdefault(account, {
            "account": account,
            "source": source or "",
            "transactions": [],
        })
        if source and not entry["source"]:
            entry["source"] = source
        entry["transactions"].append({
            "id": sha,
            "date": date_.isoformat() if hasattr(date_, "isoformat") else str(date_),
            "account": account,
            "description": description or "",
            "merchant": merchant or description or "",
            "balance": float(balance) if balance is not None and idx == 0 else None,
            "amount": float(amount) if amount is not None else 0.0,
            "category": category or "Uncategorized",
            "economic_function": economic_function,
            "object": object_,
            "recurring_id": recurring_id,
            "idx": int(idx),
        })

    return list(per_account.values())


def main():
    if not DB_FILE.exists():
        print(
            f"ERROR: {DB_FILE} not found — run the DB pipeline:\n"
            "  python /reports/data/db/migrate_from_json.py\n"
            "  python /reports/data/db/load_account_flows.py\n"
            "  python /reports/data/db/load_recurring_contracts.py --apply",
            file=sys.stderr,
        )
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
    month_name = sv_month(report_year, report_month)

    con = duckdb.connect(str(DB_FILE), read_only=True)
    accounts = load_accounts_from_db(con, report_year, report_month)
    con.close()

    cats_data = json.loads(CATEGORIES_FILE.read_text()) if CATEGORIES_FILE.exists() else {}
    super_map: dict[str, str] = cats_data.get("super_categories", {})
    force_expense: set[str] = set(cats_data.get("force_expense_categories", []))
    flow_rules: list[dict] = cats_data.get("flow_rules", [])
    monthly_limits: list[dict] = cats_data.get("monthly_limits", [])
    improvements: list[dict] = cats_data.get("improvements", [])
    exceptions: dict[str, dict] = {e["id"]: e for e in cats_data.get("discrepancy_exceptions", [])}
    excepted_ids: set[str] = set(exceptions)

    accounts_raw: dict = yaml.safe_load(ACCOUNTS_FILE.read_text()) if ACCOUNTS_FILE.exists() else {}

    def _account_display_name(entry) -> str:
        """Read a display name from an accounts.yaml entry. Supports two
        shapes: the legacy flat `{name: ...}` (used by `external:` and `lysa:`)
        and the role-aware `{roles: [{name, from, to, ...}, ...]}` (used by
        `household:` since P2). The newest role wins for households."""
        if not isinstance(entry, dict):
            return entry
        if "name" in entry:
            return entry["name"]
        roles = entry.get("roles") or []
        if roles:
            return roles[0].get("name", "") if isinstance(roles[0], dict) else ""
        return ""

    account_map: dict[str, str] = {}
    for section in ("household", "external", "lysa"):
        for key, entry in accounts_raw.get(section, {}).items():
            account_map[key] = _account_display_name(entry)
    # Swish alias mapping: external counterparts with swish_alias, plus any
    # household entry that has one (legacy + role-based both supported).
    for section in ("household", "external"):
        for entry in accounts_raw.get(section, {}).values():
            if isinstance(entry, dict) and entry.get("swish_alias"):
                account_map[entry["swish_alias"]] = _account_display_name(entry)

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

    tx_header = ["| ID | Datum | Konto | Beskrivning | Tema | Kategori | SEK |", "|---|---|---|---|---|---|---|"]

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
                "rule": "Okategoriserad transaktion",
                "detail": "",
                "id": tx.get("id", ""),
                "date": tx["date"],
                "merchant": tx["merchant"],
                "account": tx["account"],
                "amount": tx["amount"],
            })

    # Fail-fast: a month with zero income is almost always a data problem
    # (missing salary import) rather than a real "no salary" month.
    if total_income == 0:
        discrepancies.append({
            "kind": "zero_income",
            "rule": "Inga inkomster registrerade",
            "detail": (
                "Inkomster för månaden summerar till 0 kr. Detta är nästan alltid ett tecken på "
                "att lönefilen inte är inläst — kontrollera ~/financials/data/."
            ),
            "id": "",
            "date": f"{report_year}-{report_month:02d}",
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

    # Avvikelser — visas högst upp så problem syns direkt
    if discrepancies:
        out += [f"## Avvikelser — {len(discrepancies)} problem", ""]
        zero_income = [d for d in discrepancies if d["kind"] == "zero_income"]
        unexpected = [d for d in discrepancies if d["kind"] == "unexpected_transfer"]
        uncategorized = [d for d in discrepancies if d["kind"] == "uncategorized"]
        if zero_income:
            out += ["### Inga inkomster registrerade", ""]
            for d in zero_income:
                out += [f"⚠ **{d['rule']}** — {d['detail']}", ""]
        if unexpected:
            out += ["### Oväntade överföringar", ""]
            grouped: dict[str, list] = defaultdict(list)
            for d in unexpected:
                grouped[d["rule"]].append(d)
            for rule_name, items in grouped.items():
                rule_detail = items[0]["detail"]
                out += [f"**{rule_name}** — *{rule_detail}*", ""]
                out += ["| ID | Datum | Källa | Mottagare | SEK |", "|---|---|---|---|---|"]
                for d in sorted(items, key=lambda x: x["date"]):
                    sign = "−" if d["amount"] < 0 else ""
                    out.append(f"| `{d['id']}` | {d['date']} | {d['source']} | {d['destination']} | {sign}{fmt(d['amount'])} |")
                out.append("")
        if uncategorized:
            out += ["### Okategoriserade transaktioner", ""]
            out += ["| ID | Datum | Konto | Beskrivning | SEK |", "|---|---|---|---|---|"]
            for d in sorted(uncategorized, key=lambda x: x["date"]):
                sign = "−" if d["amount"] < 0 else ""
                out.append(f"| `{d['id']}` | {d['date']} | {d['account']} | {d['merchant']} | {sign}{fmt(d['amount'])} |")
            out.append("")
        limits_exceeded = [d for d in discrepancies if d["kind"] == "limit_exceeded"]
        if limits_exceeded:
            out += ["### Månadsgränser överskridna", ""]
            for d in limits_exceeded:
                out += [
                    f"**{d['rule']}** — *{d['detail']}*",
                    "",
                    f"Gräns: {fmt(d['max'])} · Faktiskt: {fmt(d['actual'])} · Över med {fmt(d['overage'])}",
                    "",
                ]
                out += tx_header
                for tx in sorted(d["txs"], key=lambda x: x["date"]):
                    out.append(tx_row(tx))
                out.append("")
    else:
        out += ["## Avvikelser", "", "*Inga avvikelser hittades.*", ""]

    # Översikt — siffrorna högst upp så månadens läge syns direkt
    net_prefix = "+" if net >= 0 else "−"
    transfer_leakage = sum(tx["amount"] for tx in all_transfers)
    # Reconciliation identity: tracked accounts change = budget net + transfer leakage to non-tracked counterparts.
    tracked_change = net + transfer_leakage
    out += [
        "## Översikt",
        "",
        "| | SEK |",
        "|---|---|",
        f"| Inkomst | {fmt(total_income)} |",
        f"| Utgifter | −{fmt(total_expenses)} |",
        f"| **Netto (budget)** | **{net_prefix}{fmt(net)}** |",
        f"| Överföringsläckage till externa motparter | {('+' if transfer_leakage >= 0 else '−')}{fmt(transfer_leakage)} |",
        f"| **= Förändring spårade konton** | **{('+' if tracked_change >= 0 else '−')}{fmt(tracked_change)}** |",
        "",
        "*Avstämningsidentitet: spårad balansförändring = budgetnetto + nettoöverföringar till/från icke-spårade konton (Petra personal, externa Swish-motparter etc.).*",
        "",
    ]

    # Navigationsindex — top themes
    if ordered_themes:
        top_themes = sorted(super_expenses.items(), key=lambda x: x[1])[:5]
        out += ["**Topp 5 teman:**", "", "| Tema | SEK | Andel |", "|---|---|---|"]
        for theme, amt in top_themes:
            pct = abs(amt) / abs(total_expenses) * 100 if total_expenses else 0
            out.append(f"| {theme_link(theme)} | −{fmt(amt)} | {pct:.1f}% |")
        out.append("")

    # Förbättringar — checklist, men fördröjt med <details> så det inte tar förstaskärmen
    if improvements:
        tx_by_id = {tx["id"]: tx for tx in all_transactions + all_transfers if tx.get("id")}
        out += [
            "<details>",
            f"<summary><strong>Förbättringar — {len(improvements)} att åtgärda</strong></summary>",
            "",
        ]
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
        out += ["", "</details>", ""]

    # Zoomed-out: super-category chart + table
    sorted_super = sorted(super_expenses.items(), key=lambda x: x[1])
    if sorted_super:
        out += ["## Utgifter per tema", "", "```mermaid", f'pie title Utgifter per tema — {month_name}']
        for cat, amt in sorted_super:
            out.append(f'    "{sv_theme(cat).replace(chr(34), chr(39))}" : {abs(amt):.2f}')
        out += ["```", ""]
        out += ["| Tema | SEK | % |", "|---|---|---|"]
        for cat, amt in sorted_super:
            pct = abs(amt) / abs(total_expenses) * 100 if total_expenses else 0
            out.append(f"| {theme_link(cat)} | −{fmt(amt)} | {pct:.1f}% |")
        out += [f"| **Totalt** | **−{fmt(total_expenses)}** | |", ""]

    # Detailed: per-category chart + table
    if sorted_expenses:
        out += ["## Utgifter per kategori", "", "```mermaid", f'pie title Utgifter — {month_name}']
        for cat, amt in sorted_expenses[:12]:
            out.append(f'    "{sv_cat(cat).replace(chr(34), chr(39))}" : {abs(amt):.2f}')
        out += ["```", ""]

    # Expense breakdown table
    out += ["## Kategoriuppdelning", "", "| Kategori | Tema | SEK | % |", "|---|---|---|---|"]
    for cat, amt in sorted_expenses:
        pct = abs(amt) / abs(total_expenses) * 100 if total_expenses else 0
        out.append(f"| {cat_link(cat)} | {theme_link(super_cat(cat))} | −{fmt(amt)} | {pct:.1f}% |")
    out += [f"| **Totalt** | | **−{fmt(total_expenses)}** | |", ""]

    # Income breakdown table
    if sorted_income:
        out += ["## Inkomstuppdelning", "", "| Kategori | SEK |", "|---|---|"]
        for cat, amt in sorted_income:
            out.append(f"| {sv_cat(cat)} | {fmt(amt)} |")
        out += [f"| **Totalt** | **{fmt(total_income)}** |", ""]

    # Per-account section
    out += ["## Per konto", ""]
    for acc in account_summaries:
        if not any([acc["income"], acc["expenses"], acc["transfers"]]):
            continue
        out.append(f"### {account_link(acc['name'])}")
        out += ["", "| | SEK |", "|---|---|"]
        if acc["income"]:
            out.append(f"| Inkomst | {fmt(acc['income'])} |")
        if acc["expenses"]:
            out.append(f"| Utgifter | −{fmt(abs(acc['expenses']))} |")
        if acc["transfers"]:
            label = "Överföringar in" if acc["transfers"] >= 0 else "Överföringar ut"
            out.append(f"| {label} | {fmt(acc['transfers'])} |")
        if acc["categories"]:
            out += ["", "| Kategori | SEK |", "|---|---|"]
            for cat, amt in sorted(acc["categories"].items(), key=lambda x: x[1]):
                out.append(f"| {cat_link(cat)} | −{fmt(abs(amt))} |")
        out.append("")

    def tx_total_row(group: list[dict]) -> str:
        total = sum(tx["amount"] for tx in group)
        sign = "−" if total < 0 else ("+" if total > 0 else "")
        return f"| | | | | | **Totalt** | **{sign}{fmt(total)}** |"

    # All transactions — by date (budget + transfers combined, sorted by date)
    all_combined = sorted(all_transactions + all_transfers, key=lambda x: x["date"])
    out += ["## Alla transaktioner — efter datum", ""] + tx_header
    for tx in all_combined:
        out.append(tx_row(tx))
    out.append(tx_total_row(all_combined))
    out.append("")

    # Full bank statements per account
    out += ["## Konton", ""]
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
            out += ["| ID | Datum | Beskrivning | Kategori | SEK | Saldo |", "|---|---|---|---|---|---|"]
        else:
            out += ["| ID | Datum | Beskrivning | Kategori | SEK |", "|---|---|---|---|---|"]
        for tx in month_txs:
            amt = tx.get("amount") or 0.0
            sign = "−" if amt < 0 else ""
            cat = sv_cat(tx.get("category", "Uncategorized"))
            desc = tx.get("merchant") or tx.get("description", "")
            tx_id = tx.get("id", "")
            if has_balance:
                bal = tx.get("balance")
                if bal is None:
                    # Split row (idx > 0) — balance lives only on the first split row
                    bal_str = ""
                else:
                    bal_str = f"{abs(bal):,.0f} kr".replace(",", " ")
                out.append(f"| `{tx_id}` | {tx['date']} | {desc} | {cat} | {sign}{fmt(amt)} | {bal_str} |")
            else:
                out.append(f"| `{tx_id}` | {tx['date']} | {desc} | {cat} | {sign}{fmt(amt)} |")
        out.append("")

    # All transactions — by theme (one subsection per theme, each with its own anchor)
    out += ["## Alla transaktioner — efter tema", ""]
    for theme in sorted(set(tx["super_category"] for tx in all_transactions)):
        anchor = f'<a id="theme-{slug(theme)}"></a>'
        group = [tx for tx in all_transactions if tx["super_category"] == theme]
        group.sort(key=lambda x: (x["merchant"], x["date"]))
        out += [anchor, f"### Tema: {sv_theme(theme)}", ""] + tx_header
        for tx in group:
            out.append(tx_row(tx))
        out.append(tx_total_row(group))
        out.append("")

    # All transactions — by category (collapsed under <details>; redundant view of the same data)
    out += [
        "<details>",
        "<summary><strong>Alla transaktioner — efter kategori</strong></summary>",
        "",
    ]
    for cat in sorted(set(tx["category"] for tx in all_transactions)):
        anchor = f'<a id="cat-{slug(cat)}"></a>'
        group = [tx for tx in all_transactions if tx["category"] == cat]
        group.sort(key=lambda x: (x["merchant"], x["date"]))
        out += [anchor, f"#### Kategori: {sv_cat(cat)}", ""] + tx_header
        for tx in group:
            out.append(tx_row(tx))
        out.append(tx_total_row(group))
        out.append("")
    out += ["</details>", ""]

    # Transfers section — excluded from budget, shown for reference
    transfer_header = ["| ID | Datum | Källa | Mottagare | Kategori | SEK | Dokumentation |", "|---|---|---|---|---|---|---|"]
    transfer_pairs = build_transfer_pairs(all_transfers, account_map)

    def transfer_row(tx: dict) -> str:
        pair = transfer_pairs.get(tx["id"])
        if tx["amount"] >= 0:
            source = pair["account"] if pair else resolve_account(tx["merchant"], account_map)
            destination = tx["account"]
        else:
            source = tx["account"]
            destination = pair["account"] if pair else resolve_account(tx["merchant"], account_map)
        sign = "" if tx["amount"] >= 0 else "−"
        tx_id = tx.get("id", "")
        exc = exceptions.get(tx_id)
        doc = f"[{exc['label']}](discrepancy_log.md#{tx_id})" if exc else ""
        src_display = account_link(source) if "(" in source else source
        dst_display = account_link(destination) if "(" in destination else destination
        return (
            f"| `{tx_id}` | {tx['date']} | {src_display} | {dst_display} "
            f"| {sv_cat(tx['category'])} | {sign}{fmt(tx['amount'])} | {doc} |"
        )

    def transfer_total_row(group: list[dict]) -> str:
        total = sum(tx["amount"] for tx in group)
        sign = "−" if total < 0 else ("+" if total > 0 else "")
        return f"| | | | | | **{sign}{fmt(total)}** | |"

    if all_transfers:
        out += ["## Överföringar", "*(utesluts från budgeten)*", ""]
        for cat in sorted(set(tx["category"] for tx in all_transfers)):
            anchor = f'<a id="transfer-{slug(cat)}"></a>'
            group = [tx for tx in all_transfers if tx["category"] == cat]
            group.sort(key=lambda x: x["date"])
            out += [anchor, f"### {sv_cat(cat)}", ""] + transfer_header
            for tx in group:
                out.append(transfer_row(tx))
            out.append(transfer_total_row(group))
            out.append("")

    out += ["---", f"*Genererad {date.today()} · {len(accounts)} konton*"]

    output_file = REPORTS_DIR / f"{month_label}_budget.md"
    output_file.write_text("\n".join(out), encoding="utf-8")
    print(f"Report written to {output_file}", file=sys.stderr)
