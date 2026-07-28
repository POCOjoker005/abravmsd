# -*- coding: utf-8 -*-
{
    'name': 'JEA Custom Invoice Report',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Custom PDF invoice report replicating the JEA Design Services layout',
    'description': """
JEA Custom Invoice Report
==========================
Adds a pixel-matched custom PDF report for Customer Invoices (account.move),
reproducing the JEA Design Services LLC invoice layout, including:

* Company letterhead block (logo + address) and Bill To block
* Job #, Order Ref, Payment Schedule and Project reference fields
* Itemised lines with Claim %, Qty (UoM), Rate, Value, VAT rate/amount, Total
* Grand total row + amount-in-words
* Signature/stamp block and bank payment information footer

All figures on the report are pulled dynamically from the standard Invoice
form view (account.move / account.move.line) plus a small set of custom
fields added on account.move for job/order/project references.
""",
    'author': 'ABRA Assessment- Abhinand K R',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
        'report/jea_invoice_report_action.xml',
        'report/jea_invoice_report_template.xml',
    ],
    'installable': True,
    'application': False,
}
