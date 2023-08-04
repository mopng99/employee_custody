# -*- coding: utf-8 -*-

{
    'name': 'UAnalyst Employee Custody',
    'version': '1.2',
    'category': 'UAnalyst Employee Custody',
    'summary': 'UAnalyst Employee Custody',
    'description': """
    UAnalyst Employee Custody.
    """,
    'author': "Mohamed Nagy",
    'sequence': '-100',
    'depends': ['base',
                'mail',
                'hr',
                'account',
                'hr_contract',
                'hr_expense',
                ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/menus.xml',
        'views/create_excel_wizard_views.xml',
        'views/hr_expense_views.xml',
        'views/configuration_custody_views.xml',
        'views/employee_custody_views.xml',
        'views/employee_maximum_limit_views.xml',
    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}
