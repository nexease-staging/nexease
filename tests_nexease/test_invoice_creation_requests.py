import bootstrap
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from uuid import uuid4
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.sales.models import Invoice, Customer, SalesOrder, SalesOrderItem
from apps.products.models import Product, Category
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.business.direct_entry import direct_invoice


class InvoiceCreationRequestTests(unittest.TestCase):
    def setUp(self):
        self.org = Organization(name='Creation test',email='test@example.com').save()
        self.user = User(organization=self.org,email=uuid4().hex+'@example.com',password='test',first_name='Test',last_name='User').save()
        self.permission = patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True)
        self.permission.start();self.addCleanup(self.permission.stop)
        self.body = {'invoice_date':'2026-11-10','customer':{'name':'New customer'},
                     'items':[{'name':'Widget','quantity':'2','unit_price':'100','unit':'PCS','tax_rate':'0'}]}

    def call(self, key='invoice-request-test-0001', body=None, user=None, org=None, view=None, numbering=None):
        headers = {'HTTP_X_NEXEASE_REQUEST_KEY':key}
        if numbering is not None:headers['HTTP_X_NEXEASE_NUMBERING']=json.dumps(numbering)
        req = RequestFactory().post('/api/v1/business/direct-invoices/',data=json.dumps(body if body is not None else self.body),content_type='application/json',**headers)
        req.api_user=user or self.user;req.api_organization=org or self.org
        return (view or direct_invoice.__wrapped__)(req)

    def test_lost_response_retry_returns_original_and_moves_stock_once(self):
        first=self.call();self.assertEqual(first.status_code,200,first.content)
        replay=self.call();self.assertEqual(replay.status_code,200,replay.content)
        self.assertEqual(json.loads(replay.content),json.loads(first.content))
        self.assertEqual(replay['X-NexEase-Replayed'],'true')
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)
        self.assertEqual(Customer.objects(organization=self.org).count(),1)
        self.assertEqual(Product.objects(organization=self.org).count(),1)
        self.assertEqual(StockMovement.objects(organization=self.org).count(),1)
        self.assertEqual(Inventory.objects(organization=self.org).get().quantity,Decimal('-2'))

    def test_validation_failure_can_be_corrected_without_a_hold(self):
        response=self.call(body={'invoice_date':'2026-11-10'})
        self.assertEqual(response.status_code,400)
        self.assertEqual(get_db().invoice_creation_requests.count_documents({'organization_id':str(self.org.id)}),0)
        self.assertEqual(self.call().status_code,200)

    def test_changed_body_or_numbering_cannot_reuse_key(self):
        self.assertEqual(self.call().status_code,200)
        self.assertEqual(self.call(body={**self.body,'notes':'Changed'}).status_code,409)
        self.assertEqual(self.call(numbering={'kind':'Invoice','mode':'manual','number':'DIFFERENT'}).status_code,409)
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)

    def test_cross_user_and_revoked_permission_cannot_replay(self):
        self.assertEqual(self.call().status_code,200)
        other=User(organization=self.org,email=uuid4().hex+'@example.com',password='test',first_name='Other',last_name='User').save()
        self.assertEqual(self.call(user=other).status_code,409)
        org=Organization(name='Other',email='other@example.com').save()
        self.assertEqual(self.call(org=org).status_code,403)
        with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=False):
            self.assertEqual(self.call().status_code,403)

    def test_after_stock_failure_holds_both_original_and_new_keys(self):
        with patch('apps.business.direct_entry.NotificationService.create_notification',side_effect=RuntimeError('injected after stock')):
            response=self.call()
        self.assertEqual(response.status_code,409,response.content)
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)
        self.assertEqual(Inventory.objects(organization=self.org).get().quantity,Decimal('-2'))
        for key in ('invoice-request-test-0001','invoice-request-test-0002'):
            self.assertEqual(self.call(key=key).status_code,409)
        receipt=get_db().invoice_creation_requests.find_one({'organization_id':str(self.org.id)})
        self.assertEqual(receipt['status'],'review_required')
        self.assertEqual(receipt['invoice_id'],str(Invoice.objects(organization=self.org).get().id))
        self.assertEqual(StockMovement.objects(organization=self.org).count(),1)

    def test_stock_failure_does_not_delete_invoice_evidence(self):
        with patch('apps.business.direct_entry.move',side_effect=ValueError('injected stock failure')):
            response=self.call()
        self.assertEqual(response.status_code,409)
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)
        self.assertEqual(self.call().status_code,409)
        from apps.sales.services.invoice_service import InvoiceService
        with self.assertRaisesRegex(ValueError,'needs review'):
            InvoiceService.issue_invoice(user=self.user,organization=self.org,
                invoice_id=str(Invoice.objects(organization=self.org).get().id))
        self.assertEqual(Invoice.objects(organization=self.org).get().status,'DRAFT')

    def test_simultaneous_request_then_successful_replay(self):
        entered,release=Event(),Event()
        def pause(**kwargs):
            entered.set()
            if not release.wait(5):raise RuntimeError('Test synchronization timeout')
        with ThreadPoolExecutor(max_workers=2) as pool,patch('apps.business.direct_entry.NotificationService.create_notification',side_effect=pause):
            first=pool.submit(self.call)
            self.assertTrue(entered.wait(5))
            try:self.assertEqual(self.call().status_code,409)
            finally:release.set()
            self.assertEqual(first.result(timeout=5).status_code,200)
        self.assertEqual(self.call().status_code,200)
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)
        self.assertEqual(StockMovement.objects(organization=self.org).count(),1)

    def test_sales_order_retry_returns_existing_invoice(self):
        from apps.sales.api.v1.views import invoice_collection_api
        customer=Customer(organization=self.org,name='Customer',code='C1').save()
        category=Category(organization=self.org,name='Goods').save()
        product=Product(organization=self.org,name='Widget',sku='W1',unit='PCS',category=category).save()
        warehouse=Warehouse(organization=self.org,name='Main',code='M').save()
        order=SalesOrder(organization=self.org,so_number='SO1',customer=customer,warehouse=warehouse,status='FULFILLED',
            order_date=datetime(2026,11,10),created_by=self.user,
            items=[SalesOrderItem(product=product,quantity=2,fulfilled_quantity=2,unit_price=100)]).save()
        body={'sales_order_id':str(order.id),'invoice_date':'2026-11-10'}
        # Bypass auth/rate-limit infrastructure; retain the creation receipt and actual API/service paths.
        view=invoice_collection_api.__wrapped__.__wrapped__
        first=self.call(body=body,view=view)
        self.assertEqual(first.status_code,201,first.content)
        replay=self.call(body=body,view=view)
        self.assertEqual(replay.status_code,201,replay.content)
        self.assertEqual(json.loads(first.content),json.loads(replay.content))
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)
