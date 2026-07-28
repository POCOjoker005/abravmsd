# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    abra_service_interval_km = fields.Integer(
        string='Service Interval (km)',
        help='Distance, in km, after which this vehicle is due for service again.',
    )
    abra_estimated_service_cost = fields.Float(
        string='Estimated Service Cost',
        help='Used as the line amount on the automatically generated vendor bill.',
    )
    abra_last_service_odometer = fields.Float(
        string='Odometer at Last Service',
        default=0.0,
        copy=False,
        help='Baseline odometer reading used to compute whether service is due. '
             'Reset by the "Mark as Serviced" button.',
    )
    abra_needs_service = fields.Boolean(
        string='Needs Service',
        compute='_compute_abra_needs_service',
        store=True,
        help='True when the odometer reading since the last recorded service '
             'has reached or exceeded the configured service interval.',
    )

    @api.depends('odometer', 'abra_last_service_odometer', 'abra_service_interval_km')
    def _compute_abra_needs_service(self):
        for vehicle in self:
            vehicle.abra_needs_service = bool(
                vehicle.abra_service_interval_km
                and (vehicle.odometer - vehicle.abra_last_service_odometer) >= vehicle.abra_service_interval_km
            )

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    def _cron_generate_service_bills(self):
        """Daily cron entry point. Finds every vehicle currently due for
        service and creates one draft vendor bill per vehicle - unless a
        draft bill from a previous run is still sitting there unreviewed,
        in which case we skip it rather than generating duplicates every
        single day until Finance gets to it.
        """
        vehicles_due = self.search([('abra_needs_service', '=', True)])
        AccountMove = self.env['account.move']
        for vehicle in vehicles_due:
            already_pending = AccountMove.search_count([
                ('abra_vehicle_id', '=', vehicle.id),
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'draft'),
            ])
            if already_pending:
                continue
            vehicle._abra_create_service_vendor_bill()

    def _abra_create_service_vendor_bill(self):
        self.ensure_one()
        print("ssssssssss")
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'abra_vehicle_id': self.id,
            'date': fields.Date.today(),
            'ref': _('Scheduled service - %(vehicle)s', vehicle=self.display_name),
            'invoice_line_ids': [(0, 0, {
                'name': _(
                    'Scheduled service for %(vehicle)s (interval: %(interval)s km, '
                    'odometer: %(odometer)s km)',
                    vehicle=self.display_name,
                    interval=self.abra_service_interval_km,
                    odometer=int(self.odometer),
                ),
                'quantity': 1,
                'price_unit': self.abra_estimated_service_cost,
            })],
        })
        print(move,"move")
        self.message_post(
            body=_(
                'Draft vendor bill %(bill)s was generated automatically because the '
                'odometer (%(odometer)s km) reached the configured service interval.',
                bill=move.name or _('(Draft)'),
                odometer=int(self.odometer),
            )
        )
        return move

    # ------------------------------------------------------------------
    # "Mark as Serviced" button
    # ------------------------------------------------------------------
    def action_mark_as_serviced(self):
        for vehicle in self:
            pending_bills = self.env['account.move'].search([
                ('abra_vehicle_id', '=', vehicle.id),
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'draft'),
            ])
            if pending_bills:
                # Cancel rather than unlink: keeps an audit trail of the
                # fact a bill was generated and later superseded by an
                # actual service, instead of silently deleting records.
                pending_bills.button_cancel()

            service_date = fields.Date.context_today(vehicle)
            vehicle.abra_last_service_odometer = vehicle.odometer
            vehicle.message_post(
                body=_(
                    'Vehicle marked as serviced on %(date)s. Odometer baseline reset '
                    'to %(odometer)s km.',
                    date=service_date,
                    odometer=int(vehicle.odometer),
                )
            )
        return True
