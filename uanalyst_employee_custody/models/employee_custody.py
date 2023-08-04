# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class EmployeeCustody(models.Model):
    _name = 'employee.custody'
    _description = 'Employee Custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    employee_maximum_ids = fields.One2many('employee.maximum', 'employee_id')

    reference = fields.Char('Custody Reference', readonly=True, default=lambda self: _('New'))
    note = fields.Text(string="Description")
    current_contract = fields.Char(string='Current Contract', compute='_compute_contract', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', related='company_id.currency_id', readonly=False, precompute=True, store=True)
    advance = fields.Monetary('Advance', currency_field='currency_id', required="1", tracking=True)
    balance = fields.Monetary('Balance', currency_field='currency_id', compute='compute_balance')
    balance_store = fields.Float('Balance Employee')
    total_expenses = fields.Integer(string="Expenses", compute='_compute_total_expenses')
    department_id = fields.Many2one(string='Department', related='employee_id.department_id')
    job_id = fields.Many2one(string='Job Position', related='employee_id.job_id')
    work_location_id = fields.Many2one(string='Work Location', related='employee_id.work_location_id')
    date = fields.Date('Date', tracking=True, default=fields.Date.today)
    ua_dev_Reason = fields.Text('Reason', tracking=True, translate=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', tracking=True)
    move_id = fields.Many2one('account.move', string='Journal Entry')
    state = fields.Selection([
        ('draft', 'DRAFT'), ('submitted', 'SUBMITTED'), ('first_approved', 'FIRST APPROVED'),
        ('second_approved', 'SECOND APPROVED'), ('paid', 'PAID')]
        , default="draft", string="status", tracking=True)

    def name_get(self):
        res = []
        for field in self:
            if self.env.context.get('special_display_name', False):
                res.append((field.id, '%s' % (field.employee_id.name)))
            else:
                res.append((field.id, '%s (%s)' % (field.reference, field.balance)))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('note'):
                vals['note'] = 'New Custody'
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('employee.custody') or _('New')
        return super(EmployeeCustody, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state in ('first_approved', 'second_approved', 'paid'):
                raise ValidationError(_('You can delete custody state is draft or submitted only'))
        return super(EmployeeCustody, self).unlink()

    @api.depends('employee_id')
    def _compute_contract(self):
        for rec in self:
            if self.env['hr.contract.history'].browse(self.employee_id.id).state == 'cancel':
                rec.current_contract = 'Canceled'
            elif self.env['hr.contract.history'].browse(self.employee_id.id).state == 'draft':
                rec.current_contract = 'New'
            elif self.env['hr.contract.history'].browse(self.employee_id.id).state == 'close':
                rec.current_contract = 'Expired'
            elif self.env['hr.contract.history'].browse(self.employee_id.id).state == 'open':
                rec.current_contract = 'Running'
            else:
                rec.current_contract = ""

    @api.depends('state')
    def compute_balance(self):
        for rec in self:
            record = self.env['hr.expense'].search([('custody_id', '=', rec.id)])
            if rec.state == 'paid':
                for rec1 in record:
                    rec.balance += rec1.total_amount
                rec.balance = rec.advance - rec.balance
                rec.balance_store = rec.balance
            else:
                rec.balance = rec.balance

    @api.constrains('advance', 'state')
    def enter_advance(self):
        for rec in self:
            max_advance = 0
            record = self.env['employee.maximum'].search([('employee_id.name', '=', rec.employee_id.name),
                                                          ('analytic_account_id.name', '=',
                                                           rec.analytic_account_id.name)])

            record2 = self.env['employee.custody'].search([('employee_id.name', '=', rec.employee_id.name)])
            record3 = self.env['hr.expense'].search(
                [('employee_id.name', '=', rec.employee_id.name), ('state', '=', 'done')])
            if record:
                if rec.advance == 0:
                    raise ValidationError(_('Please enter the amount of money in ِAdvance field'))
                for rec2 in record2:
                    max_advance += rec2.advance
                if record3:
                    for rec3 in record3:
                        max_advance -= rec3.total_amount
                for rec1 in record:
                    if rec.advance > rec1.maximum_limit:
                        raise ValidationError(_('Maximum Limit For Advance is %s' % rec1.maximum_limit))
                    if max_advance > rec1.maximum_limit:
                        max_advance -= rec.advance
                        raise ValidationError(
                            _('Maximum Limit For Advance is %s And You Used %s' % (rec1.maximum_limit, max_advance)))
            else:
                raise ValidationError(_('You are not defined Maximum Limit For Advance'))

    def _compute_total_expenses(self):
        for rec in self:
            rec.total_expenses = self.env['hr.expense'].search_count(
                [('custody_id', '=', self.id), ('state', '=', 'done')])

    def open_hr_expense_tree(self):
        view = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,search,form',
            'res_model': 'hr.expense',
            'name': _('Expenses'),
            'domain': "[('custody_id','=',%s), ('state', '=', 'done')]" % self.id,
            'view_type': 'tree,form',
            'context': {
                'default_employee_id': self.employee_id.id,
            }
        }
        return view

    # address_home_id
    # user_id.partner_id

    def action_paid(self):
        if not self.employee_id.address_home_id:
            raise ValidationError(_('The employee of the custody must have a partner'))
        partner_id = self.employee_id.address_home_id
        custody_configuration = self.env['configuration.custody'].search([], limit=1)
        if not custody_configuration:
            raise ValidationError(_('Please configure the debit/credit account to complete the payment'))
        credit_account_id = custody_configuration.credit_account_id
        debit_account_id = custody_configuration.debit_account_id
        journal_id = custody_configuration.journal_id
        for rec in self:
            rec.state = 'paid'
            account_move = self.env['account.move'].sudo().create({
                'move_type': 'entry',
                'date': fields.Date.context_today(self),
                "journal_id": journal_id.id,
                "currency_id": rec.currency_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': 'Custody Credit',
                        'account_id': credit_account_id.id,
                        'partner_id': partner_id.id,
                        'debit': 0.0,
                        'credit': rec.advance,
                    }),
                    (0, 0, {
                        'name': 'Custody Debit',
                        'account_id': debit_account_id.id,
                        'partner_id': partner_id.id,
                        'debit': rec.advance,
                        'credit': 0.0,
                    }),
                ],
            })
            rec.move_id = account_move.id

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_first_approved(self):
        for rec in self:
            rec.state = 'first_approved'

    def action_second_approved(self):
        for rec in self:
            rec.state = 'second_approved'
