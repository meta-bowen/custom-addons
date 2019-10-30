# -*- coding: utf-8 -*-

{
    'name': 'Sale Extend',
    'author': 'Mr.Wan',
    'version': '1.0',
    'category': 'Sales',
    'description': """
        1. 在产品档案中增加价格表视图，并与价格表数据双向绑定
        2. 添加自定义发票模板
    """,
    'depends': ['product', 'sale'],
    'data': [
        'security/evaluate_security.xml',
        'security/ir.model.access.csv',
        'views/pricelist_views.xml',
        'views/invoice_views.xml',
        'views/product_evaluate_views.xml',

    ],
    'installable': True,
    'auto_install': False
}
