# coding: utf-8
# Copyright (C) 2014 - Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class IntercompanyTradeConfig(models.Model):
    _inherit = 'intercompany.trade.config'

    # Columns section
    line_ids = fields.One2many(
        comodel_name='intercompany.trade.config.line',
        inverse_name='config_id')

    # Custom Section
    @api.multi
    def _get_product_in_customer_company(self, product):
        """
            Return the product in the customer company from a product in the
            supplier company
            Realize correct check if the product is not referenced.

            :param @product: product in the supplier company
            :return : product, in the customer company
        """
        self.ensure_one()
        customer_product = self._get_product_in_customer_company_strict(
            product)
        if not customer_product:
            customer_product =\
                self._get_product_in_customer_company_approximate(product)
        if not customer_product:
            raise UserError(_(
                "You can not add the product '%s' to the"
                " current Order or Invoice because the customer didn't"
                " referenced your product. Please contact him and"
                " say him to do it.") % (product.name))
        return customer_product

    @api.multi
    def _get_product_in_customer_company_strict(self, product):
        self.ensure_one()

        product_obj = self.env['product.product']
        supplierinfo_obj = self.env['product.supplierinfo']

        # Get current Product
        product = product_obj.sudo().browse(product.id)
        supplierinfos = supplierinfo_obj.sudo().search([
            ('supplier_product_id', '=', product.id),
            ('name', '=', self.supplier_partner_id.id),
            ('company_id', '=', self.customer_company_id.id)])
        if len(supplierinfos) == 0:
            return False
        supplierinfo = supplierinfos[0]
        customer_products = product_obj.sudo(
            self.customer_user_id).with_context(active_test=False).search([
                ('company_id', '=', self.customer_company_id.id),
                ('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id),
            ])
        if len(customer_products) != 1:
            raise UserError(_(
                "You can not add '%s' to the current Order or Invoice"
                " because the customer referenced many variants of"
                " this template.") % (
                    product.name))
        return customer_products[0]

    @api.multi
    def _get_product_in_customer_company_approximate(self, product):
        """Overloadable function, allow to return a product if the
        customer did'nt referenced the supplier product, by category,
        or other rules."""
        return False
