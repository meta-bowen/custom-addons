import logging

from odoo import api, fields, models, _
from odoo.exceptions import Warning

logger =logging.getLogger(__name__)


class Invoice(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Custom Invoice"

    # invoice_template = fields.Many2one('report.layout', string='Invoice Template', required=True)
    external_report_layout_id = fields.Many2one('ir.ui.view', 'Document Template')

    @api.multi
    def create_invoices(self):
        """
        为create invoice 按钮增加功能
        :return:
        """
        ex_id = self.external_report_layout_id.id
        if ex_id:
            company_id = self.env.user.company_id.id
            # 修改res_company中external_report_layout_id值，赋值为ex_id
            self.env.cr.execute('update res_company set external_report_layout_id=%s where id=%s', (ex_id, company_id))
            super().create_invoices()
        else:
            raise Warning('Please select an Teamplate for Invoice')



class InvoiceTemplate(models.Model):
    _inherit = "report.layout"
    _description = 'Invoice Template'

    name = fields.Char('Invoice Template', compute='_compute_name')

    def _compute_name(self):
        for node in self:
            id = node.id
            node.name = 'Invoice Template %s' % id

