

# 3.6 售后管理
> wanbowen
## 0920, 23, 24, 25 | Total 4 Day
 
### 需求描述
追溯产品问题，减少业务过程中的问题，从而提高用户满意度，进而达到促进销售的目标。

需求范围：
- 问题有描述
- 可分派责任人
- 处理过程与结果可追溯

### 解决方案
#### 方案规划
1. 模型设计：
    - 售后请求模型（aftersale.request）：
    ```python
    # 售后请求Title
    name = fields.Char('Subjects', store=True, compute='_get_name')
    # 公司id
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    # 售后请求描述
    description = fields.Text('Description')
    # 请求日期
    request_date = fields.Date('Request Date', track_visibility='onchange', default=fields.Date.context_today,
                               help="Date requested for the aftersale to happen")
    # 请求人
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid)
    # 产品分类
    category_id = fields.Many2one(
        'product.category', 'Category', related='product_id.categ_id',
        store=True,
        readonly=True, help="Select category for the current product")
    # 产品
    product_id = fields.Many2one('product.template', string='Product', ondelete='restrict', index=True)
    # 负责人
    user_id = fields.Many2one('res.users', string='Technician', track_visibility='onchange', oldname='technician_user_id')
    # 售后阶段
    stage_id = fields.Many2one('aftersale.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', default=_default_stage)
    # 看板优先级
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
    # 看板颜色
    color = fields.Integer('Color Index')
    # 售后请求关闭时间
    close_date = fields.Date('Close Date', help="Date the aftersale was finished. ")
    # 看板状态
    kanban_state = fields.Selection([('normal', 'In Progress'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', required=True, default='normal', track_visibility='onchange')
    # 归档（失效）
    archive = fields.Boolean(default=False, help="Set archive to true to hide the aftersale request without deleting it.")
    # 售后类型
    aftersale_type = fields.Many2one('aftersale.type', string='AfterSale Type', default=_default_type)
    # 计划时间
    schedule_date = fields.Datetime('Scheduled Date', help="Date the aftersale team plans the aftersale.  It should not differ much from the Request Date. ")
    # 售后团队
    aftersale_team_id = fields.Many2one('aftersale.team', string='Team', required=True, default=_get_default_team_id)
    # 持续时间
    duration = fields.Float(help="Duration in hours and minutes.")
    ```
    - 售后类型模型（aftersale.type）：
    ```python
    # 售后类型名
    name = fields.Char(srting='AfterSale Type')
    # 售后类型描述
    description = fields.Text(string='Type Description')
    # 售后类型有效性（默认有效）
    active = fields.Boolean(default=True)
    ```
    - 售后团队模型（aftersale.team）：
    ```python
    # 售后团队名
    name = fields.Char(required=True, translate=True)
    # 团队有效性（默认有效）
    active = fields.Boolean(default=True)
    # 公司id
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    # 团队成员
    member_ids = fields.Many2many('res.users', 'aftersale_team_users_rel', string="Team Members")
    # 看板颜色
    color = fields.Integer("Color Index", default=0)
    # 售后请求记录集
    request_ids = fields.One2many('aftersale.request', 'aftersale_team_id', copy=False)
    ```
    - 售后阶段模型（aftersale.stage）：
    ```python
    # 售后请求阶段
    name = fields.Char('Name', required=True, translate=True)
    # 默认序列
    sequence = fields.Integer('Sequence', default=20)
    # 折叠
    fold = fields.Boolean('Folded in AfterSale Pipe')
    # 已完成状态
    done = fields.Boolean('Request Done')
    ```
2. 需求1： 问题描述：
    - 在售后请求模型中实现：
        1. 售后请求描述：description
3. 需求2： 不同阶段分派不同负责人：
    - 在售后请求模型实现该需求：
        1. 售后阶段： stage_id
        2. 负责人： user_id
4. 需求3： 处理过程与结果可追溯
    - 售后请求模块继承 mail.thread模型实现该需求:通过记录售后请求相应状态变更来实现处理过程的可追溯性
5. 核心模型： 售后请求（aftersale.request）

6. 视图设计：
    - 参考[保养]模块设计风格，包含以下视图模型：
        - kanban视图
        - tree视图
        - form视图
        - search视图
7. 中英互译

8. 创建新的模型分类：
    ```html
    <record id="module_category_after_sale" model="ir.module.category">
        <!--创建model分类-->
        <field name="name">AfterSale</field>
    </record>
    ```
9. 创建 售后管理 安全组：AfterSale Manager
   
#### 具体实施
1. 安全权限管理设定如下：
    - 售后管理 安全组：AfterSale Manager
     ```html
    <!-- This group is only allowed to deal with aftersale -->
    <record id="group_aftersale_manager" model="res.groups">
        <field name="name">AfterSale Manager</field>
        <field name="category_id" ref="module_category_after_sale"/>
        <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
        <field name="comment">The user will be able to manage aftersale.</field>
    </record>
    ```
   - 权限文件设定
    ```python
    id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
    # aftersale_manager组的用户对aftersale_type模型具有所有权限
    access_type_admin_user,aftersale.type.admin.user,model_aftersale_type,group_aftersale_manager,1,1,1,1
    # base.group_user组的用户对aftersale_type模型具有只读权限
    access_type_user,aftersale.type.user,model_aftersale_type,base.group_user,1,0,0,0
    # base.group_user组的用户对aftersale_request模型具有所有权限
    access_aftersale_system_user,aftersale.request.system.user,model_aftersale_request,base.group_user,1,1,1,1
    # base.group_user组的用户对aftersale_request模型具有只读权限
    access_aftersale_stage_user,aftersale.stage.user,model_aftersale_stage,base.group_user,1,0,0,0
    # aftersale_manager组的用户对aftersale_stage模型具有所有权限
    access_aftersale_stage_admin_user,aftersale.request.stage system user,model_aftersale_stage,group_aftersale_manager,1,1,1,1
    # base.group_user组的用户对aftersale_team模型具有只读权限
    access_aftersale_team_user,aftersale.team.user,model_aftersale_team,base.group_user,1,0,0,0
    # aftersale_manager组的用户对aftersale_team模型具有所有权限
    access_aftersale_team_admin_user,aftersale.team.admin.user,model_aftersale_team,group_aftersale_manager,1,1,1,1
    ```
   
2. 视图设计效果：
    - 整体概览：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160134_b9cbd505_5136250.png "屏幕截图.png")
    - 售后团队视图：
        - tree：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160321_436d38d3_5136250.png "屏幕截图.png")
        - form：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160342_c64db384_5136250.png "屏幕截图.png")
    - 售后阶段视图：
        - tree：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160410_5a882495_5136250.png "屏幕截图.png")
    - 售后类型视图：
        - tree：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160448_f4983e9b_5136250.png "屏幕截图.png")
        - form：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160510_6bbba54f_5136250.png "屏幕截图.png")
    - 售后请求视图：
        - kanban：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160542_db86d63c_5136250.png "屏幕截图.png")
        - form：![输入图片说明](https://images.gitee.com/uploads/images/2019/0925/160649_78b29c0b_5136250.png "屏幕截图.png")
3. 计算字段:售后请求 name，自动生成相应Title：
    ```
    @api.depends('request_date', 'product_id.name', 'owner_user_id.name')
    def _get_name(self):
        for item in self:
            item.name = "%s_%s_%s" % (item.request_date, item.product_id.name, item.owner_user_id.name)
    ```
4. 代码详情请见 custom_addons/aftersale 模块