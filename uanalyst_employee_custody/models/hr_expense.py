# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    custody_id = fields.Many2one('employee.custody', string="Custody")
    total_receipts = fields.Integer(string="Receipts", default="0")

    @api.constrains('total_amount')
    def check_balance(self):
        for rec in self:
            if rec.custody_id and rec.custody_id.balance_store < rec.total_amount:
                raise ValidationError(_('The amount of balance not enough for this custody'))

    def button_receipts(self):
        # print("read .............", self.env['employee.custody'].search([]).read(['employee_id']))
        return




