# Activity 2 — "Update Income Account" Button

## 1. Time tracking

| Task | Estimated | Actual |
|---|---|---|
| Design: wizard vs. inline form, state guard placement | 5 min | 10 min |
| `account.move.update.income.account.wizard` model | 15 min | 15 min |
| Wizard form view (pop-up) | 10 min | 10 min |
| Button on invoice header + xpath | 10 min | 10 min |
| Security access rights | 2 min | 3 min |
| Manual test pass on running instance | 10 min | *(pending — see note)* |
| Documentation + test cases | 8 min | 12 min |
| **Total** | **60 min** | **~60 min (excl. live test pass)** |


## 2. Design decisions

- **Wizard (`TransientModel`), not an inline popup on the invoice form itself.** A pop-up form is literally what the requirement asks for, and a wizard keeps the "select account → confirm → bulk write" logic isolated and testable, rather than bolting temporary state onto `account.move`.
- **Button anchored on `//header`**, not a specific sibling button, so it survives reordering of standard buttons across Odoo point releases (same reasoning as Activity 1's `//notebook` anchor).
- **Restricted to `move_type in ('out_invoice', 'out_refund')`** — the brief says "Invoice form view," which I read as customer invoices/credit notes, not vendor bills. Flagging this as an assumption in case the intent was broader.
- **`account_type in ('income', 'income_other')`** — Odoo's chart of accounts uses these two account types for income-side accounts (Odoo 17+ terminology; older versions used `user_type_id` against an income account type instead — if you're on an older point release this domain will need adjusting).
- **Defense in depth on the Draft check**, not just UI hiding: both `default_get()` (when the wizard opens) and `action_confirm()` (when it's submitted) re-verify `move_id.state == 'draft'` and raise a `UserError` otherwise. The button's `invisible` attribute is a convenience, not a security boundary — a determined user could still trigger the underlying action via a saved URL, browser console, or automation, so the real guard has to live server-side.
- **Section/note lines excluded** via `filtered(lambda l: not l.display_type)` — those lines have no account to update and would error if included.
- **Chatter log on confirm** (`message_post`) so there's an audit trail of who changed the income account and to what, directly on the invoice — useful since this is a bulk data-changing action.

## 3. Test cases

| # | Test case | Steps | Expected result |
|---|---|---|---|
| TC-01 | Button visibility — Draft | Open a draft customer invoice | "Update Income Account" button appears in the header |
| TC-02 | Button visibility — Posted | Post the invoice, reopen the form | Button is hidden |
| TC-03 | Button visibility — Vendor Bill | Open a draft vendor bill | Button does not appear (restricted to `out_invoice`/`out_refund`) |
| TC-04 | Happy path | Click button, select a valid income account, click Confirm | All non-section/note invoice lines now show the selected account; wizard closes; chatter shows the update message |
| TC-05 | Account domain filtering | Open the wizard's account field | Only accounts with `account_type` in (income, income_other), not deprecated, and belonging to the invoice's company are selectable |
| TC-06 | Cancel | Click button, select an account, click Cancel | No lines are changed |
| TC-07 | Multi-line invoice | Invoice with 5 lines across different original accounts | All 5 lines end up on the newly selected account after Confirm |
| TC-08 | Invoice with section/note lines | Invoice has a "Section" line plus 3 product lines | Only the 3 product lines update; the section line is untouched and doesn't error |
| TC-09 | No product lines | Invoice with only a section/note line, no real lines | Confirm raises a clear `UserError` ("no product/service lines to update") instead of silently doing nothing |
| TC-10 | Race condition — invoice posted between opening and confirming | Open the wizard, then post the invoice from another tab/window before clicking Confirm | `action_confirm()` re-checks state and blocks the update with a `UserError`, rather than trusting the state at the time the wizard opened |
| TC-11 | Required field | Click button, leave income account empty, click Confirm | Odoo's standard required-field validation blocks submission |
| TC-12 | Multi-company | Company A invoice, only Company B income accounts exist | Account field domain correctly returns nothing / excludes Company B accounts (verify `company_ids` behaves as expected on your instance) |

## 4. Known follow-ups

1. If your Odoo 19 build's `account.account` model doesn't use `company_ids` (many2many) — check by inspecting the field on `account.account` in Technical settings — swap the domain clause to whatever the equivalent field is on your version.
2. Currently the wizard has no confirmation/warning step summarizing *which* accounts are being replaced (just a count). If the business wants a full before/after diff shown before confirming, that's a small additional enhancement, not implemented here since it wasn't in the stated requirement.
