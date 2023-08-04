from ast import literal_eval

from odoo import http
from odoo.http import content_disposition, request


class XLSXReportController(http.Controller):

    @http.route('/web/content/download/payroll_summary_report', type='http', csrf=False)
    def get_report_xlsx(self, **kw):
        date_from = kw.get('date_from')
        date_to = kw.get('date_to')
        state = str(kw.get('state'))
        employee_id = literal_eval(kw.get('employee_ids'))

        response = request.make_response(
            None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                     (
                         'Content-Disposition',
                         content_disposition('Employee Custody Report' + '.xlsx'))
                     ]
        )
        request.env['create.excel.wizard'].get_xlsx_report(
            response,
            date_from,
            date_to,
            state,
            employee_id,
        )
        return response

