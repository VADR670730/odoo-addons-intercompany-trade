# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from odoo.addons.intercompany_trade_base.tests.test_module import (
    TestModule as TestIntercompanyTradeBase,
)


class TestBase(TestIntercompanyTradeBase):
    def setUp(self):
        super(TestBase, self).setUp()
        self.test_00_log_installed_modules()


class TestModule(TransactionCase):
    def setUp(self):
        super(TestModule, self).setUp()
        self.PurchaseOrder = self.env["purchase.order"]
        self.PurchaseOrderLine = self.env["purchase.order.line"]
        self.normal_supplier = self.env.ref(
            "intercompany_trade_base.normal_supplier"
        )
        self.config = self.env.ref(
            "intercompany_trade_base.intercompany_trade"
        )
        self.customer_user = self.env.ref(
            "intercompany_trade_base.customer_user"
        )
        self.customer_company = self.env.ref(
            "intercompany_trade_base.customer_company"
        )
        self.customer_product = self.env.ref(
            "intercompany_trade_product.product_customer_service"
        )

    def test_01_invoice_purchase_order_not_intercompany_trade(self):
        """[Non Regression] Test if invoicing is done for
        Not Intercompany Trade Purchases"""
        purchase_order = self._create_purchase_order(self.normal_supplier)
        purchase_order.sudo(self.customer_user).button_confirm()
        res = purchase_order.sudo(self.customer_user).action_view_invoice()
        print("===========")
        print(res)
        print("===========")
        self.assertNotEqual(
            res,
            False,
            "Invoicing a non Intercompany Trade purchase order should"
            " generate invoice",
        )

    # def test_02_invoice_purchase_order_intercompany_trade(self):
    #     """[Functional Test] Test if invoicing is not done for
    #     Intercompany Trade Purchases"""
    #     purchase_order = self._create_purchase_order(
    #         self.config.supplier_partner_id
    #     )
    #     purchase_order.sudo(self.customer_user).button_confirm()
    #     res = purchase_order.sudo(self.customer_user).action_view_invoice()
    #     self.assertEqual(
    #         res,
    #         False,
    #         "Invoicing an Intercompany Trade purchase order should not"
    #         " generate invoice",
    #     )

    def _create_purchase_order(self, partner):
        purchase_order = self.PurchaseOrder.sudo(self.customer_user).create(
            {
                "name": "Intercompany Trade PO Test",
                "partner_id": partner.id,
                "company_id": self.customer_company.id,
            }
        )
        self.PurchaseOrderLine.sudo(self.customer_user).create(
            {
                "order_id": purchase_order.id,
                "product_id": self.customer_product.id,
                "name": "Intercompany Trade PO Line Test",
                "price_unit": 15.0,
                "product_qty": 1.0,
                "date_planned": "1970-01-01",
                "product_uom": self.customer_product.uom_id.id,
            }
        )
        return purchase_order
