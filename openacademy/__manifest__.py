# -*- coding: utf-8 -*-
{
    'name': "Open Academy",

    'summary': """This App manages training""",

    'description': """
        The Citadel offers training for any individuals including Knights, Squire, etc.
    """,

    'author': "Jasper Rivera",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Training Grounds',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'board'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/openacademy.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/partner.xml',
        'reports.xml',
        'views/session_board.xml',
        'reports/course_details_report.xml',
        'reports/report_course_pdf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
