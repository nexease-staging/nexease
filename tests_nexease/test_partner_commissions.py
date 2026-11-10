import bootstrap
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from mongoengine.connection import get_db
from apps.saas import commissions, alerts
from apps.organizations.models import Organization
from apps.saas.models import Checkout


class CommissionTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name='Referral customer', email='customer@example.com').save()
        commissions.approve_partner('partner-1', 'Partner One', 'partner@example.com', 'test')
        commissions.attach_referral(self.org.id, 'partner-1', 'test')

    def payment(self, key, paid_at, amount=74900, refund=0, mode='live', org=None):
        get_db().saas_payments.update_one({'_id': key}, {'$set': {
            'organization_id': str(org or self.org.id), 'subscription_id': 'subscription-1',
            'mode': mode, 'paid_at': paid_at, 'amount_paise': amount, 'refunded_paise': refund,
        }}, upsert=True)
        get_db().saas_payment_tax.update_one({'_id':mode+':'+key}, {'$set':{'gross_paise':amount,'refunded_paise':refund,'gst_paise':0,'refund_gst_paise':0}}, upsert=True)

    def test_first_and_renewal_replay_once(self):
        self.payment('first', 100)
        self.payment('renewal', 200)
        for _ in range(3): commissions.rebuild(self.org.id, 'live')
        rows = list(get_db().saas_commissions.find().sort('paid_at', 1))
        self.assertEqual([(r['percent'], r['amount_paise']) for r in rows], [(20,14980),(10,7490)])
        self.assertTrue(all(r['status']=='review_required' for r in rows))

    def test_late_first_payment_reorders_without_duplicates(self):
        self.payment('renewal', 200)
        commissions.rebuild(self.org.id, 'live')
        self.payment('first', 100)
        commissions.rebuild(self.org.id, 'live')
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'live:renewal'})['percent'], 10)
        self.assertEqual(get_db().saas_commissions.count_documents({}), 2)

    def test_partial_and_full_refund_recalculate(self):
        self.payment('first', 100, refund=10000)
        commissions.rebuild(self.org.id, 'live')
        self.assertEqual(get_db().saas_commissions.find_one()['amount_paise'], 12980)
        self.payment('first', 100, refund=74900)
        self.payment('renewal', 200)
        commissions.rebuild(self.org.id, 'live')
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'live:first'})['amount_paise'], 0)
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'live:renewal'})['percent'], 10)

    def test_paise_round_half_up_and_validation(self):
        self.assertEqual(commissions.commission_paise(5,0,10),1)
        self.assertEqual(commissions.commission_paise(4,0,10),0)
        for args in [(1.2,0,20),(10,11,20),(-1,0,20),(10,0,50)]:
            with self.assertRaises(ValueError): commissions.commission_paise(*args)

    def test_mode_and_tenant_isolation(self):
        self.payment('test-first',100,mode='test')
        self.payment('live-first',200)
        self.payment('other',50,org='other-organization')
        commissions.rebuild(self.org.id,'live')
        rows=list(get_db().saas_commissions.find())
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['percent'],20)
        self.assertEqual(rows[0]['payment_id'],'live-first')

    def test_referral_immutable_and_requires_approved_partner(self):
        commissions.attach_referral(self.org.id,'partner-1','test')
        commissions.approve_partner('partner-2','Two','two@example.com','test')
        with self.assertRaises(ValueError): commissions.attach_referral(self.org.id,'partner-2','test')
        org=Organization(name='Other',email='other@example.com').save()
        with self.assertRaises(ValueError): commissions.attach_referral(org.id,'missing','test')
        Checkout(subscription_id='existing',organization_id=str(org.id),plan='basic',price_paise=74900,mode='live').save()
        with self.assertRaises(ValueError): commissions.attach_referral(org.id,'partner-1','test')

    def test_missing_timestamp_held_for_review(self):
        self.payment('missing-date',None)
        with self.assertRaises(ValueError): commissions.rebuild(self.org.id,'live')
        self.assertEqual(get_db().saas_commissions.count_documents({}),0)

    def test_approved_default_reminder_offsets(self):
        from apps.accounts.models import User
        from apps.authorization.models import Role
        from apps.saas.models import Membership
        role=Role(organization=self.org,name='Admin',is_system=True).save()
        User(organization=self.org,role=role,email='admin@example.com',password='test',first_name='A',last_name='B').save()
        end=datetime(2026,12,1,18,30)
        Membership(organization_id=str(self.org.id),status='active',plan='plus',start=end-timedelta(days=30),end=end).save()
        with patch.dict(os.environ):
            os.environ.pop('SUBSCRIPTION_ALERT_DAYS',None)
            for offset in [7,3,1,0]: alerts.schedule(now=end-timedelta(days=offset))
        rows=list(get_db().subscription_alerts.find())
        self.assertEqual(len(rows),6)
        self.assertEqual({r['kind'] for r in rows},{'renewal:7','renewal:3','renewal:1'})

    def test_gateway_verified_history_and_refund_do_not_reactivate_old_period(self):
        from apps.saas import gateway
        from apps.saas.models import Membership
        Checkout(subscription_id='subscription-1',organization_id=str(self.org.id),plan='basic',price_paise=74900,mode='test').save()
        current_start=1794000000
        end=current_start+2592000
        def api(path):
            if path.startswith('subscriptions/'):
                return {'id':'subscription-1','status':'active','current_start':current_start,'current_end':end}
            if path.startswith('invoices?'):
                return {'items':[
                    {'id':'new','subscription_id':'subscription-1','status':'paid','currency':'INR','amount_paid':74900,'payment_id':'new-pay','billing_start':current_start,'billing_end':end,'paid_at':current_start},
                    {'id':'old','subscription_id':'subscription-1','status':'paid','currency':'INR','amount_paid':74900,'payment_id':'old-pay','billing_start':current_start-2592000,'billing_end':current_start,'paid_at':current_start-2592000},
                ]}
            if path=='payments/new-pay': return {'status':'captured','currency':'INR','amount':74900,'amount_refunded':0}
            if path=='payments/old-pay': return {'status':'refunded','currency':'INR','amount':74900,'amount_refunded':74900}
            raise AssertionError(path)
        with patch.dict(os.environ,RAZORPAY_KEY_ID='rzp_test_fake'), patch.object(gateway,'api',side_effect=api):
            gateway.reconcile('subscription-1')
            gateway.reconcile('subscription-1')
        self.assertEqual(Membership.objects.first().status,'active')
        self.assertEqual(Membership.objects.first().start,datetime.utcfromtimestamp(current_start))
        self.assertIsNone(get_db().saas_commissions.find_one({'_id':'test:old-pay'})['amount_paise'])
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'test:new-pay'})['percent'],10)
        self.assertEqual(get_db().saas_commissions.count_documents({}),2)

    def test_gst_excluded_first_and_renewal(self):
        self.payment('first',100,amount=118000)
        self.payment('renewal',200,amount=118000)
        for key in ('first','renewal'):
            commissions.record_tax(key,'live',18000,0,'INV-'+key,'test','Verified invoice')
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'live:first'})['amount_paise'],20000)
        self.assertEqual(get_db().saas_commissions.find_one({'_id':'live:renewal'})['amount_paise'],10000)

    def test_missing_or_stale_gst_holds_previous_amount(self):
        self.payment('first',100,amount=118000)
        get_db().saas_payment_tax.delete_many({})
        commissions.rebuild(self.org.id,'live')
        self.assertIsNone(get_db().saas_commissions.find_one()['amount_paise'])
        commissions.record_tax('first','live',18000,0,'INV-1','test','Verified invoice')
        get_db().saas_payments.update_one({'_id':'first'},{'$set':{'refunded_paise':59000}})
        commissions.rebuild(self.org.id,'live')
        self.assertIsNone(get_db().saas_commissions.find_one()['amount_paise'])
        commissions.record_tax('first','live',18000,9000,'CN-1','test','Verified refund')
        self.assertEqual(get_db().saas_commissions.find_one()['amount_paise'],10000)

    def test_invalid_tax_and_full_refund_validation(self):
        for values in [(118000,118000,18000,0),(118000,59000,18000,19000),(118000,0,18000.0,0)]:
            with self.assertRaises(ValueError): commissions.validate_tax(*values)
        commissions.validate_tax(118000,118000,18000,18000)
