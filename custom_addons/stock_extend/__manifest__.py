# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock Extend',
    'version': '1.0',
    'category': 'Warehouse',
    'author': 'Mr.Wan',
    'description': """
    1. 
    2. 
    """,
    'depends': ['product', 'barcodes'],
    'website': 'http://odoo.wanbowen.com',
    'sequence': 123,
    'data': [
        'security/ir.model.access.csv',
        'security/stock_extend_security.xml',
        'views/stock_extend_view.xml',
    ],
    'installable': True,
}
