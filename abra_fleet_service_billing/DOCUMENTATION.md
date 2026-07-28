# Activity 4 — Fleet × Finance Automation

## 1. Time tracking

| Task | Estimated | Actual |
|---|---|---|
| Design: baseline-tracking approach, cron dedup logic, cancel-vs-unlink decision | 15 min | 25 min |
| `fleet.vehicle` fields + `needs_service` compute | 15 min | 15 min |
| `account.move` link field | 5 min | 5 min |
| Cron method + `ir.cron` record | 20 min | 20 min |
| "Mark as Serviced" action | 15 min | 15 min |
| Views (vehicle form + vendor bill form) | 20 min | 20 min |
| Manual test pass on running instance | 20 min | *(pending — see note)* |
| Documentation + test cases | 10 min | 20 min |
| **Total** | **120 min** | **~120 min (excl. live test pass)** |

**Note:** same caveat as the earlier activities — no live Odoo 19 instance in this sandbox, so validation here is syntax linting + manual trace of the ORM logic, not an actual install/run. Given how much back-and-forth the Activity 1 report needed once it hit a real instance, I'd treat this module as needing a genuine test pass before sign-off even more than the others — crons in particular are easy to get subtly wrong in ways that only show up over multiple simulated "days."

## 2. Module structure

```
abra_fleet_service_billing/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── fleet_vehicle.py      # fields, needs_service compute, cron method, Mark as Serviced
│   └── account_move.py       # abra_vehicle_id link field
├── views/
│   ├── fleet_vehicle_views.xml   # form fields, ribbon, button
│   └── account_move_views.xml    # vehicle field on vendor bill form
└── data/
    └── ir_cron.xml            # daily scheduled action
```

## 3. Design decisions

- **`abra_last_service_odometer` as an explicit baseline field**, rather than trying to infer "last service" from bill history. `needs_service` is simply `(current odometer − baseline) >= interval`. This keeps the compute cheap and the logic auditable — no querying invoices to figure out vehicle state.
- **`needs_service` is stored** (`store=True`) specifically so the cron can do a plain `search([('abra_needs_service', '=', True)])` instead of computing the condition in Python for every vehicle on every run.
- **Cron dedup check**: before creating a bill, the cron checks whether a draft vendor bill already exists for that vehicle. Without this, a vehicle that stays overdue for a week (because Finance hasn't gotten to it yet) would get a new duplicate draft bill every single day the cron runs.
- **"Mark as Serviced" cancels rather than unlinks** the pending bill (`button_cancel()`, not `unlink()`). Requirement wording allowed either; I chose cancel because it preserves an audit trail — you can still see in the Vendor Bills list that a bill was generated and later voided, rather than the record vanishing with no trace. If your Finance team specifically wants hard deletion instead (e.g. to keep the vendor bills list completely clean of noise), swapping `button_cancel()` for `unlink()` is a one-line change — flagged as a judgment call, not a hard requirement in the brief.
- **No vendor (`partner_id`) is set on the generated bill.** The requirement doesn't specify which vendor should be billed for service, and guessing one would be worse than leaving it blank — Odoo allows a vendor bill to exist in Draft without a partner, and the brief explicitly frames this as "for the Finance team to review and post," which implies the draft isn't expected to be complete/postable as generated. Flagged as an open question for the business, not silently resolved.
- **Line item has no product**, just a text description with `price_unit = abra_estimated_service_cost`. Simpler than requiring every vehicle to have a "Service" product configured, and matches the requirement's wording ("using estimated_service_cost as the line amount") rather than inventing a product-catalogue dependency that wasn't asked for.

## 4. Test cases

| # | Test case | Steps | Expected result |
|---|---|---|---|
| TC-01 | needs_service computes correctly | Vehicle: interval=10,000 km, baseline=0, odometer=10,500 | `abra_needs_service` = True |
| TC-02 | Not yet due | Vehicle: interval=10,000 km, baseline=0, odometer=8,000 | `abra_needs_service` = False |
| TC-03 | No interval configured | `abra_service_interval_km` = 0 (unset) | `abra_needs_service` = False, regardless of odometer (avoids a 0km interval flagging every vehicle immediately) |
| TC-04 | Cron creates a bill | Run `_cron_generate_service_bills()` manually (or trigger the scheduled action) on a vehicle needing service | One draft `account.move` (in_invoice) created, `abra_vehicle_id` set, line amount = `abra_estimated_service_cost` |
| TC-05 | Cron doesn't duplicate | Run the cron twice in a row without posting/cancelling the first bill | Only one draft bill exists after the second run |
| TC-06 | Cron skips vehicles not due | Vehicle below its interval | No bill created for that vehicle |
| TC-07 | Mark as Serviced resets baseline | Vehicle at odometer=10,500, click Mark as Serviced | `abra_last_service_odometer` = 10,500; `abra_needs_service` recomputes to False |
| TC-08 | Mark as Serviced posts chatter note | Click Mark as Serviced | A message appears in the vehicle's chatter with the service date and odometer reading |
| TC-09 | Mark as Serviced cancels pending bill | Cron has created a draft bill; click Mark as Serviced | The draft bill's state becomes `cancel`; a new one is NOT auto-created until the vehicle becomes overdue again |
| TC-10 | Mark as Serviced with no pending bill | No draft bill exists for the vehicle; click Mark as Serviced | No error; baseline still resets and chatter note still posts |
| TC-11 | Mark as Serviced doesn't touch posted bills | A vendor bill for this vehicle was already posted (not draft) | That posted bill is left untouched — only draft bills tied to the vehicle are cancelled |
| TC-12 | Vehicle field visible on the generated bill | Open a bill created by the cron | "Vehicle" field shows on the form, read-only |
| TC-13 | Vehicle field hidden on manual bills | Create a normal vendor bill by hand, unrelated to fleet | "Vehicle" field is not shown (empty + invisible) |
| TC-14 | Ribbon indicator | Vehicle with `abra_needs_service` = True | "Needs Service" ribbon shows on the vehicle form |

## 5. Known follow-ups / open questions for the business

1. **No vendor is assigned** on the generated bill — confirm with Finance whether there should be a default "Service Vendor" per vehicle (would mean adding a `Many2one('res.partner')` field on the vehicle) or whether leaving it blank for manual selection is acceptable.
2. **Currency/company**: the bill is created without explicitly setting `company_id` — it will default to the current user's company via `account.move`'s own defaults, which should be correct in a single-company setup but is worth an explicit test in a multi-company fleet (a vehicle belonging to Company A being serviced should generate a bill in Company A's books, not the acting user's default company).
3. If the business wants a notification (e.g. email or activity) to Finance when a new service bill is generated, rather than relying on someone to check the Vendor Bills list — not implemented here since it wasn't in the stated requirement, but a natural next step (`mail.activity` on the created move, or a `mail.template` trigger).
