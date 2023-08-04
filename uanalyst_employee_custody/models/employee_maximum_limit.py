# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class EmployeeMaximumLimit(models.Model):
    _name = 'employee.maximum'
    _description = 'Employee Maximum Limit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', related='company_id.currency_id', store=True, readonly=False, precompute=True,
        required=True,
    )
    maximum_limit = fields.Monetary('Maximum Limit', currency_field='currency_id', tracking=True)

    @api.constrains('maximum_limit')
    def enter_maximum_limit(self):
        for rec in self:
            if rec.maximum_limit == 0:
                raise ValidationError(_('Please enter the amount of money in Maximum Limit field'))

