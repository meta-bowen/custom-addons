# 销售管理板块
> wanbowen
## 0909 Mon

## 3.2 价格管理 
### 需求描述
1. 在产品档案中设置价格表策略，根据不同的销售渠道、产品型号、不同购买数量、不同时期等因素设置相应的价格表。
2. 价格表的定价策略将在订单创建时被自动带出，供订单创建者进行参考，创建者也可以自己通过手动进行价格调整。 产品价格信息可以通过用户操作同步到Amazon渠道。
### 解决方案
#### 方案规划：
- [x] 1.价格表相关数据均在数据表：product.pricelist.item
- [x] 2.需将数据表数据在产品信息中以表格table形式展现
- [x] 3.且产品详情页中的价格表与价格表进行双向数据绑定


#### 具体实施：

## 0910 Tue
1. ~~理解 product.pricelist model~~
2. ~~将产品的product_id与product.pricelist中的product_id对应起来~~ （修正为product_tmpl_id）
3. ~~产品价格表数据已经获取到，但在产品页的价格表中新增价格表时出现：~~(通过为Tree添加editable=“buttom”解决该问题)
    - 货币类型无法定义
    - 无法定义价格表组

4. ~~为 product_template 增加关联product_pricelist表many2one字段~~(无效)
## 0911 Wed
5. 通过显示固定价格开启价格可编辑，隐藏计算字段 price：
    - ![输入图片说明](https://images.gitee.com/uploads/images/2019/0911/130650_b8976f16_5136250.png "屏幕截图.png") 
    - 效果如下：![输入图片说明](https://images.gitee.com/uploads/images/2019/0911/130749_07a6efcf_5136250.png "屏幕截图.png")

#### 未解决项
1. ~~Product中的Pricelist栏暂无法实现定制化显示，两处代码系统只运行其中一处：~~[已解决]
```python
<record id="product_pricelist_view_extend" model="ir.ui.view">
            <field name="name">product.pricelist.form.extend</field>
            <field name="model">product.pricelist</field>
            <field name="priority" eval="16" />
            <field name="arch" type="xml">
                    <form string="Products Price List">
                        <sheet>
                            <div class="oe_title">
                                <h1><field name="name" placeholder="e.g. USD Retailers"/></h1>
                            </div>
                            <group>
                                <field name="currency_id" groups="base.group_multi_currency"/>
                            </group>
                        </sheet>
                    </form>
            </field>
        </record>
```
```python
<record id="product_pricelist_view" model="ir.ui.view">
            <field name="name">product.pricelist.form</field>
            <field name="model">product.pricelist</field>
            <field name="arch" type="xml">
                <form string="Products Price List">
                    <sheet>
                        <div class="oe_button_box" name="button_box">
                            <button name="toggle_active" type="object"
                                    class="oe_stat_button" icon="fa-archive">
                                <field name="active" widget="boolean_button"
                                    options='{"terminology": "archive"}'/>
                            </button>
                        </div> 
```

## 3.3.2 订单发票
### 需求描述
1. 支持2个发票模板，供用户操作选择；
2. 模板自动抓取订单信息、发票地址信息生成发票内容；
3. 合并开票 – 针对同一个客户的多张订单；
4. 系统需要识别企业客户，订单完成自动按默认发送发票；
5. 针对客户税号填写错误问题，自动检查地址栏，如果识别为税号，则由系统把信息调入税号栏；

### 解决方案
#### 方案规划
- [x] 1.继承开票模块的选择发票模板视图至销售模块
- [x] 2.通过点选相应模板后，再点击下方创建发票按钮，实现订单发票能够选择需要的发票模板并发送
- [x] 3.选定的发票模板写入公司对应的res_company数据表
#### 具体实施
1. 代码移植至自定义继承模块sale_extend：
```xml
\sale_ext\invoice_views.xml

<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <record id="view_sale_advance_payment_inv_inherit" model="ir.ui.view">
        <field name="name">Invoice Orders</field>
        <field name="model">sale.advance.payment.inv</field>
        <field name="inherit_id" ref="sale.view_sale_advance_payment_inv"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='deposit_taxes_id']" position="after">
                <separator string="Invoice Template"/>
<!--                <field name="invoice_template" string="Select a Invoice Template"/>-->
                <label for="external_report_layout_id" string="Select a Invoice Template" colspan="2" />
                <field name="external_report_layout_id" colspan="2" nolabel="1"
                        class="report_layout_container"
                        widget="report_layout" options="{
                            'field_image': 'preview_image',
                            'field_binary': 'preview_pdf'
                        }"/>

            </xpath>
        </field>
    </record>
</odoo>

```
可以实现如下样式：![输入图片说明](https://images.gitee.com/uploads/images/2019/0916/094830_a1971ac6_5136250.png)

## 0916 Mon
2. 进一步通过xpath方式将所选的对应发票模板绑定到下方的按钮上：
```
<xpath expr="//footer/button[1]" position="replace">
    <button string="Create and View Invoices" class="btn-primary" type="object" context="{'open_invoices': True}" name="create_invoices" />
</xpath>
<xpath expr="//footer/button[2]" position="replace">
    <button string="Create Invoices" class="btn-primary" type="object" name="create_invoices" />
</xpath>
```
在model中声明create_invoices方法，继承原有按钮功能，并增加相应新的逻辑：
```
@api.multi
    def create_invoices(self):
        super().create_invoices()
        ex_id = self.external_report_layout_id.id
        company_id = self.env.user.company_id.id
        # 修改res_company中external_report_layout_id值，赋值为ex_id
        self.env.cr.execute('update res_company set external_report_layout_id=%s where id=%s', (ex_id, company_id))
```
最终实现 点击不同发票模板再点击创建发票按钮后，打印&预览的发票即为设置的发票模板ID

3. 目前仍然存在的问题：
    - 在点击sale_order 的预览 & 打印按钮后，所打印的发票模板id是res_company表中的external_report_layout_id，而不同的sale_order设定的发票模板是不同的，res_company table只能存储最新设置的external_report_layout_id。
    - 改进思路：打印 & 预览 按钮所对应的代码逻辑需要与sale_order建立连接，而sale_order table中应存储对应的发票模板id external_report_layout_id
    - Create Invoices按钮代码逻辑存在部分问题，即“创建发票”按钮颜色没有发生相应变化 

4. 预览按钮代码逻辑：
```
@api.multi
    def preview_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

```
打印按钮代码逻辑：
```
@api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})

        return self.env.ref('sale.action_report_saleorder')\
            .with_context({'discard_logo_check': True}).report_action(self)
```

## 3.5 客户测评
### 需求描述
1. 按产品、客户记录测评结果，支持以图表的方式分析统计测评的结果。
2. 为产品的上架、营销提供决策支持。
### 解决方案
## 0917 Tue
#### 方案规划
1. 产品评价模型（product_evaluate）：
    - 评价名（date_productname_customername）
    - 外观（五星制）
    - 质量（五星制）
    - 功能（五星制）
    - 性价比（五星制）
    - 平均得分（float）
    - 总体均分（为所有评价得分提供参考意义）
    - 产品总体均分（为产品提供均分参考）
    - 评价补充（note）
    - date
    - 产品 关联产品模型（many2one）
    - 客户 关联客户模型（many2one）
    - 其他相关字段
2. 需要实现的视图：
    - form视图
        - 使用sheet纸张效果样式
        - 通过group形式划定三组展示
    - tree视图
        - name
        - avg_rating
        - product_tmpl_id
        - customer_id
        - date
    - search视图
        - filter功能
        - Group By功能
    - 图表视图
        - row: date
        - product_id
3. 编写i18n，实现模块内容中英互译      
#### 具体实施
1. 针对模型要求编写如下模型代码：
```python
_name = "product.evaluate"
    _description = 'Product Evaluate'
    # 排序字段
    _order = 'name, date desc'
    
    name = fields.Char(string='Title', required=True, compute='_compute_name')
    date = fields.Date()
    active = fields.Boolean('Active?', default=True)
    # 评价维度字段
    appearance = fields.Selection([
        (1, 'One-star'),
        (2, 'Two-star'),
        (3, 'Three-star'),
        (4, 'Four-star'),
        (5, 'Five-star'),
    ], default=3, copy=False, string='Appearance rate')
    quality = fields.Selection([
        (1, 'One-star'),
        (2, 'Two-star'),
        (3, 'Three-star'),
        (4, 'Four-star'),
        (5, 'Five-star'),
    ], default=3, copy=False, string='Quality rate')
    function = fields.Selection([
        (1, 'One-star'),
        (2, 'Two-star'),
        (3, 'Three-star'),
        (4, 'Four-star'),
        (5, 'Five-star'),
    ], default=3, copy=False, string='Function rate')
    cost_performance = fields.Selection([
        (1, 'One-star'),
        (2, 'Two-star'),
        (3, 'Three-star'),
        (4, 'Four-star'),
        (5, 'Five-star'),
    ], default=3, copy=False, string='Cost-Performance rate')
    # 产品额外评价
    notes = fields.Text('Internal Notes')
    # 当前评价平均分
    avg_rating = fields.Float(string='Average Rating', digits=(3, 2), help='The rate of avg', compute='_get_avg_rating')
    # 历史总体平均分
    avg_rating_history = fields.Float(string='History Average Rating', digits=(3, 2), help='The History rate of avg', compute='_get_avg_rating_history')
    # 当前产品总体平均分
    avg_rating_product = fields.Float(string='Product Average Rating', digits=(3, 2), help='The Product rate of avg', compute='_get_avg_rating_product',)
    # 关联字段
    product_tmpl_id = fields.Many2one('product.template', string="Product Name", require=True)
    customer_id = fields.Many2one('res.partner', string="Customer Name", require=True)
```
根据模型字段实现对应的form、tree、graph、pivot视图。

## 0918-19 Wed & Thu
> 出现的待解决问题：   
- ~~compute字段暂不能写入到数据库~~[stock=True 已解决]
- 历史总体平均分 & 当前产品总体平均分 计算方法有待改进[已解决]

方法如下：
```python
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
                avg_sum = '%.2f' % (sum/count)
                item.avg_rating_product = avg_sum
                # 更新整个数据表该产品的该字段值
                for product in products:
                    self.env.cr.execute('update product_evaluate set avg_rating_product=%s where id=%s', (avg_sum, product.id))

```
1. 报表视图如下：
    - ![输入图片说明](https://images.gitee.com/uploads/images/2019/0919/145516_56b63944_5136250.png "屏幕截图.png")
    - ![输入图片说明](https://images.gitee.com/uploads/images/2019/0919/145611_1f26a02b_5136250.png "屏幕截图.png")
> 红框内表示的当天有多个同一产品评价产生，这一块有待商议，讨论一下是否需要更改

> 关于图表展示这一块有待进一步探讨
 
## 0926 
## 3.7 销售业务报表
### 需求描述
销售业务报表的目的是反映销售的状况，内容包括产品的销量统计，订单的情况，个人/团队的销售业绩等。相关的报表可以分为以下几类：

1. 商品报告 – 可售商品报告/在售商品报告/渠道仓库存报告
2. 订单报告 – 待处理订单/等待中订单
3. 业绩报告 – 可选择从产品、团队、个人3个维度来分别生成报表，方便查看每天/每月/每年的销量，单个产品的成本，利润
4. 结算报告

### 解决方案
#### 方案规划
> 该版块暂定不做方案实施
#### 具体实施
