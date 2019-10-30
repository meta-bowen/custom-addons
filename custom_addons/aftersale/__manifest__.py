# -*- coding: utf-8 -*-

{
    'name': 'AfterSale',
    'version': '1.0',
    'sequence': 125,
    'category': 'AfterSale',
    'author': 'Mr.Wan',
    'description': """
        Track equipments and aftersale requests""",
    'depends': ['mail', 'product'],
    'summary': 'Track equipment and manage aftersale requests',
    'website': 'http://odoo.wanbowen.com',
    'data': [
        'security/aftersale.xml',
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/aftersale_views.xml',
        'views/aftersale_templates.xml',
    ],
    'installable': True,
    'application': True,
}
