# -*- coding: utf-8 -*-
{
    'name': 'ABRA Fleet Service Billing',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Automate vendor bill drafts for overdue vehicle service, based on odometer readings',
    'description': """
ABRA Fleet Service Billing
============================
Cross-module automation between Fleet and Accounting:

* service_interval_km / estimated_service_cost configured per vehicle
* needs_service computed automatically from the current odometer reading
* Daily scheduled action creates a draft Vendor Bill (account.move,
  in_invoice) for every vehicle that needs service, linked back to the
  vehicle for traceability
* "Mark as Serviced" button on the vehicle resets the tracking baseline,
  logs the service date on the chatter, and cancels any still-pending
        'views/fleet_vehicle_views.xml',
        'views/account_move_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
  (unposted) vendor bill the cron generated for that vehicle
""",
    'author': 'ABRA Assessment- Abhinand K R',
    'license': 'LGPL-3',
    'depends': ['fleet', 'account'],
    'data': [
        'views/fleet_vehicle_views.xml',
        'views/account_move_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
