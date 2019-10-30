# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, RedirectWarning, UserError


class AfterSaleStage(models.Model):
    """ Model for case stages. This models the main stages of a AfterSale Request management flow. """

    _name = 'aftersale.stage'
    _description = 'AfterSale Stage'
    _order = 'sequence, id'

    # 售后请求阶段
    name = fields.Char('Name', required=True, translate=True)
    # 默认序列
    sequence = fields.Integer('Sequence', default=20)
    # 折叠
    fold = fields.Boolean('Folded in AfterSale Pipe')
    # 已完成状态
    done = fields.Boolean('Request Done')


class AfterSaleType(models.Model):

    _name = 'aftersale.type'
    _description = 'AfterSale Type'
    _order = 'id desc'

    # 售后类型名
    name = fields.Char(srting='AfterSale Type')
    # 售后类型描述
    description = fields.Text(string='Type Description')
    # 售后类型有效性（默认有效）
    active = fields.Boolean(default=True)


class AfterSaleRequest(models.Model):
    _name = 'aftersale.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'AfterSale Request'
    _order = "id desc"

    @api.returns('self')
    def _default_stage(self):
        return self.env['aftersale.stage'].search([], limit=1)

    @api.returns('self')
    def _default_type(self):
        return self.env['aftersale.type'].search([], limit=1)

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values and self.stage_id.sequence <= 1:
            return 'aftersale.mt_req_created'
        elif 'stage_id' in init_values and self.stage_id.sequence > 1:
            return 'aftersale.mt_req_status'
        return super(AfterSaleRequest, self)._track_subtype(init_values)

    def _get_default_team_id(self):
        MT = self.env['aftersale.team']
        team = MT.search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        if not team:
            team = MT.search([], limit=1)
        return team.id

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
    product_id = fields.Many2one('product.template', string='Product', ondelete='restrict', index=True,)
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

    @api.depends('request_date', 'product_id.name', 'owner_user_id.name')
    def _get_name(self):
        for item in self:
            item.name = "%s_%s_%s" % (item.request_date, item.product_id.name, item.owner_user_id.name)

    @api.multi
    def archive_product_request(self):
        self.write({'archive': True})

    @api.multi
    def reset_product_request(self):
        """ Reinsert the aftersale request into the aftersale pipe in the first stage"""
        first_stage_obj = self.env['aftersale.stage'].search([], order="sequence asc", limit=1)
        # self.write({'active': True, 'stage_id': first_stage_obj.id})
        self.write({'archive': False, 'stage_id': first_stage_obj.id})

    @api.model
    def create(self, vals):
        """ """
        # context: no_log, because subtype already handle this
        self = self.with_context(mail_create_nolog=True)
        request = super(AfterSaleRequest, self).create(vals)
        if request.owner_user_id or request.user_id:
            request._add_followers()
        request.activity_update()
        return request

    @api.multi
    def write(self, vals):
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the AfterSale Request changes.
        if vals and 'kanban_state' not in vals and 'stage_id' in vals:
            vals['kanban_state'] = 'normal'
        res = super(AfterSaleRequest, self).write(vals)
        if vals.get('owner_user_id') or vals.get('user_id'):
            self._add_followers()
        if 'stage_id' in vals:
            self.filtered(lambda m: m.stage_id.done).write({'close_date': fields.Date.today()})
            self.activity_feedback(['aftersale.mail_act_aftersale_request'])
        if vals.get('user_id') or vals.get('schedule_date'):
            self.activity_update()
        if vals.get('product_id'):
            # need to change description of activity also so unlink old and create new activity
            self.activity_unlink(['aftersale.mail_act_aftersale_request'])
            self.activity_update()
        return res

    def activity_update(self):
        """ Update aftersale activities based on current record set state.
        It reschedule, unlink or create aftersale request activities. """
        self.filtered(lambda request: not request.schedule_date).activity_unlink(['aftersale.mail_act_aftersale_request'])
        for request in self.filtered(lambda request: request.schedule_date):
            date_dl = fields.Datetime.from_string(request.schedule_date).date()
            updated = request.activity_reschedule(
                ['aftersale.mail_act_aftersale_request'],
                date_deadline=date_dl,
                new_user_id=request.user_id.id or request.owner_user_id.id or self.env.uid)
            if not updated:
                if request.product_id:
                    note = _('Request planned for <a href="#" data-oe-model="%s" data-oe-id="%s">%s</a>') % (
                        request.product_id._name, request.product_id.id, request.product_id.display_name)
                else:
                    note = False
                request.activity_schedule(
                    'aftersale.mail_act_aftersale_request',
                    fields.Datetime.from_string(request.schedule_date).date(),
                    note=note, user_id=request.user_id.id or request.owner_user_id.id or self.env.uid)

    def _add_followers(self):
        for request in self:
            partner_ids = (request.owner_user_id.partner_id + request.user_id.partner_id).ids
            request.message_subscribe(partner_ids=partner_ids)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)


class AfterSaleTeam(models.Model):
    _name = 'aftersale.team'
    _description = 'AfterSale Teams'

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

    # For the dashboard only
    todo_request_ids = fields.One2many('aftersale.request', string="Requests", copy=False, compute='_compute_todo_requests')
    todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_todo_requests')
    todo_request_count_date = fields.Integer(string="Number of Requests Scheduled", compute='_compute_todo_requests')
    todo_request_count_high_priority = fields.Integer(string="Number of Requests in High Priority", compute='_compute_todo_requests')
    todo_request_count_block = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_requests')
    todo_request_count_unscheduled = fields.Integer(string="Number of Requests Unscheduled", compute='_compute_todo_requests')

    @api.one
    @api.depends('request_ids.stage_id.done')
    def _compute_todo_requests(self):
        self.todo_request_ids = self.request_ids.filtered(lambda e: e.stage_id.done==False)
        self.todo_request_count = len(self.todo_request_ids)
        self.todo_request_count_date = len(self.todo_request_ids.filtered(lambda e: e.schedule_date != False))
        self.todo_request_count_high_priority = len(self.todo_request_ids.filtered(lambda e: e.priority == '3'))
        self.todo_request_count_block = len(self.todo_request_ids.filtered(lambda e: e.kanban_state == 'blocked'))
        self.todo_request_count_unscheduled = len(self.todo_request_ids.filtered(lambda e: not e.schedule_date))

