"""Extract transactions from SEB bank exports (Excel and PDF) to JSON."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import openpyxl

DATA_DIR = Path("/data")
REPORTS_DIR = Path("/reports")
OUTPUT_FILE = REPORTS_DIR / "transactions.json"

# Matches SEB account number format: "Account Name (5354 35 830 50)"
_ACCOUNT_RE = re.compile(r".+\(\d{4}\s+\d{2}\s+\d{3,}\s+\d+\)")

# Matches a transaction line in a SEB PDF:
# "2026-05-06  Some Merchant/26-05-05  -168,00  536,58"
_PDF_TX_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})\s{2,}(.+?)\s{2,}(-?[\d\s]+,\d{2})\s{2,}([\d\s]+,\d{2})\s*$"
)


def _tx_hash(account: str, date: str, description: str, amount: float | None) -> str:
    key = f"{date}|{account}|{description}|{amount}"
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def _parse_swedish_number(s: str) -> float:
    return float(s.replace(" ", "").replace(" ", "").replace(",", "."))


def parse_excel(path: Path) -> dict:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    account_name = None
    header_idx = None

    for i, row in enumerate(rows):
        if not row or row[0] is None:
            continue
        cell = str(row[0]).strip()
        if _ACCOUNT_RE.match(cell):
            account_name = cell
        if cell == "Bokföringsdatum":
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"No header row found in {path.name}")

    transactions = []
    for row in rows[header_idx + 1 :]:
        if not row or row[0] is None:
            continue
        try:
            transactions.append(
                {
                    "date": str(row[0]),
                    "description": str(row[3]).strip() if row[3] else "",
                    "amount": float(row[4]) if row[4] is not None else None,
                    "balance": float(row[5]) if row[5] is not None else None,
                }
            )
        except (TypeError, ValueError, IndexError):
            continue

    for tx in transactions:
        tx["id"] = _tx_hash(account_name or "", tx["date"], tx.get("description", ""), tx.get("amount"))
    return {"account": account_name, "source": path.name, "transactions": transactions}


def parse_pdf(path: Path) -> dict:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )

    account_name = None
    transactions = []
    in_transactions = False

    for line in result.stdout.splitlines():
        stripped = line.strip()

        if not account_name and _ACCOUNT_RE.match(stripped):
            account_name = stripped
            continue

        if stripped == "Transaktioner":
            in_transactions = True
            continue

        if not in_transactions or not stripped:
            continue

        # Skip header and page-break lines
        if stripped.startswith("Datum") or stripped.startswith("Utskrift"):
            continue

        # Stop at "Reserverade belopp" section (pending transactions — not booked)
        if stripped.startswith("Reserverade belopp"):
            in_transactions = False
            continue

        m = _PDF_TX_RE.match(stripped)
        if m:
            try:
                transactions.append(
                    {
                        "date": m.group(1),
                        "description": m.group(2).strip(),
                        "amount": _parse_swedish_number(m.group(3)),
                        "balance": _parse_swedish_number(m.group(4)),
                    }
                )
            except ValueError:
                continue

    for tx in transactions:
        tx["id"] = _tx_hash(account_name or "", tx["date"], tx.get("description", ""), tx.get("amount"))
    return {"account": account_name, "source": path.name, "transactions": transactions}


def extract_all() -> list[dict]:
    results = []
    seen_accounts: dict[str, str] = {}

    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix.lower() == ".xlsx":
            result = parse_excel(path)
        elif path.suffix.lower() == ".pdf":
            result = parse_pdf(path)
        else:
            print(f"Skipping unsupported file: {path.name}", file=sys.stderr)
            continue

        account = result.get("account") or path.name
        if account in seen_accounts:
            print(
                f"WARNING: duplicate account '{account}' in {path.name} "
                f"(already seen in {seen_accounts[account]}) — skipping",
                file=sys.stderr,
            )
            continue

        seen_accounts[account] = path.name
        print(
            f"  {path.name}: {account} — {len(result['transactions'])} transactions",
            file=sys.stderr,
        )
        results.append(result)

    return results


def main():
    print("Extracting transactions...", file=sys.stderr)
    accounts = extract_all()

    total = sum(len(a["transactions"]) for a in accounts)
    print(f"Total: {total} transactions across {len(accounts)} accounts", file=sys.stderr)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(accounts, ensure_ascii=False, indent=2))
    print(f"Written to {OUTPUT_FILE}", file=sys.stderr)
