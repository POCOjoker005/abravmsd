# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # --- Header reference fields shown on the JEA invoice layout -----
    # Design note: only fields with NO existing standard equivalent were
    # added. TRN reuses res.company.vat, Qty("LS") reuses the standard
    # product_uom_id, and the amount-in-words line reuses the built-in
    # currency_id.amount_to_text() helper - none of those were duplicated
    # as custom fields.

    jea_job_number = fields.Char(
        string='Job #',
        copy=False,
        help='Internal job/project code shown on the printed invoice (e.g. 24-0926).',
    )
    jea_order_ref = fields.Char(
        string='Order Reference',
        copy=False,
        help='Free-text reference to the signed contract/order, e.g. "Agreed contract".',
    )
    jea_order_ref_date = fields.Date(
        string='Order Reference Date',
        copy=False,
    )
    jea_payment_schedule = fields.Text(
        string='Payment Schedule',
        copy=False,
        help='Free text describing the agreed payment milestones, '
             'e.g. "25% Signing Fee, 25% Design Phase 1, ..."',
    )
    jea_project_reference = fields.Char(
        string='Project Reference',
        copy=False,
        help='Short project description printed in the PROJECT column of the report.',
    )
    jea_trn_override = fields.Char(
        string='TRN Override',
        copy=False,
        help='Use this only when the company TRN should NOT be printed as-is '
             '(e.g. "Under Regn" while VAT registration is pending). '
             'If left empty, the report falls back to the company VAT/TRN, '
             'and to "Under Regn" if that is empty too.',
    )
    jea_trn_display = fields.Char(
        string='TRN (Display)',
        compute='_compute_jea_trn_display',
        help='Computed value actually printed on the report.',
    )

    @api.depends('jea_trn_override', 'company_id.vat')
    def _compute_jea_trn_display(self):
        for move in self:
            move.jea_trn_display = (
                move.jea_trn_override
                or move.company_id.vat
                or 'Under Regn'
            )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    jea_claim_percentage = fields.Float(
        string='Claim %',
        digits=(5, 2),
        copy=False,
        help='Percentage of the total contract value being claimed on this line, '
             'e.g. 25.00 for "25% Signing fees". Purely informational - it does '
             'not affect price_subtotal/price_total, which remain the source '
             'of truth for accounting.',
    )