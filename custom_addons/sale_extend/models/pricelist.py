from odoo import api, fields, models, tools, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template Inherit"
    _order = "sequence asc, id desc"

    item_ids = fields.One2many(
        'product.pricelist.item', 'product_tmpl_id', 'Pricelist Items',
        copy=True)
