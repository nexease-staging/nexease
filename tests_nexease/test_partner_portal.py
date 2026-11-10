import bootstrap
import json
import time
import unittest
from datetime import datetime
from unittest.mock import patch
from django.test import RequestFactory, Client
from django.contrib.auth.hashers import make_password
from mongoengine.connection import get_db
from apps.saas import partners
from apps.saas.models import PlatformOwner


class Session(dict):
    def cycle_key(self):
        self.rotated = True


class PartnerPortalTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names(): get_db().drop_collection(name)
        self.factory=RequestFactory()
        self.session=Session()
        self.rate=patch('apps.saas.partners.rate');self.rate.start();self.addCleanup(self.rate.stop)

    def request(self, data=None, session=None, query=''):
        r=self.factory.post('/api/v1/saas/partners/session/',json.dumps(data),content_type='application/json') if data is not None else self.factory.get('/api/v1/saas/partners/dashboard/'+query)
        r.session=self.session if session is None else session
        return r

    def register(self, email='partner@example.com'):
        return partners.session(self.request({'action':'register','email':email,'name':'Partner','password':'PartnerSecure#2937'}))

    def login(self,email='partner@example.com'):
        return partners.session(self.request({'action':'login','email':email,'password':'PartnerSecure#2937'}))

    def test_registration_pending_hashed_and_idempotent(self):
        self.assertEqual(self.register().status_code,200)
        self.assertEqual(self.register().status_code,200)
        row=get_db().saas_partners.find_one()
        self.assertEqual(row['status'],'pending')
        self.assertNotEqual(row['password'],'PartnerSecure#2937')
        self.assertEqual(get_db().saas_partners.count_documents({}),1)
        self.assertEqual(self.login().status_code,200)
        self.assertTrue(self.session.rotated)
        self.assertEqual(partners.dashboard(self.request()).status_code,403)

    def test_invalid_password_and_login_denied(self):
        self.assertEqual(partners.session(self.request({'action':'register','email':'p@example.com','name':'P','password':'123'})).status_code,400)
        self.assertEqual(self.login().status_code,401)

    def test_isolated_live_statement_and_session_revocation(self):
        self.register();row=get_db().saas_partners.find_one()
        get_db().saas_partners.update_one({'_id':row['_id']},{'$set':{'status':'approved','referral_code':'ref-1'}})
        self.login()
        for key,pid,mode in [('mine',row['_id'],'live'),('other','other','live'),('sandbox',row['_id'],'test')]:
            get_db().saas_commissions.insert_one({'_id':key,'partner_id':pid,'mode':mode,'amount_paise':20000,'payment_id':key,'paid_at':100,'percent':20,'status':'review_required'})
        data=json.loads(partners.dashboard(self.request(query='?partner_id=other')).content)['data']
        self.assertEqual(data['total'],1)
        self.assertEqual(data['entries'][0]['payment_id'],'mine')
        self.assertEqual(data['totals']['review_paise'],20000)
        self.assertNotIn('password',data['partner'])
        get_db().saas_partners.update_one({'_id':row['_id']},{'$inc':{'generation':1}})
        self.assertEqual(partners.dashboard(self.request()).status_code,403)

    def test_expired_and_logout_session(self):
        self.register();self.login()
        self.session['nexease_partner']['at']=time.time()-9*3600
        self.assertIsNone(partners.partner_for(self.request()))
        self.login();partners.session(self.request({'action':'logout'}))
        self.assertNotIn('nexease_partner',self.session)

    def test_owner_required_and_fresh_auth(self):
        self.register();row=get_db().saas_partners.find_one()
        self.assertEqual(partners.owner_partners(self.request()).status_code,401)
        owner=PlatformOwner(email='owner@example.com',password=make_password('Owner#1234'),totp_secret='unused').save()
        owner_session=Session(nexease_owner={'email':owner.email,'generation':0,'at':time.time()})
        data={'id':row['_id'],'action':'approve','reason':'Identity verified','password':'wrong','code':'123456'}
        self.assertEqual(partners.owner_partners(self.request(data,owner_session)).status_code,400)
        get_db().saas_partners.update_one({'_id':row['_id']},{'$set':{'email_verified':True}})
        data['password']='Owner#1234'
        with patch('apps.saas.partners.verify_totp',return_value=True):
            self.assertEqual(partners.owner_partners(self.request(data,owner_session)).status_code,200)
        row=get_db().saas_partners.find_one()
        self.assertEqual(row['status'],'approved')
        self.assertTrue(row['referral_code'])
        self.assertEqual(row['generation'],1)

    def test_referral_requires_approval_and_blocks_same_email(self):
        self.register();row=get_db().saas_partners.find_one()
        get_db().saas_partners.update_one({'_id':row['_id']},{'$set':{'referral_code':'code'}})
        with self.assertRaises(ValueError):partners.resolve_referral('code','customer@example.com')
        get_db().saas_partners.update_one({'_id':row['_id']},{'$set':{'status':'approved'}})
        self.assertEqual(partners.resolve_referral('code','customer@example.com'),row['_id'])
        with self.assertRaises(ValueError):partners.resolve_referral('code','PARTNER@example.com')

    def test_post_requires_csrf(self):
        r=Client(enforce_csrf_checks=True).post('/api/v1/saas/partners/session/',data=json.dumps({'action':'register'}),content_type='application/json')
        self.assertEqual(r.status_code,403)

    def test_referral_signup_attaches_and_rollback_removes_attribution(self):
        from apps.accounts.organization_signup_service import OrganizationSignupService
        from apps.organizations.models import Organization
        from django.core.management import call_command
        call_command('seed_permissions',verbosity=0)
        self.register();partner=get_db().saas_partners.find_one()
        get_db().saas_partners.update_one({'_id':partner['_id']},{'$set':{'status':'approved','referral_code':'code'}})
        args=dict(organization_name='Customer',organization_email='org@example.com',first_name='Customer',last_name='Admin',user_email='customer@example.com',password='Customer#2937',referral_code='code')
        result=OrganizationSignupService.create_organization_account(**args)
        self.assertEqual(get_db().saas_referrals.find_one({'_id':str(result['organization'].id)})['partner_id'],partner['_id'])
        args.update(organization_email='org2@example.com',user_email='customer2@example.com')
        with patch('apps.saas.entitlements.grant_signup_trial',side_effect=RuntimeError('test rollback')):
            with self.assertRaises(RuntimeError):OrganizationSignupService.create_organization_account(**args)
        self.assertEqual(get_db().saas_referrals.count_documents({}),1)
        self.assertEqual(Organization.objects.count(),1)
