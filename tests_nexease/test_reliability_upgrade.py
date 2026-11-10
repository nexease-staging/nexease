import bootstrap
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import Mock
from mongoengine.connection import get_db
from apps.saas import alerts
from apps.saas.provider_guard import guarded_call, meter, month_key, ProviderGuardError
from apps.saas.models import Membership
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.authorization.models import Role
from apps.core.notification_models import Notification

class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org=Organization(name='Test', email='org@example.com').save()
        role=Role(organization=self.org,name='Admin',is_system=True).save()
        self.user=User(organization=self.org,role=role,email='admin@example.com',password='test',first_name='A',last_name='B').save()
        self.start=datetime(2026,10,1)
        self.end=datetime(2026,11,10,18,30) # Nov 11 at 00:00 IST
        Membership(organization_id=str(self.org.id),status='active',plan='plus',start=self.start,end=self.end,subscription_id='sub_test').save()

    def drain(self, now, sender):
        while alerts.deliver_one(now=now,send_email=sender):
            pass

    def test_each_offset_once_each_channel_with_restart_and_concurrent_scans(self):
        sender=Mock()
        for offset in [7,3,1,0]:
            now=self.end-timedelta(days=offset)
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda _: alerts.schedule(now=now,offsets=[7,3,1,0]),range(8)))
            self.drain(now,sender)
            # Simulate restarted workers rescheduling the same date.
            alerts.schedule(now=now,offsets=[7,3,1,0]);self.drain(now,sender)
        self.assertEqual(sender.call_count,4)
        self.assertEqual(Notification.objects.count(),4)
        self.assertEqual(get_db().subscription_alerts.count_documents({'status':'sent'}),8)
        self.assertEqual(len({row['_id'] for row in get_db().subscription_alerts.find()}),8)

    def test_ist_boundary_not_server_date(self):
        alerts.schedule(now=self.end-timedelta(seconds=1),offsets=[0])
        self.assertEqual(get_db().subscription_alerts.count_documents({}),0)
        alerts.schedule(now=self.end,offsets=[0])
        self.assertEqual(get_db().subscription_alerts.count_documents({}),2)

    def test_ambiguous_email_not_resent(self):
        alerts.schedule(now=self.end,offsets=[0]);sender=Mock(side_effect=TimeoutError())
        self.drain(self.end,sender);self.drain(self.end+timedelta(days=1),sender)
        self.assertEqual(sender.call_count,1)
        self.assertEqual(get_db().subscription_alerts.count_documents({'status':'review_required'}),1)
        self.assertEqual(Notification.objects.count(),1)

    def test_concurrent_delivery_claims(self):
        alerts.schedule(now=self.end,offsets=[0]);sender=Mock()
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: alerts.deliver_one(now=self.end,send_email=sender),range(8)))
        self.assertEqual(sender.call_count,1)
        self.assertEqual(Notification.objects.count(),1)

    def test_new_cycle_does_not_reuse_old_key(self):
        alerts.schedule(now=self.end,offsets=[0]);self.drain(self.end,Mock())
        m=Membership.objects.first();m.start=self.end;m.end=self.end+timedelta(days=30);m.save()
        alerts.schedule(now=m.end,offsets=[0]);self.drain(m.end,Mock())
        self.assertEqual(Notification.objects.count(),2)

    def call(self, identity='GST-A', org=None, now=None, limit=1, fn=None):
        return guarded_call(org_id=org or self.org.id,feature='gst',identity=identity,limit=limit,call=fn or (lambda:{'name':'Test'}),now=now or self.start)

    def test_cache_quota_expiry_and_tenant_isolation(self):
        fn=Mock(return_value={'name':'Test'})
        self.call(fn=fn);self.call(fn=fn)
        self.assertEqual(fn.call_count,1)
        with self.assertRaises(ProviderGuardError):self.call(identity='GST-B',fn=fn)
        self.call(org='different-tenant',fn=fn)
        self.assertEqual(fn.call_count,2)
        self.call(now=self.start+timedelta(days=31),fn=fn)
        self.assertEqual(fn.call_count,3)

    def test_no_provider_call_when_zero_limit(self):
        fn=Mock()
        with self.assertRaises(ProviderGuardError):self.call(limit=0,fn=fn)
        fn.assert_not_called()

    def test_inflight_duplicate_does_not_call_provider(self):
        def provider():
            with self.assertRaises(ProviderGuardError):self.call(limit=5)
            return {'name':'Test'}
        self.call(fn=provider,limit=5)
        self.assertEqual(meter(self.org.id,'gst',5,self.start)['used'],1)

    def test_failed_paid_attempt_keeps_quota(self):
        with self.assertRaises(TimeoutError):self.call(fn=Mock(side_effect=TimeoutError()))
        with self.assertRaises(ProviderGuardError):self.call()

    def test_ist_month_boundary(self):
        self.assertEqual(month_key(datetime(2026,3,31,18,29)), '2026-03')
        self.assertEqual(month_key(datetime(2026,3,31,18,30)), '2026-04')

    def test_welcome_unique_per_user_each_channel(self):
        sender=Mock()
        for _ in range(3):
            alerts.enqueue(organization=self.org.id,recipient=self.user.id,cycle='signup:'+str(self.user.id),
                due_date=self.start.date(),kind='welcome',title='Welcome',message='Welcome',now=self.start)
        self.drain(self.start,sender)
        self.assertEqual(sender.call_count,1)
        self.assertEqual(Notification.objects.count(),1)
        self.assertEqual(Notification.objects.first().action_url,'/dashboard')

    def test_requested_plan_caps_and_free_features(self):
        from apps.saas.entitlements import DEFAULTS
        self.assertEqual([(DEFAULTS[k][2]['users'],DEFAULTS[k][2]['invoices']) for k in ('free','basic','plus','pro')],[(1,30),(3,300),(10,1000),(25,3000)])
        self.assertEqual(DEFAULTS['pro'][2]['employees'],50)
        self.assertEqual(DEFAULTS['pro'][2]['einvoices'],100)
        self.assertEqual(DEFAULTS['pro'][2]['scan_pages'],100)
        self.assertEqual(DEFAULTS['free'][3],[])

    def test_einvoice_limit_reserves_once_and_counts_pending(self):
        from apps.saas.provider_guard import reserve_einvoice
        m=Membership.objects.first();m.limits={'einvoices':1};m.save()
        reserve_einvoice(self.org,'invoice-one','test',self.start)
        reserve_einvoice(self.org,'invoice-one','test',self.start)
        with self.assertRaises(ProviderGuardError):reserve_einvoice(self.org,'invoice-two','test',self.start)
        self.assertEqual(get_db().saas_einvoice_usage.count_documents({}),1)

    def test_renewal_before_delivery_cancels_old_cycle(self):
        alerts.schedule(now=self.end, offsets=[0])
        Membership.objects(organization_id=str(self.org.id)).update(set__end=self.end+timedelta(days=30))
        sender = Mock()
        self.drain(self.end, sender)
        sender.assert_not_called()
        self.assertEqual(get_db().subscription_alerts.count_documents({'status':'cancelled'}), 2)
