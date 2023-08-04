# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import xlsxwriter
import io


class CreateExcelWizard(models.TransientModel):
    _name = 'create.excel.wizard'
    _description = 'Create Excel Wizard'

    employee_ids = fields.Many2many('hr.employee', string='Employee')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    state = fields.Selection([
        ('draft', 'DRAFT'), ('submitted', 'SUBMITTED'), ('first_approved', 'FIRST APPROVED'),
        ('second_approved', 'SECOND APPROVED'), ('paid', 'PAID')], string="status")

    def print_report_xml(self):
        data = {
            'form_data': self.read()[0],
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        print("Data >>", data)
        return self.env.ref('uanalyst_employee_custody.report_employee_custody_xml').report_action(self, data=data)

    def action_print_xml_report(self):
        return {
            'type': "ir.actions.act_url",
            'target': "new",
            'tag': 'reload',
            'url': "/print_xml_report?date_from={date_from}&date_to={date_to}&state={state}&employee_ids={employee_id}".format(
                date_from=self.date_from, date_to=self.date_to,
                state=str(self.state),
                employee_id=self.employee_ids.ids if self.employee_ids else False,
            )
        }

    def get_xml_report(self, response, date_from, date_to, state, employee_id):
        cr = self._cr
        query = """select employee_id from employee_custody"""
        cr.execute(query)
        dat = cr.dictfetchall()

        return {
            'date_from': date_from,
            'date_to': date_to,
            'dat': dat
        }

    def action_print_excel_report(self):
        return {
            'type': "ir.actions.act_url",
            'target': "new",
            'tag': 'reload',
            'url': "/web/content/download/payroll_summary_report?date_from={date_from}&date_to={date_to}&state={state}&employee_ids={employee_id}".format(
                date_from=self.date_from, date_to=self.date_to,
                state=str(self.state),
                employee_id=self.employee_ids.ids if self.employee_ids else False,
            )
        }

    def get_xlsx_report(self, response, date_from, date_to, state, employee_id,):
        employee_id = self.env['hr.employee'].browse(employee_id)

        employees = []
        all_employees = []
        custodies_employee_id = []

        if employee_id:
            for rec in employee_id:
                domain = []
                domain += [('employee_id.id', '=', rec.id)]
                if date_from != 'False':
                    domain += [('date', '>=', date_from)]
                if date_to != 'False':
                    domain += [('date', '<=', date_to)]
                if state != 'False':
                    domain += [('state', '=', state)]
                record = self.env['employee.custody'].search_count(domain)
                if record > 1:
                    custody_id = self.env['employee.custody'].search(domain)
                    for rec1 in custody_id:
                        custodies_employee_id.append(rec1.id)
                else:
                    employees += self.env['employee.custody'].search_read(domain)

        else:
            domain = []
            if date_from != 'False':
                domain += [('date', '>=', date_from)]
            if date_to != 'False':
                domain += [('date', '<=', date_to)]
            if state != 'False':
                domain += [('state', '=', state)]
            all_employees_id = self.env['employee.custody'].search(domain)
            for rec2 in all_employees_id:
                all_employees.append(rec2.id)

        data = {
            'custodies_employee_id': custodies_employee_id,
            'employees': employees,
            'all_employees': all_employees,
        }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True, 'strings_to_formulas': False, })
        sheet = workbook.add_worksheet('Employee Custody')
        # sheet.set_column(0, 0, 30)
        sheet.set_column('A:I', 25)
        sheet.set_default_row(25)
        date_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'align': 'center', 'font_size': 11, 'num_format': 'yyyy-mm-dd'})
        text_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'align': 'center', 'font_size': 11})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'fg_color': '#071f75', 'font_size': 16, 'font_color': 'white',
             'bold': True, 'align': 'center', 'border': 2, 'left': 1,
             'bottom': 1,
             'right': 1, 'top': 1})

        row = 0
        col = 0
        sheet.write(row, col, 'Employee', header_style)
        sheet.write(row, col + 1, 'Reference', header_style)
        sheet.write(row, col + 2, 'State', header_style)
        sheet.write(row, col + 3, 'Advance', header_style)
        sheet.write(row, col + 4, 'Balance', header_style)
        sheet.write(row, col + 5, 'The liquidated amount', header_style)
        sheet.write(row, col + 6, 'Bank', header_style)
        sheet.write(row, col + 7, 'Account Number', header_style)
        sheet.write(row, col + 8, 'Date', header_style)

        for emp in data['custodies_employee_id']:
            emp_id = self.env['employee.custody'].browse(emp)
            if emp_id.balance == 0:
                liquidated_amount = 0
            else:
                liquidated_amount = emp_id.advance - emp_id.balance
            col = 0
            row += 1

            sheet.write(row, col, emp_id.employee_id.name, text_style)
            col += 1
            sheet.write(row, col, emp_id.reference, text_style)
            col += 1
            sheet.write(row, col, emp_id.state, text_style)
            col += 1
            sheet.write(row, col, emp_id.advance, text_style)
            col += 1
            sheet.write(row, col, emp_id.balance, text_style)
            col += 1
            sheet.write(row, col, liquidated_amount, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.bank_id.name, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.acc_number, text_style)
            col += 1
            sheet.write(row, col, emp_id.date, date_style)
            col += 1

        for emp in data['employees']:
            emp_id = self.env['employee.custody'].browse(emp.get('id'))
            if emp_id.balance == 0:
                liquidated_amount = 0
            else:
                liquidated_amount = emp.get('advance') - emp.get('balance')
            col = 0
            row += 1

            sheet.write(row, col, emp.get('employee_id')[1], text_style)
            col += 1
            sheet.write(row, col, emp.get('reference'), text_style)
            col += 1
            sheet.write(row, col, emp.get('state'), text_style)
            col += 1
            sheet.write(row, col, emp.get('advance'), text_style)
            col += 1
            sheet.write(row, col, emp.get('balance'), text_style)
            col += 1
            sheet.write(row, col, liquidated_amount, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.bank_id.name, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.acc_number, text_style)
            col += 1
            sheet.write(row, col, emp.get('date'), date_style)
            col += 1

        for emp in data['all_employees']:
            emp_id = self.env['employee.custody'].browse(emp)
            if emp_id.balance == 0:
                liquidated_amount = 0
            else:
                liquidated_amount = emp_id.advance - emp_id.balance
            col = 0
            row += 1

            sheet.write(row, col, emp_id.employee_id.name, text_style)
            col += 1
            sheet.write(row, col, emp_id.reference, text_style)
            col += 1
            sheet.write(row, col, emp_id.state, text_style)
            col += 1
            sheet.write(row, col, emp_id.advance, text_style)
            col += 1
            sheet.write(row, col, emp_id.balance, text_style)
            col += 1
            sheet.write(row, col, liquidated_amount, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.bank_id.name, text_style)
            col += 1
            sheet.write(row, col, emp_id.employee_id.bank_account_id.acc_number, text_style)
            col += 1
            sheet.write(row, col, emp_id.date, date_style)
            col += 1

        workbook.close()
        output.seek(0)
        generated_file = response.stream.write(output.read())
        output.close()

        return generated_file
        # return self.env.ref('uanalyst_employee_custody.report_employee_custody_xlsx').report_action(self, data=data)
