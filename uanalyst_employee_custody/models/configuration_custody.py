# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ConfigurationCustody(models.Model):
    _name = 'configuration.custody'
    _description = 'Configuration Custody'
    _rec_name = 'ref'

    ref = fields.Char(string="Reference")
    credit_account_id = fields.Many2one('account.account', string='Credit Account')
    debit_account_id = fields.Many2one('account.account', string='Debit Account')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', '=', 'general')])

