# -*- coding: utf-8 -*-
# Copyright (C) 2014 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import SUPERUSER_ID
from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.osv.osv import except_osv
from openerp.tools.translate import _


class intercompany_trade_config(Model):
    _name = 'intercompany.trade.config'
    _description = 'Intercompany Trade'
    _order = 'customer_company_id, supplier_company_id'

    # Columns section
    _columns = {
        'name': fields.char(
            'Name', required=True, size=64),
        'active': fields.boolean(
            'Active',
            help="""By unchecking the active field you can disable """
            """the trading between the two company without deleting it."""),
        'customer_user_id': fields.many2one(
            'res.users', 'Customer User', required=True,
            domain="[('company_id', '=', customer_company_id)]",
            help="""This user will be used to create customer data when
            supplier users update datas.\n
            Please take that this user must have good access right on the
            customer company."""),
        'customer_company_id': fields.many2one(
            'res.company', 'Customer Company', required=True,
            help="""Select the company that could purchase to the other."""),
        'supplier_user_id': fields.many2one(
            'res.users', 'Supplier User', required=True,
            domain="[('company_id', '=', supplier_company_id)]",
            help="""This user will be used to create supplier data when
            customer users update datas.\n
            Please take that this user must have good access right on the
            supplier company."""),
        'supplier_company_id': fields.many2one(
            'res.company', 'Supplier Company', required=True,
            help="""Select the company that could sale to the other."""),
        'customer_partner_id': fields.many2one(
            'res.partner', 'Customer Partner in the Supplier Company',
            readonly=True),
        'supplier_partner_id': fields.many2one(
            'res.partner', 'Supplier Partner in the Customer Company',
            readonly=True),
    }

    _defaults = {
        'name': '/',
        'active': True,
        'customer_user_id': SUPERUSER_ID,
        'supplier_user_id': SUPERUSER_ID,
    }

    _sql_constraints = [
        (
            'customer_supplier_company_uniq',
            'unique(customer_company_id, supplier_company_id)',
            'Customer and Supplier company must be uniq !'),
    ]

    # Custom Section
    def _get_intercompany_trade_by_partner_company(
            self, cr, uid, partner_id, company_id, type,
            context=None):
        """
        Return a intercompany.trade.config.
        * If type='in', partner_id is a supplier in the customer company;
          (purchase workflow)
        * If type='out', partner_id is a customer in the supplier company;
          (sale workflow)
        """
        if type == 'in':
            domain = [
                ('supplier_partner_id', '=', partner_id),
                ('customer_company_id', '=', company_id),
            ]
        else:
            domain = [
                ('customer_partner_id', '=', partner_id),
                ('supplier_company_id', '=', company_id),
            ]
        rit_id = self.search(cr, uid, domain, context=context)[0]
        return self.browse(cr, uid, rit_id, context=context)

    def _prepare_partner_from_company(
            self, cr, uid, company_id, inner_company_id, context=None):
        """
            Return vals for the creation of a partner, depending of
            a company_id.
        """
        rc_obj = self.pool['res.company']
        rc = rc_obj.browse(cr, uid, company_id, context=context)
        return {
            'name': rc.name + ' ' + _('(Intercompany Trade)'),
            'street': rc.street,
            'street2': rc.street2,
            'city': rc.city,
            'zip': rc.zip,
            'state_id': rc.state_id.id,
            'country_id': rc.country_id.id,
            'website': rc.website,
            'phone': rc.phone,
            'fax': rc.fax,
            'email': rc.email,
            'vat': rc.vat,
            'is_company': True,
            'image': rc.logo,
        }

    # Overload Section
    def create(self, cr, uid, vals, context=None):
        """Create or update associated partner in each company"""
        rp_obj = self.pool['res.partner']
        res = super(intercompany_trade_config, self).create(
            cr, uid, vals, context=context)
        rit_id = self.search(cr, uid, [
            ('customer_company_id', '=', vals['supplier_company_id']),
            ('supplier_company_id', '=', vals['customer_company_id']),
        ], context=context)
        if len(rit_id) == 0:
            rit = self.browse(cr, uid, res, context=context)
            ctx = context.copy()
            ctx['ignore_intercompany_trade_check'] = True
            # create supplier in customer company
            partner_vals = self._prepare_partner_from_company(
                cr, uid, vals['supplier_company_id'],
                vals['customer_company_id'], context=context)
            partner_vals['customer'] = False
            partner_vals['supplier'] = True
            partner_vals['intercompany_trade'] = True
            partner_vals['company_id'] = vals['customer_company_id']
            supplier_partner_id = rp_obj.create(
                cr, rit.customer_user_id.id, partner_vals, context=ctx)

            # create customer in supplier company
            partner_vals = self._prepare_partner_from_company(
                cr, uid, vals['customer_company_id'],
                vals['supplier_company_id'], context=context)
            partner_vals['customer'] = True
            partner_vals['supplier'] = False
            partner_vals['intercompany_trade'] = True
            partner_vals['company_id'] = vals['supplier_company_id']
            customer_partner_id = rp_obj.create(
                cr, rit.supplier_user_id.id, partner_vals, context=ctx)

            # Update intercompany trade config
            self.write(cr, uid, [res], {
                'customer_partner_id': customer_partner_id,
                'supplier_partner_id': supplier_partner_id,
            }, context=context)
        else:
            # Change the actual partners
            rit = self.browse(cr, uid, rit_id, context=context)[0]
            rp_obj.write(
                cr, uid, [rit.customer_partner_id.id], {'supplier': True},
                context=context)
            rp_obj.write(
                cr, uid, [rit.supplier_partner_id.id], {'customer': True},
                context=context)
            self.write(cr, uid, [res], {
                'customer_partner_id': rit.supplier_partner_id.id,
                'supplier_partner_id': rit.customer_partner_id.id,
            }, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """ Block possibility to change customer or supplier company"""
        if 'customer_company_id' in vals.keys()\
                or 'supplier_company_id' in vals.keys():
            if context.get('install_mode', False):
                vals.pop('customer_company_id')
                vals.pop('supplier_company_id')
            else:
                raise except_osv(
                    _("Error!"),
                    _("""You can not change customer or supplier company."""
                        """If you want to do so, please disable this"""
                        """ intercompany trade and create a new one."""))
        return super(intercompany_trade_config, self).write(
            cr, uid, ids, vals, context=context)
