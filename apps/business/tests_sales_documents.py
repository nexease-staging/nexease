import hashlib
import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from mongoengine.connection import get_db

from apps.business import einvoice
from apps.business.delivery_challan import challans, render_pdf
from apps.organizations.models import Organization
from apps.saas.models import Membership


class SalesDocumentTests(SimpleTestCase):
    def setUp(self):
        self.org=Organization(name='IRP test',email='irp@example.test').save()
        self.other=Organization(name='Other',email='other@example.test').save()
        self.factory=RequestFactory()
        self.addCleanup(self.org.delete)
        self.addCleanup(self.other.delete)
        self.addCleanup(lambda:Membership.objects(organization_id=str(self.org.id)).delete())

    def test_einvoice_access_requires_pro_even_when_general_enforcement_off(self):
        request=self.factory.get('/api/v1/business/e-invoices/')
        org=self.org
        with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',return_value={'user':SimpleNamespace(organization=org),'organization':org}), patch('apps.business.einvoice.permitted',return_value=True):
            m=Membership(organization_id=str(org.id),plan='plus',status='active',
                         start=datetime.utcnow()-timedelta(days=1),end=datetime.utcnow()+timedelta(days=1)).save()
            self.assertEqual(einvoice.einvoices(request).status_code,403)
            m.update(set__plan='pro')
            self.assertEqual(einvoice.einvoices(request).status_code,200)
            m.update(set__suspended=True)
            self.assertEqual(einvoice.einvoices(request).status_code,403)

    def test_payload_preserves_tax_split_and_rejects_mismatched_provider_irn(self):
        item=SimpleNamespace(item_type='goods',hsn_code='220110',item_name='Bottled water',unit='Piece',
                             quantity='2',unit_price='50',discount='0',line_subtotal='100',
                             line_tax='18',tax_rate='18',line_total='118')
        inv=SimpleNamespace(status='ISSUED',billing_details={'supplier_gstin':'27AAACQ3770E1Z0','supplier_state':'27',
             'place_of_supply':'27','tax_reviewed':True,'supply_type':'taxable'},customer_gstin='27AAACQ3770E2Z0',
             billing_name='Buyer India',billing_address='12 Main Road',billing_city='Pune',billing_pincode='411001',
             invoice_number='INV-1',invoice_date=datetime(2026,11,5),items=[item],discount_amount='0',
             subtotal='100',tax_amount='18',total_amount='118')
        reg={'registration':'regular','gstin':'27AAACQ3770E1Z0','legal_name':'Seller India'}
        doc=einvoice.build_document(inv,reg,{'address':'10 Main Road','city':'Pune','pincode':'411001'})
        self.assertEqual(doc['ValDtls'],dict(AssVal=100,CgstVal=9,SgstVal=9,IgstVal=0,TotInvVal=118))
        self.assertEqual(doc['ItemList'][0]['Unit'],'PCS')
        irn=hashlib.sha256(b'27AAACQ3770E1Z02026-27INVINV-1').hexdigest()
        reply={'code':200,'data':{'status_cd':'1','data':{'Irn':irn,'SignedQRCode':'signed','AckNo':123}}}
        self.assertEqual(einvoice.saved_result(reply,doc)['ack_no'],'123')
        reply['data']['data']['Irn']='0'*64
        with self.assertRaisesRegex(ValueError,'did not match'):
            einvoice.saved_result(reply,doc)
        inv.total_amount='119'
        with self.assertRaisesRegex(ValueError,'totals do not reconcile'):
            einvoice.build_document(inv,reg,{'address':'10 Main Road','city':'Pune','pincode':'411001'})

    def test_challan_pdf_and_cross_tenant_document_block(self):
        coll=get_db().nexease_delivery_challans
        self.addCleanup(lambda:coll.delete_one({'_id':'challan-test'}))
        doc=dict(_id='challan-test',organization_id=str(self.other.id),number='DC-2026-000001',
                 status='issued',date='2026-11-05',reason='job_work',seller_name='Seller',seller_address='Pune',
                 seller_gstin='',customer_name='Buyer',address='Mumbai',customer_gstin='',pos='27',
                 transport='MH-12',invoice_number='',notes='',items=[dict(name='Goods',hsn='2201',qty='1',unit='PCS',
                    value='100',rate='0',cgst='0',sgst='0',igst='0')])
        coll.insert_one(doc)
        self.assertTrue(render_pdf(doc).startswith(b'%PDF'))
        request=self.factory.get('/api/v1/business/delivery-challans/challan-test/')
        with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',return_value={'user':SimpleNamespace(organization=self.org),'organization':self.org}), patch('apps.business.delivery_challan.permitted',return_value=True):
            self.assertEqual(challans(request,doc_id='challan-test').status_code,404)

    def test_annual_quota_resets_on_monthly_anniversary(self):
        from apps.saas.entitlements import usage_period
        m=SimpleNamespace(cycle='yearly',start=datetime(2026,1,31,12))
        with patch('apps.saas.entitlements.datetime') as clock:
            clock.utcnow.return_value=datetime(2026,3,2)
            self.assertEqual(usage_period(m),'2026-02-28T12:00:00')
            clock.utcnow.return_value=datetime(2026,3,31,12)
            self.assertEqual(usage_period(m),'2026-03-31T12:00:00')

    def test_annual_checkout_publishes_the_exact_yearly_amount(self):
        from apps.saas import gateway
        from apps.saas.models import Plan
        plan=Plan(code='pro',name='NexEase Pro',price_paise=129900,published=True,
                  razorpay_plan_id='monthly-existing',gateway_mode='test')
        with patch.object(gateway,'mode',return_value='test'), patch.object(gateway,'api',return_value={'id':'annual-new'}) as api, patch.object(Plan,'save'):
            gateway.publish(plan,'yearly')
        sent=api.call_args.args[1]
        self.assertEqual((sent['period'],sent['interval'],sent['item']['amount']),('yearly',1,1299900))
        self.assertEqual((plan.razorpay_plan_id,plan.annual_razorpay_plan_id),('monthly-existing','annual-new'))

    def test_uncertain_submission_is_not_sent_twice(self):
        from bson import ObjectId
        from apps.sales.models import Invoice
        invoice_id=ObjectId()
        collection=Invoice._get_collection()
        collection.insert_one({'_id':invoice_id,'organization':self.org.id,'invoice_number':'INV-2',
                               'invoice_date':datetime(2026,11,5),'status':'ISSUED','updated_at':datetime.utcnow(),
                               'billing_details':{'supplier_gstin':'27AAACQ3770E1Z0'}})
        self.addCleanup(lambda:collection.delete_one({'_id':invoice_id}))
        Membership(organization_id=str(self.org.id),plan='pro',status='active',
                   start=datetime.utcnow()-timedelta(days=1),end=datetime.utcnow()+timedelta(days=1)).save()
        def submit():
            req=self.factory.post('/api/v1/business/e-invoices/',
                                  data=json.dumps({'id':str(invoice_id),'action':'generate','confirm':True}),
                                  content_type='application/json')
            return einvoice.einvoices(req)
        context={'user':SimpleNamespace(organization=self.org),'organization':self.org}
        with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',return_value=context), \
             patch('apps.business.einvoice.permitted',return_value=True), \
             patch('apps.business.einvoice.session',return_value=('https://example.test',{},{})), \
             patch('apps.business.einvoice.build_document',return_value={'DocDtls':{'No':'INV-2'}}), \
             patch('apps.business.einvoice.call',side_effect=ValueError('Timed out')) as call:
            self.assertEqual(submit().status_code,400)
            self.assertEqual(collection.find_one({'_id':invoice_id})['einvoice']['status'],'pending')
            self.assertEqual(submit().status_code,400)
            call.assert_called_once()
