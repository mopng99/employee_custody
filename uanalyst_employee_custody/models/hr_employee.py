# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from werkzeug.urls import url_encode


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    total_custodies = fields.Integer(string="Count Custodies", compute="_compute_total_custody", store=True)
    custody_ids = fields.One2many('employee.custody', 'employee_id')

    @api.depends('custody_ids')
    def _compute_total_custody(self):
        for rec in self:
            rec.total_custodies = len(rec.custody_ids)
