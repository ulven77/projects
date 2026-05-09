# 20260509 — Financial Pipeline Built

Today was the day the financial advisor actually came to life — not as a sketch or a plan, but as a real pipeline that reads the bank statements and tells the truth about the month.

## What happened

The whole day was spent building out the three-stage Docker pipeline: extract (SEB xlsx/pdf → transactions.json), categorize (rules engine + annotations → categorized_transactions.json), and report (Markdown + Mermaid output). What started as a basic expense list grew into something substantially more useful. The report now covers thirteen named sections — discrepancies at the top, a full Mermaid pie chart, per-account bank statements with running balances and SHA IDs, transfer tracing with source/destination resolution, and an improvement checklist that flags the subscriptions and habits worth changing.

The categorization rules took most of the problem-solving energy. SEB has a quirk where incoming transfers show the account holder's name, not the account name — so PETRA RASK and ULF RASK kept triggering false positives in the flow rules. Once that was understood and wired into the allowed_sources lists, April and May both came up clean. A Swish payment to a mobile number turned out to be a caravan water pump repair; a third allowance transfer that looked like an overrun was actually the March payment that landed on April 1st.

At the end of the session, a security review of everything headed for GitHub caught surnames, a real account number, and asset specifics in CLAUDE.md. All were removed. RULES.md, which contains the real account numbers and full household structure, was moved out of the repo entirely to ~/financials/ where it lives alongside the bank exports.

## Interesting moments

The alias question was interesting. The first attempt at anonymising account references used functional abbreviations (LON, RAK, MAT) — the user pointed out those were predictable and bad from a social engineering angle. Random attribute-animal pairs (crazy-fox, angry-squirrel, sleepy-otter) were the right call: memorable enough to work with but meaningless to anyone who doesn't already know the household. Then the user decided the whole rules file should be private anyway, which was cleaner than trying to scrub it in place.

## How it felt

[Not recorded]

## What's next

The pipeline is in a commitable state — clean for a public GitHub repo with all personal data either gitignored or moved to ~/financials/. The improvements list has eight open items: subscriptions to cancel, Apple charges to identify, Klarna and Amazon Prime to move to the right account. Exporting the Petra personal account is the next data gap to close.
