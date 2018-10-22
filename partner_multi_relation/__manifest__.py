# -*- coding: utf-8 -*-
# Copyright 2013-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Partner relations",
    "version": "10.0.2.0.0",
    "author": "Therp BV,Camptocamp,Odoo Community Association (OCA)",
    "complexity": "normal",
    "category": "Customer Relationship Management",
    "license": "AGPL-3",
    "depends": [
        'contacts',
        'web_domain_field',
        'web_tree_many2one_clickable',
    ],
    "demo": [
        "demo/res_partner_category_demo.xml",
        "demo/res_partner_demo.xml",
        "demo/res_partner_relation_type_demo.xml",
        "demo/res_partner_relation_demo.xml",
    ],
    "data": [
        "views/res_partner_relation_all.xml",
        'views/res_partner.xml',
        'views/res_partner_relation_type.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',
    ],
    "auto_install": False,
    "installable": True,
}
