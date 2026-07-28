# -*- coding: utf-8 -*-
{
    'name': 'ABRA Update Income Account',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Bulk-update the income account on all lines of a draft customer invoice',
    'description': """
ABRA Update Income Account
============================
Adds an "Update Income Account" button on the Customer Invoice form (visible
only while the invoice is in Draft) that opens a small pop-up wizard. On
confirmation, every invoice line's income account is updated to the account
chosen in the wizard.
""",
    'author': 'ABRA Assessment- Abhinand K R',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_income_account_wizard_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
