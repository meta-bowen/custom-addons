# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo.tests.common import TransactionCase
from dateutil import relativedelta
import datetime

class TestEquipment(TransactionCase):
    """ Test used to check that when doing equipment/aftersale_request/equipment_category creation."""

    def setUp(self):
        super(TestEquipment, self).setUp()
        self.equipment = self.env['aftersale.equipment']
        self.aftersale_request = self.env['aftersale.request']
        self.res_users = self.env['res.users']
        self.aftersale_team = self.env['aftersale.team']
        self.main_company = self.env.ref('base.main_company')
        res_user = self.env.ref('base.group_user')
        res_manager = self.env.ref('aftersale.group_equipment_manager')

        self.user = self.res_users.create(dict(
            name="Normal User/Employee",
            company_id=self.main_company.id,
            login="emp",
            email="empuser@yourcompany.example.com",
            groups_id=[(6, 0, [res_user.id])]
        ))

        self.manager = self.res_users.create(dict(
            name="Equipment Manager",
            company_id=self.main_company.id,
            login="hm",
            email="eqmanager@yourcompany.example.com",
            groups_id=[(6, 0, [res_manager.id])]
        ))

    def test_10_equipment_request_category(self):

        # Create a new equipment
        equipment_01 = self.equipment.sudo(self.manager).create({
            'name': 'Samsung Monitor "15',
            'category_id': self.ref('aftersale.equipment_monitor'),
            'technician_user_id': self.ref('base.user_root'),
            'owner_user_id': self.user.id,
            'assign_date': time.strftime('%Y-%m-%d'),
            'serial_no': 'MT/127/18291015',
            'model': 'NP355E5X',
            'color': 3,
        })

        # Check that equipment is created or not
        assert equipment_01, "Equipment not created"

        # Create new aftersale request
        aftersale_request_01 = self.aftersale_request.sudo(self.user).create({
            'name': 'Resolution is bad',
            'user_id': self.user.id,
            'owner_user_id': self.user.id,
            'equipment_id': equipment_01.id,
            'color': 7,
            'stage_id': self.ref('aftersale.stage_0'),
            'aftersale_team_id': self.ref('aftersale.equipment_team_aftersale')
        })

        # I check that aftersale_request is created or not
        assert aftersale_request_01, "AfterSale Request not created"

        # I check that Initially aftersale request is in the "New Request" stage
        self.assertEquals(aftersale_request_01.stage_id.id, self.ref('aftersale.stage_0'))

        # I check that change the aftersale_request stage on click statusbar
        aftersale_request_01.sudo(self.user).write({'stage_id': self.ref('aftersale.stage_1')})

        # I check that aftersale request is in the "In Progress" stage
        self.assertEquals(aftersale_request_01.stage_id.id, self.ref('aftersale.stage_1'))

    def test_20_cron(self):
        """ Check the cron creates the necessary preventive aftersale requests"""
        equipment_cron = self.equipment.create({
            'name': 'High AfterSale Monitor because of Color Calibration',
            'category_id': self.ref('aftersale.equipment_monitor'),
            'technician_user_id': self.ref('base.user_root'),
            'owner_user_id': self.user.id,
            'assign_date': time.strftime('%Y-%m-%d'),
            'period': 7,
            'color': 3,
        })

        aftersale_request_cron = self.aftersale_request.create({
            'name': 'Need a special calibration',
            'user_id': self.user.id,
            'request_date': (datetime.datetime.now() + relativedelta.relativedelta(days=7)).strftime('%Y-%m-%d'),
            'aftersale_type': 'preventive',
            'owner_user_id': self.user.id,
            'equipment_id': equipment_cron.id,
            'color': 7,
            'stage_id': self.ref('aftersale.stage_0'),
            'aftersale_team_id': self.ref('aftersale.equipment_team_aftersale')
        })

        self.env['aftersale.equipment']._cron_generate_requests()
        # As it is generating the requests for one month in advance, we should have 4 requests in total
        tot_requests = self.aftersale_request.search([('equipment_id', '=', equipment_cron.id)])
        self.assertEqual(len(tot_requests), 1, 'The cron should have generated just 1 request for the High AfterSale Monitor.')

    def test_21_cron(self):
        """ Check the creation of aftersale requests by the cron"""

        team_test = self.aftersale_team.create({
            'name': 'team_test',
        })
        equipment = self.equipment.create({
            'name': 'High AfterSale Monitor because of Color Calibration',
            'category_id': self.ref('aftersale.equipment_monitor'),
            'technician_user_id': self.ref('base.user_root'),
            'owner_user_id': self.user.id,
            'assign_date': time.strftime('%Y-%m-%d'),
            'period': 7,
            'color': 3,
            'aftersale_team_id': team_test.id,
            'aftersale_duration': 3.0,
        })

        self.env['aftersale.equipment']._cron_generate_requests()
        tot_requests = self.aftersale_request.search([('equipment_id', '=', equipment.id)])
        self.assertEqual(len(tot_requests), 1, 'The cron should have generated just 1 request for the High AfterSale Monitor.')
        self.assertEqual(tot_requests.aftersale_team_id.id, team_test.id, 'The aftersale team should be the same as equipment one')
        self.assertEqual(tot_requests.duration, 3.0, 'Equipement aftersale duration is not the same as the request one')
