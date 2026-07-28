# -*- coding: utf-8 -*-
from odoo import models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_update_income_account(self):
        """Open the 'Update Income Account' pop-up wizard for this invoice.

        Kept as a thin method on account.move  so
        the actual update logic lives in one place: the wizard's
        action_confirm(). This method's only job is to launch the pop-up
        pre-filled with the current invoice.
        """
        self.ensure_one()
        return {
            'name': _('Update Income Account'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.update.income.account.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            },
        }
