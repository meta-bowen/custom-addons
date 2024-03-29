# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestEquipmentMulticompany(TransactionCase):

    def test_00_equipment_multicompany_user(self):
        """Test Check aftersale with equipment manager and user in multi company environment"""

        # Use full models
        Equipment = self.env['aftersale.equipment']
        AfterSaleRequest = self.env['aftersale.request']
        Category = self.env['aftersale.equipment.category']
        ResUsers = self.env['res.users']
        ResCompany = self.env['res.company']
        AfterSaleTeam = self.env['aftersale.team']

        # Use full reference.
        group_user = self.env.ref('base.group_user')
        group_manager = self.env.ref('aftersale.group_equipment_manager')

        # Company A
        company_a = ResCompany.create({
            'name': 'Company A',
            'currency_id': self.env.ref('base.USD').id,
        })

        # Create one child company having parent company is 'Your company'
        company_b = ResCompany.create({
            'name': 'Company B',
            'currency_id': self.env.ref('base.USD').id,
            'parent_id': company_a.id,
        })

        # Create equipment manager.
        equipment_manager = ResUsers.create({
            'name': 'Equipment Manager',
            'company_id': company_a.id,
            'login': 'e_equipment_manager',
            'email': 'eqmanager@yourcompany.example.com',
            'groups_id': [(6, 0, [group_manager.id])],
            'company_ids': [(6, 0, [company_a.id, company_b.id])]
        })

        # Create equipment user
        user = ResUsers.create({
            'name': 'Normal User/Employee',
            'company_id': company_b.id,
            'login': 'emp',
            'email': 'empuser@yourcompany.example.com',
            'groups_id': [(6, 0, [group_user.id])],
            'company_ids': [(6, 0, [company_b.id])]
        })

        # create a aftersale team for company A user
        team = AfterSaleTeam.sudo(equipment_manager).create({
            'name': 'Metrology',
            'company_id': company_a.id,
        })
        # create a aftersale team for company B user
        teamb = AfterSaleTeam.sudo(equipment_manager).create({
            'name': 'Subcontractor',
            'company_id': company_b.id,
        })

        # User should not able to create equipment category.
        with self.assertRaises(AccessError):
            Category.sudo(user).create({
                'name': 'Software',
                'company_id': company_b.id,
                'technician_user_id': user.id,
            })

        # create equipment category for equipment manager
        category_1 = Category.sudo(equipment_manager).create({
            'name': 'Monitors',
            'company_id': company_b.id,
            'technician_user_id': equipment_manager.id,
        })

        # create equipment category for equipment manager
        Category.sudo(equipment_manager).create({
            'name': 'Computers',
            'company_id': company_b.id,
            'technician_user_id': equipment_manager.id,
        })

        # create equipment category for equipment user
        Category.sudo(equipment_manager).create({
            'name': 'Phones',
            'company_id': company_a.id,
            'technician_user_id': equipment_manager.id,
        })

        # Check category for user equipment_manager and user
        self.assertEquals(Category.sudo(equipment_manager).search_count([]), 3)
        self.assertEquals(Category.sudo(user).search_count([]), 2)

        # User should not able to create equipment.
        with self.assertRaises(AccessError):
            Equipment.sudo(user).create({
                'name': 'Samsung Monitor 15',
                'category_id': category_1.id,
                'assign_date': time.strftime('%Y-%m-%d'),
                'company_id': company_b.id,
                'owner_user_id': user.id,
            })

        Equipment.sudo(equipment_manager).create({
                'name': 'Acer Laptop',
                'category_id': category_1.id,
                'assign_date': time.strftime('%Y-%m-%d'),
                'company_id': company_b.id,
                'owner_user_id': user.id,
            })

        # create an equipment for user
        Equipment.sudo(equipment_manager).create({
            'name': 'HP Laptop',
            'category_id': category_1.id,
            'assign_date': time.strftime('%Y-%m-%d'),
            'company_id': company_b.id,
            'owner_user_id': equipment_manager.id,
        })
        # Now there are total 2 equipments created and can view by equipment_manager user
        self.assertEquals(Equipment.sudo(equipment_manager).search_count([]), 2)

        # And there is total 1 equipment can be view by Normal User ( Which user is followers)
        self.assertEquals(Equipment.sudo(user).search_count([]), 1)

        # create an equipment team BY user
        with self.assertRaises(AccessError):
            AfterSaleTeam.sudo(user).create({
                'name': 'Subcontractor',
                'company_id': company_b.id,
            })

        # create an equipment category BY user
        with self.assertRaises(AccessError):
            Category.sudo(user).create({
                'name': 'Computers',
                'company_id': company_b.id,
                'technician_user_id': user.id,
            })

        # create an aftersale stage BY user
        with self.assertRaises(AccessError):
            self.env['aftersale.stage'].sudo(user).create({
                'name': 'identify corrective aftersale requirements',
            })

        # Create an aftersale request for ( User Follower ).
        AfterSaleRequest.sudo(user).create({
            'name': 'Some keys are not working',
            'company_id': company_b.id,
            'user_id': user.id,
            'owner_user_id': user.id,
        })

        # Create an aftersale request for equipment_manager (Admin Follower)
        AfterSaleRequest.sudo(equipment_manager).create({
            'name': 'Battery drains fast',
            'company_id': company_a.id,
            'user_id': equipment_manager.id,
            'owner_user_id': equipment_manager.id,
        })

        # Now here is total 1 aftersale request can be view by Normal User
        self.assertEquals(AfterSaleRequest.sudo(equipment_manager).search_count([]), 2)
        self.assertEquals(AfterSaleRequest.sudo(user).search_count([]), 1)
