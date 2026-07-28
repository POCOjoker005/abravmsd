# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

EXCLUDED_DISPLAY_TYPES = ('line_section', 'line_note')

class AccountMoveUpdateIncomeAccountWizard(models.TransientModel):
    _name = 'account.move.update.income.account.wizard'
    _description = 'Update Income Account on Invoice Lines'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='move_id.company_id',
        string='Company',
    )
    income_account_id = fields.Many2one(
        'account.account',
        string='Income Account',
        required=True,
        domain="[('account_type', 'in', ('income', 'income_other')),"
               " ('company_ids', 'in', company_id)]",
        help='This account will replace the account on every product/service '
             'line of the invoice (section and note lines are left untouched).',
    )
    affected_line_count = fields.Integer(
        string='Lines to update',
        compute='_compute_affected_line_count',
    )

    @api.depends('move_id')
    def _compute_affected_line_count(self):
        for wizard in self:
            wizard.affected_line_count = len(
                wizard.move_id.invoice_line_ids.filtered(
                    lambda l: l.display_type not in EXCLUDED_DISPLAY_TYPES
                )
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_id = res.get('move_id') or self.env.context.get('default_move_id')
        if move_id:
            move = self.env['account.move'].browse(move_id)
            # Defense in depth: the button is already hidden outside Draft,
            # but the wizard itself must not silently allow the update if
            # somehow opened on a posted/cancelled invoice (e.g. via a
            # saved action URL or another button reusing this context).
            if move.state != 'draft':
                raise UserError(_(
                    'The income account can only be updated while the '
                    'invoice is in Draft status.'
                ))
        return res

    def action_confirm(self):
        self.ensure_one()
        if self.move_id.state != 'draft':
            raise UserError(_(
                'The income account can only be updated while the '
                'invoice is in Draft status.'
            ))

        # Force a fresh read from DB in case invoice lines were
        # deleted/recreated (e.g. recomputed) after this wizard was opened.
        self.move_id.invalidate_recordset(['invoice_line_ids'])

        lines = self.move_id.invoice_line_ids.exists().filtered(
            lambda l: l.display_type not in EXCLUDED_DISPLAY_TYPES
        )
        if not lines:
            raise UserError(_(
                'This invoice has no product/service lines to update. '
                'The invoice may have changed since this window was opened — '
                'please close it and try again.'
            ))

        lines.write({'account_id': self.income_account_id.id})

        self.move_id.message_post(
            body=_(
                'Income account updated to %(account)s on %(count)s invoice line(s).',
                account=self.income_account_id.display_name,
                count=len(lines),
            )
        )
        return {'type': 'ir.actions.act_window_close'}