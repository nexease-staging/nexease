from types import SimpleNamespace
from django.test import SimpleTestCase
from apps.business.ewaybill import build, response_fields, transport

class EWayBillTests(SimpleTestCase):
    def test_challan_uses_chl_and_job_work_without_creating_invoice(self):
        source={'seller_gstin':'27AAACQ3770E1Z0','customer_gstin':'','seller_name':'Seller','customer_name':'Buyer',
                'seller_address':'Pune Road','address':'Mumbai Road','pos':'27','reason':'job_work','number':'DC-2026-000001',
                'date':'2026-11-05','items':[dict(qty='2',value='100',rate='18',unit='Piece',name='Goods',hsn='220110',
                                                cgst='9',sgst='9',igst='0')]}
        body=build(source,'challan',{'gstin':source['seller_gstin']},{'city':'Pune','pincode':'411001'},
                   dict(mode='1',distance='150',vehicle='MH-12-AB-1234',destination_city='Mumbai',destination_pin='400001'))
        self.assertEqual((body['docType'],body['subSupplyType'],body['toGstin'],body['totInvValue']),('CHL','4','URP',118))
        self.assertEqual((body['vehicleNo'],body['itemList'][0]['qtyUnit']),('MH12AB1234','PCS'))
        source['items'][0]['qty']='0'
        with self.assertRaisesRegex(ValueError,'final positive quantities'):
            build(source,'challan',{'gstin':source['seller_gstin']},{'city':'Pune','pincode':'411001'},
                  dict(mode='1',distance='150',vehicle='MH12AB1234',destination_city='Mumbai',destination_pin='400001'))

    def test_missing_transport_document_and_missing_government_number_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'transport document'):
            transport({'mode':'2','distance':'100'})
        with self.assertRaisesRegex(ValueError,'No valid'):
            response_fields({'code':200})
        self.assertEqual(response_fields({'EwbNo':123456789012,'EwbValidTill':'2026-11-10'})['number'],'123456789012')

    def test_service_invoice_cannot_generate_standalone_eway_bill(self):
        with self.assertRaisesRegex(ValueError,'goods-only'):
            build(SimpleNamespace(items=[SimpleNamespace(item_type='service')]),'invoice',{}, {},
                  {'mode':'1','distance':'100','vehicle':'MH12AB1234'})
