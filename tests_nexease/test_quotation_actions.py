import bootstrap
import json
import unittest
from uuid import uuid4
from unittest.mock import patch
from django.test import RequestFactory
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.business.quotation_actions import quotation_pdf
from apps.business.quotations import quotations
from apps.business.direct_entry import direct_invoice
from apps.business.models import BusinessRecord
from apps.sales.api.v1.views import sales_order_collection_api
from apps.sales.models import Invoice, Customer, SalesOrder
from apps.inventory.models import Warehouse
from apps.products.models import Category, Product


class QuotationActions(unittest.TestCase):
    def setUp(self):
        self.org = Organization(name="Quote tests",email="quote@example.com").save()
        self.user = User(organization=self.org,email=uuid4().hex+"@example.com",password="test",
                         first_name="Test",last_name="User").save()
        permission = patch("apps.authorization.services.AuthorizationService.has_permission",return_value=True)
        permission.start()
        self.addCleanup(permission.stop)
        self.sale = {"customer":{"name":"Buyer"},"invoice_date":"2026-11-17","items":[
            {"name":"Widget","quantity":"2","unit_price":"100","discount":"10","tax_rate":"18"}]}
        response = quotations.__wrapped__(self.request("POST","/",self.sale))
        self.key = json.loads(response.content)["data"]["number"]

    def request(self,method,path,body=None):
        factory = RequestFactory()
        req = factory.get(path) if method=="GET" else factory.post(path,data=json.dumps(body),content_type="application/json")
        req.api_user=self.user
        req.api_organization=self.org
        return req

    def test_pdf_and_tenant_boundary(self):
        req = self.request("GET","/")
        pdf = quotation_pdf.__wrapped__(req,self.key)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        req.api_organization=Organization(name="Other",email="other@example.com").save()
        self.assertEqual(quotation_pdf.__wrapped__(req,self.key).status_code,404)

    def test_invoice_link_and_repeat(self):
        path="/?quotation="+self.key
        response=direct_invoice.__wrapped__(self.request("POST",path,self.sale))
        self.assertEqual(response.status_code,200,response.content)
        quote=BusinessRecord.objects.get(organization=self.org,kind="quotation",key=self.key)
        invoice=Invoice.objects.get(organization=self.org)
        self.assertEqual(quote.data["conversion"]["id"],str(invoice.id))
        self.assertEqual(direct_invoice.__wrapped__(self.request("POST",path,self.sale)).status_code,409)
        self.assertEqual(Invoice.objects(organization=self.org).count(),1)

    def test_order_link(self):
        customer=Customer(organization=self.org,name="Buyer",code="B").save()
        warehouse=Warehouse(organization=self.org,name="Main",code="W").save()
        category=Category(organization=self.org,name="Parts").save()
        product=Product(organization=self.org,name="Widget",sku="P",category=category,unit="PCS").save()
        body={"order_date":"2026-11-17","customer_id":str(customer.id),"warehouse_id":str(warehouse.id),
              "items":[{"product_id":str(product.id),"quantity":"2","unit_price":"100","discount":"10","tax_rate":"18"}]}
        req=self.request("POST","/?quotation="+self.key,body)
        response=sales_order_collection_api.__wrapped__.__wrapped__(req)
        self.assertEqual(response.status_code,201,response.content)
        order=SalesOrder.objects.get(organization=self.org)
        self.assertEqual(str(order.total_amount),"224.20")
        quote=BusinessRecord.objects.get(organization=self.org,kind="quotation",key=self.key)
        self.assertEqual(quote.data["conversion"]["id"],str(order.id))
        invoice_response = direct_invoice.__wrapped__(self.request("POST","/", self.sale))
        self.assertEqual(invoice_response.status_code,200,invoice_response.content)
        invoice=Invoice.objects.get(organization=self.org)
        invoice.update(set__sales_order=order)
        result=quotations.__wrapped__(self.request("GET","/"))
        row=json.loads(result.content)["data"]["rows"][0]
        self.assertEqual(row["linked_invoice"]["id"],str(invoice.id))
