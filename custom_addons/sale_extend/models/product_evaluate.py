import logging
from odoo import api, fields, models, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class ProductEvaluate(models.Model):
    """
    产品评价模型
    """
    _name = "product.evaluate"
    _description = 'Product Evaluate'
    # 排序策略
    _order = 'name, date desc'

    name = fields.Char(string='Title', compute='_compute_name', store=True)
    date = fields.Date(string='Date')
    active = fields.Boolean('Active?', default=True)
    # 评价维度字段
    appearance = fields.Selection([
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ], copy=False, required=True, string='Appearance rate')
    quality = fields.Selection([
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ], copy=False, required=True, string='Quality rate')
    function = fields.Selection([
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ], copy=False, required=True, string='Function rate')
    cost_performance = fields.Selection([
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ], copy=False, required=True, string='Cost-Performance rate')
    # 产品额外评价
    notes = fields.Text('Evaluate Notes')
    # 当前评价平均分
    avg_rating = fields.Float(string='Average Rating', digits=(3, 2), help='The rate of avg', compute='_get_avg_rating', store=True)
    # 历史总体平均分
    avg_rating_history = fields.Float(string='History Average Rating', digits=(3, 2), help='The History rate of avg', compute='_get_avg_rating_history', store=True)
    # 当前产品总体平均分
    avg_rating_product = fields.Float(string='Product Average Rating', digits=(3, 2), help='The Product rate of avg', compute='_get_avg_rating_product', store=True)
    # 关联字段
    product_tmpl_id = fields.Many2one('product.template', string="Product Name", require=True)
    customer_id = fields.Many2one('res.partner', string="Customer Name", require=True)
    # datetime = fields.Datetime(string='Recode Datetime', default=lambda self: fields.Datetime.now(), store=True)

    @api.depends('appearance', 'quality', 'function', 'cost_performance')
    def _get_avg_rating(self):
        """
        计算当前记录评价平均分
        :return:
        """
        for rate in self:
            sum = rate.appearance + rate.quality + rate.function + rate.cost_performance
            rate.avg_rating = sum/4
            _logger.info("_get_avg_rating rate.avg_rating >>> %r", rate.avg_rating)

    @api.depends('avg_rating')
    def _get_avg_rating_history(self):
        """
        获取全部评价的平均评分

        在数据表的数据发生更新时触发该方法进行计算
        :return:
        """
        print('self>>>', self)
        sum = 0
        count = 0
        items = self.env['product.evaluate'].search([])
        print('items>>>', items)
        for item in items:
            count += 1
            sum += item.avg_rating
        # 计算总体均值
        if count:
            # 保留两位小数
            avg_sum = '%.2f' % (sum/count)
            print('avg_sum>>>', avg_sum)
            for item in self:
                item.avg_rating_history = avg_sum
            for item in items:
                # 使用SQL
                self.env.cr.execute('update product_evaluate set avg_rating_history=%s where id=%s', (avg_sum, item.id))

    @api.depends('avg_rating')
    def _get_avg_rating_product(self):
        """
        获取选择的产品的总体平均分
        :return:
        """
        for item in self:
            # 点选了某个产品
            if item.product_tmpl_id.id:
                # 数据表中该产品的记录集合
                products = self.env['product.evaluate'].search([('product_tmpl_id', '=', item.product_tmpl_id.id)])
                _logger.info('products>>> %r', products)
                sum = 0
                count = 0
                for product in products:
                    sum += product.avg_rating
                    count += 1
                if count:
                    avg_sum = '%.2f' % (sum/count)
                    item.avg_rating_product = avg_sum
                    # 更新整个数据表该产品的该字段值
                    for product in products:
                        self.env.cr.execute('update product_evaluate set avg_rating_product=%s where id=%s', (avg_sum, product.id))

    @api.depends('date', 'product_tmpl_id.name', 'customer_id.name')
    def _compute_name(self):
        """
        自动生成评价title
        :return:
        """
        for item in self:
            item.name = "%s_%s_%s" % (item.date, item.product_tmpl_id.name, item.customer_id.name)

    @api.multi
    def button_avg_rating_history(self):
        for rate in self:
            raise Warning('History Average Rating = %s' % rate.avg_rating_history)

    @api.multi
    def button_avg_rating_product(self):
        for rate in self:
            raise Warning('Product Average Rating = %s' % rate.avg_rating_product)


class ProductEvalutate2(models.Model):
    _inherit = "product.evaluate"




