import bootstrap
import json
import unittest
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4
from django.test import RequestFactory
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.sales.models import Customer, Invoice, InvoiceItem, SalesOrder, SalesOrderItem
from apps.products.models import Product, Category
from apps.inventory.models import Warehouse
from apps.sales.api.v1.views import invoice_collection_api, sales_order_collection_api


class ListSearchAcrossReferencesTests(unittest.TestCase):
    """Production 500 (26 Nov): searching invoices raised 'Cannot perform join in mongoDB'."""

    def setUp(self):
        self.org = Organization(name='Search org', email='s@example.com').save()
        self.other = Organization(name='Other org', email='o@example.com').save()
        self.user = User(organization=self.org, email=uuid4().hex + '@example.com', password='x', first_name='A', last_name='B').save()
        permission = patch('apps.authorization.services.AuthorizationService.has_permission', return_value=True)
        permission.start(); self.addCleanup(permission.stop)
        self.customer = Customer(organization=self.org, name='Sharma Traders', code='SHA').save()
        self.plain = Customer(organization=self.org, name='Patil Hardware', code='PAT').save()
        Customer(organization=self.other, name='Sharma Elsewhere', code='SHX').save()
        category = Category(organization=self.org, name='Goods').save()
        product = Product(organization=self.org, name='Widget', sku='W1', unit='PCS', category=category).save()
        warehouse = Warehouse(organization=self.org, name='Main godown', code='MAIN').save()
        self.order = SalesOrder(organization=self.org, so_number='SO-77', customer=self.customer, warehouse=warehouse, status='FULFILLED',
                                order_date=datetime(2026, 11, 10), created_by=self.user,
                                items=[SalesOrderItem(product=product, quantity=1, fulfilled_quantity=1, unit_price=100)]).save()
        for number, customer, order in [('INV-1', self.customer, self.order), ('INV-2', self.plain, None)]:
            Invoice(organization=self.org, invoice_number=number, customer=customer, sales_order=order, created_by=self.user,
                    invoice_date=datetime(2026, 11, 11), billing_name=customer.name, total_amount=100, balance_due=100,
                    items=[InvoiceItem(product=product, item_name='Widget', unit='PCS', quantity=1, unit_price=100, line_subtotal=100, line_total=100)]).save()

    def get(self, view, term):
        request = RequestFactory().get('/', {'search': term})
        request.api_user = self.user; request.api_organization = self.org; request.user = self.user
        response = view.__wrapped__.__wrapped__(request)
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)['data']

    def test_invoice_search_by_customer_name_and_order_number(self):
        self.assertEqual([i['invoice_number'] for i in self.get(invoice_collection_api, 'sharma')['invoices']], ['INV-1'])
        self.assertEqual([i['invoice_number'] for i in self.get(invoice_collection_api, 'SO-77')['invoices']], ['INV-1'])
        self.assertEqual([i['invoice_number'] for i in self.get(invoice_collection_api, 'INV-2')['invoices']], ['INV-2'])

    def test_sales_order_search_by_customer_and_warehouse(self):
        self.assertEqual([o['so_number'] for o in self.get(sales_order_collection_api, 'Sharma')['sales_orders']], ['SO-77'])
        self.assertEqual([o['so_number'] for o in self.get(sales_order_collection_api, 'godown')['sales_orders']], ['SO-77'])
        self.assertEqual(self.get(sales_order_collection_api, 'Patil')['sales_orders'], [])

    def test_matches_in_another_organization_do_not_leak(self):
        self.assertEqual(self.get(invoice_collection_api, 'Elsewhere')['invoices'], [])
