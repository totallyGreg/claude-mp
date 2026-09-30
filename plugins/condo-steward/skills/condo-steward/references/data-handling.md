# Handling sensitive community data

Association records are, by statute, open to owners — but "an owner may inspect at the office" is not the same as "sitting in a shared Google Drive folder that gets synced to six laptops." Treat every derived file as if it will leak, and keep the raw sources where the statute puts them: with the manager and the official records.

## Three tiers

| Tier | Examples | Where it may live | What the scripts do |
|---|---|---|---|
| **Secret** | Full bank account numbers, routing numbers, online-banking credentials, ACH trace numbers, loan account numbers, EIN on bank letters | Treasurer's password manager or a locked note. Never in a repo, shared drive, chat, or generated file. | Mask every 8+ digit run to `****1234` in all output, unconditionally. No override flag exists. |
| **Personal** | Owner names tied to balances, unit numbers, owner account numbers, email/phone, delinquency status by unit, fine hearings | Official records (manager/portal). Board packets only when the agenda requires it. Not in reports, not in the plugin. | Dropped by the parser unless `--include-names`; never rendered in HTML even then. |
| **Community** | Balance sheet, budget vs actual, aging **totals**, reconciliation status, vendor payees, statutes, meeting notices | Shared drive, reports, board emails | Included. This is what owners are entitled to understand. |

Reports show **account name + last four digits** (`Operating Checking ****4321`) — enough to talk about an account, not enough to move money.

## Rules for shared locations (Google Drive, Dropbox, iCloud shared folders)

1. **Raw bank exports (CSV/XLSX) do not go in the shared folder.** They contain full account numbers in the ID column *and* in transfer descriptions. Run `parse_transactions.py` and share the masked JSON or a summary instead.
2. **Monthly statement PDFs** are borderline: the balance sheet is community-tier, but the aged-receivable and prepaid pages name owners and their balances, and the reconciliation pages may include the bank's own statement pages. If the folder is shared beyond the board, keep PDFs in a board-only subfolder and put generated reports in the shared one.
3. **Run the scanner before syncing or committing:** `uv run scan_sensitive.py <folder>` — exits 1 if it finds unmasked account-like numbers (8+ digits, or 3+ separated groups). Statement PDFs will usually trip it on owner account and invoice numbers in the aging pages; `--ignore-ext pdf` focuses on exports and generated files. It cannot detect names; that judgment stays with a person.
4. **`community.toml` is private** (thresholds are harmless, but the name plus folder paths are still yours). Gitignore it.
5. **Never paste account numbers into a chat with an AI assistant**, including this one. The scripts exist so the numbers never need to be typed.

## Why the manager and bank make account numbers hard to get

Banks mask numbers on statements and portals deliberately; managers hold the full numbers under fidelity-bond and internal-control obligations (see 718.111(11)(h)). A board member rarely needs the full number — the exceptions are setting up a new account, moving reserves, or changing signers, all of which are board actions that belong in minutes, not in files.

## When something has leaked

- Ask the bank to add verbal-password or positive-pay controls on the account; consider re-numbering if the exposure was public.
- Delete the file from the shared location **and** its version history / trash.
- Note it in the board minutes if owner data (Personal tier) was exposed; Florida has no association-specific breach statute, but the general data-breach law (§501.171) can apply to certain identifiers — ask the attorney.
