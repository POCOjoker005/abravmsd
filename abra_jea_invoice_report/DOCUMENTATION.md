# Activity 1 — Custom JEA Invoice PDF Report

## 1. Time tracking

| Task | Estimated | Actual |
|---|---|---|
| Analyse source PDF, map layout to Odoo fields | 15 min | 20 min |
| `account.move` / `account.move.line` custom fields | 15 min | 15 min |
| Invoice form view (tab + Claim % column) | 15 min | 15 min |
| QWeb report template (header, refs table, lines table, totals, footer) | 45 min | 55 min |
| Report action + menu binding | 5 min | 5 min |
| Manual test pass in a running Odoo instance | 20 min | *(pending — see note below)* |
| Documentation + test case write-up | 5 min | 15 min |
| **Total** | **120 min** | **~125 min (excl. live Odoo test pass)** |

**Note on the live test pass:** this environment has no running Odoo 19 server, so the module was validated by (a) linting every Python/XML file, and (b) rendering the exact same HTML/CSS markup through `wkhtmltopdf` — the identical PDF engine Odoo's `qweb-pdf` report type uses — to visually confirm the layout against `Test_Invoice.pdf`. Installing the module (`-i abra_jea_invoice_report`) on a real instance and running the checklist in §3 is the remaining step before sign-off.

## 2. Design decisions worth flagging in review

- **Reused standard fields wherever one already existed** instead of adding redundant custom fields: `TOTAL VALUE`/`VALUE` map to `price_total`/`price_subtotal`, `VAT RATE`/`VAT AMT` are derived from `tax_ids` and `price_total - price_subtotal`, the amount-in-words line uses the built-in `currency_id.amount_to_text()`, and the `QTY` column ("LS") reuses the standard `product_uom_id` — create a UoM named "LS" under a Service category rather than adding a text field.
- **New fields only where no standard equivalent exists**: `jea_job_number`, `jea_order_ref` (+ `jea_order_ref_date`), `jea_payment_schedule`, `jea_project_reference` on `account.move`, and `jea_claim_percentage` on `account.move.line`.
  - *Naming note:* custom fields use the `jea_` prefix (module-specific) rather than the generic Odoo `x_` studio-style prefix, to keep them clearly scoped to this module and avoid collisions with any ad-hoc Studio customizations added later.
- **TRN handling**: real TRNs already live on `res.company.vat`. Added `jea_trn_override` + computed `jea_trn_display` so the report prints the company VAT by default, an invoice-specific override if set, and falls back to `"Under Regn"` if neither exists — matching the source PDF without hardcoding the fallback text into the template. `jea_trn_display` is a plain (non-stored) computed field, recomputed via `@api.depends('jea_trn_override', 'company_id.vat')` — it's read-only in the UI/report and does not need to be stored or searched on.
- **Claim % field**: `jea_claim_percentage` is a `Float` with explicit `digits=(5, 2)` precision, purely informational — it does not affect `price_subtotal`/`price_total`, which remain the source of truth for accounting.
- **View inheritance is anchored on `//notebook`** rather than a specific page id, since exact page ids in `account.view_move_form` can shift between Odoo point releases — appending as the last tab is more upgrade-safe.
- **Money fields use `t-options` with `display_currency`** rather than string formatting, so multi-currency invoices still render correctly (the source invoice is AED-only, but the report shouldn't assume that).

## 3. Test cases

| # | Test case | Steps | Expected result |
|---|---|---|---|
| TC-01 | Report appears only for customer invoices | Open a Vendor Bill, check Print menu | "JEA Invoice" is **not** listed (binding is on `account.move` generically — see note below on restricting to `out_invoice`) |
| TC-02 | Basic field mapping | Create a draft customer invoice, fill Job#, Order Ref, Payment Schedule, Project (`jea_job_number`, `jea_order_ref`, `jea_payment_schedule`, `jea_project_reference`), add one invoice line with Claim % = 25 (`jea_claim_percentage`), qty UoM = LS, price = 58,750, tax = 0% | Printed PDF shows all values in the correct cells, matching `Test_Invoice.pdf` layout |
| TC-03 | TRN fallback logic | Leave `jea_trn_override` empty and Company VAT empty | PDF prints "Under Regn" in the TRN cell (via `jea_trn_display`) |
| TC-04 | TRN override | Set `jea_trn_override` = "100123456700003" | PDF prints the override value, ignoring Company VAT |
| TC-05 | Multi-line invoice | Add 3 invoice lines with different `jea_claim_percentage`, rates and 5% tax | SI# increments 1/2/3, each row's VAT RATE/AMT and TOTAL VALUE compute correctly, Grand Total sums all lines |
| TC-06 | Logo rendering | Company has a logo image configured | Logo renders top-left at consistent size; if no logo, company name text prints as fallback (no broken image icon) |
| TC-07 | Amount in words | Total = 58,750.00 AED | Text reads "Fifty-eight thousand seven hundred fifty" (locale-correct via `amount_to_text`) |
| TC-08 | Long payment schedule text | `jea_payment_schedule` field has 5+ lines | Text wraps within the PAYMENT cell without overflowing the table border |
| TC-09 | Draft vs Posted | Print report from both Draft and Posted invoice states | Layout is identical in both states (no draft watermark unless explicitly desired — confirm with business) |
| TC-10 | Zero-tax line | Line with 0% VAT | VAT AMT column prints "-" (matching source PDF), not "0.00" |
| TC-11 | Bank details footer | Company has a `res.partner.bank` record configured | Footer prints bank name, account number, IBAN, SWIFT dynamically (not hardcoded) |
| TC-12 | No bank record configured | Remove all `bank_ids` from the company | Report should not raise an IndexError — **known gap, see Follow-ups** |

## 4. Known follow-ups before production sign-off
1. `bank_ids[0]` in the payment-info footer will raise an `IndexError` if the company has zero bank accounts configured — needs a guard (`t-if="doc.company_id.bank_ids"`) before go-live.
2. The `binding_model_id` currently binds to all `account.move` records; add a `t-if="move_type in ('out_invoice','out_refund')"`-equivalent domain or a Python `_get_report_values` override so the Print button doesn't appear on vendor bills. **Partially addressed**: the form-view tab and Claim % column are now hidden on vendor bills via `invisible` conditions, but the report action binding itself (the Print menu entry) still needs the same restriction.
3. `jea_order_ref` currently stores free text (e.g. "Agreed contract"); if the business wants this to reference an actual `sale.order`, swap it for a `Many2one('sale.order')` instead — flagged as a scope question, not implemented since the source PDF only shows free text.