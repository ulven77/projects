"""Categorize transactions using keyword rules stored in categories.json."""

import json
import re
import sys
from pathlib import Path

import yaml

REPORTS_DIR = Path("/reports")
TRANSACTIONS_FILE = REPORTS_DIR / "transactions.json"
CATEGORIES_FILE = REPORTS_DIR / "categories.json"
ANNOTATIONS_FILE = REPORTS_DIR / "annotations.json"
ACCOUNTS_FILE = REPORTS_DIR / "accounts.yaml"
UNKNOWN_FILE = REPORTS_DIR / "unknown_merchants.json"
CATEGORIZED_FILE = REPORTS_DIR / "categorized_transactions.json"

# Strip date suffixes like "/26-04-27" appended by SEB to truncated merchant names
_DATE_SUFFIX_RE = re.compile(r"/\d{2}-\d{2}-\d{2}$")


def strip_date_suffix(description: str) -> str:
    return _DATE_SUFFIX_RE.sub("", description).strip()


def load_rules() -> list[dict]:
    if not CATEGORIES_FILE.exists():
        return []
    return json.loads(CATEGORIES_FILE.read_text())["rules"]


def load_annotations() -> list[dict]:
    if not ANNOTATIONS_FILE.exists():
        return []
    return json.loads(ANNOTATIONS_FILE.read_text())


def load_accounts() -> set[str]:
    """Return the set of household account number keys.

    Only household accounts (where money internally circulates) trigger the
    auto-Internal-transfers classification. External entries in accounts.json
    (Marie, Länsförsäkringar fund, etc.) are display-only and must fall through
    to keyword rules.
    """
    if not ACCOUNTS_FILE.exists():
        return set()
    data = yaml.safe_load(ACCOUNTS_FILE.read_text())
    keys: set[str] = set(data.get("household", {}).keys())
    for entry in data.get("household", {}).values():
        if isinstance(entry, dict) and entry.get("swish_alias"):
            keys.add(entry["swish_alias"])
    return keys


_DIGITS_RE = re.compile(r"\D")


def find_category(tx: dict, account_name: str, rules: list[dict], known_accounts: set[str] = frozenset()) -> str | None:
    """Return the first matching category for a transaction, or None.

    Rule fields (all optional except category):
      keyword         — description contains this string (case-insensitive)
      account_contains — account name contains this string (case-insensitive)
      amount_min      — transaction amount >= this value
      amount_max      — transaction amount <= this value
      date_from       — transaction date >= this (YYYY-MM-DD)
      date_to         — transaction date <= this (YYYY-MM-DD)

    All specified fields must match (AND). Unspecified fields are wildcards.
    """
    desc = tx.get("description") or ""
    desc_upper = desc.upper()
    amount = tx.get("amount") or 0.0
    date_str = tx.get("date", "")
    account_lower = account_name.lower()

    # Description is a known account number → always an internal transfer.
    # SEB populates outgoing transfer descriptions with the destination account number,
    # making this a reliable machine-generated signal that should not be overridden by keywords.
    if known_accounts and _DIGITS_RE.sub("", desc) in known_accounts:
        return "Internal transfers"

    for rule in rules:
        if rule.get("keyword") and rule["keyword"].upper() not in desc_upper:
            continue
        if rule.get("account_contains") and rule["account_contains"].lower() not in account_lower:
            continue
        if rule.get("amount_min") is not None and amount < rule["amount_min"]:
            continue
        if rule.get("amount_max") is not None and amount > rule["amount_max"]:
            continue
        if rule.get("date_from") and date_str < rule["date_from"]:
            continue
        if rule.get("date_to") and date_str > rule["date_to"]:
            continue
        return rule["category"]
    return None


def find_annotation(tx: dict, account_name: str, annotations: list[dict]) -> str | None:
    """Return a category override if an annotation matches this exact transaction."""
    for ann in annotations:
        if ann.get("description") and ann["description"] != tx.get("description", ""):
            continue
        if ann.get("date") and ann["date"] != tx["date"]:
            continue
        if ann.get("amount") is not None and abs(ann["amount"] - (tx.get("amount") or 0)) > 0.01:
            continue
        if ann.get("account_contains") and ann["account_contains"].lower() not in account_name.lower():
            continue
        return ann["category"]
    return None


def main_unknown_merchants():
    if not TRANSACTIONS_FILE.exists():
        print(f"ERROR: {TRANSACTIONS_FILE} not found — run 'make extract' first.", file=sys.stderr)
        sys.exit(1)

    accounts = json.loads(TRANSACTIONS_FILE.read_text())
    rules = load_rules()
    known_accounts = load_accounts()

    unknown: set[str] = set()
    for account in accounts:
        for tx in account["transactions"]:
            merchant = strip_date_suffix(tx["description"])
            if merchant and not find_category(tx, account["account"], rules, known_accounts):
                unknown.add(merchant)

    result = sorted(unknown)
    UNKNOWN_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"{len(result)} uncategorized merchants → {UNKNOWN_FILE}", file=sys.stderr)
    for merchant in result:
        print(merchant)


def main_categorize():
    if not TRANSACTIONS_FILE.exists():
        print(f"ERROR: {TRANSACTIONS_FILE} not found — run 'make extract' first.", file=sys.stderr)
        sys.exit(1)

    accounts = json.loads(TRANSACTIONS_FILE.read_text())
    rules = load_rules()
    annotations = load_annotations()
    known_accounts = load_accounts()

    if not rules:
        print("WARNING: categories.json is empty — all transactions will be Uncategorized.", file=sys.stderr)

    total = categorized_count = 0
    annotation_count = 0
    uncategorized: set[str] = set()

    for account in accounts:
        for tx in account["transactions"]:
            total += 1
            merchant = strip_date_suffix(tx["description"])
            tx["merchant"] = merchant
            category = find_annotation(tx, account["account"], annotations)
            if category:
                annotation_count += 1
            else:
                category = find_category(tx, account["account"], rules, known_accounts)
            tx["category"] = category or "Uncategorized"
            if category:
                categorized_count += 1
            else:
                uncategorized.add(merchant)

    CATEGORIZED_FILE.write_text(json.dumps(accounts, ensure_ascii=False, indent=2))
    print(f"Categorized {categorized_count}/{total} transactions ({annotation_count} via annotations)", file=sys.stderr)
    if uncategorized:
        print(f"{len(uncategorized)} unique merchants still uncategorized", file=sys.stderr)
    print(f"Written to {CATEGORIZED_FILE}", file=sys.stderr)
