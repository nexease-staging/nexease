import bootstrap
import os
import unittest
from contextlib import ExitStack
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4
from mongoengine.connection import get_db
from apps.core.quotation import deliver_one
from apps.core.management.commands.run_background_worker import Command


class WorkerReleaseTests(unittest.TestCase):
    def quotation(self):
        key=uuid4().hex
        get_db().nexease_quotations.insert_one({'_id':key,'name':'Test','email':'test@example.com','phone':'','business':'Test','service':'Software','message':'Test enquiry','status':'pending','attempts':0,'created_at':datetime.utcnow()})
        self.addCleanup(lambda:get_db().nexease_quotations.delete_one({'_id':key}))
        return key

    def test_ambiguous_smtp_send_is_held_and_never_automatically_repeated(self):
        key=self.quotation()
        with patch.dict(os.environ,EMAIL_MODE='production'),patch('django.core.mail.EmailMessage.send',side_effect=TimeoutError('acknowledgement lost')) as send:
            deliver_one();deliver_one()
            send.assert_called_once()
        self.assertEqual(get_db().nexease_quotations.find_one({'_id':key})['status'],'review_required')

    def test_known_pre_send_failure_can_retry_without_sending(self):
        key=self.quotation()
        with patch.dict(os.environ,EMAIL_MODE='development'),patch('django.core.mail.EmailMessage.send') as send:
            deliver_one();send.assert_not_called()
        self.assertEqual(get_db().nexease_quotations.find_one({'_id':key})['status'],'retry')

    def test_successful_send_is_not_repeated(self):
        key=self.quotation()
        with patch.dict(os.environ,EMAIL_MODE='production'),patch('django.core.mail.EmailMessage.send',return_value=1) as send:
            deliver_one();deliver_one();send.assert_called_once()
        self.assertEqual(get_db().nexease_quotations.find_one({'_id':key})['status'],'sent')

    def test_queue_failure_does_not_starve_other_queues_or_normal_jobs(self):
        module='apps.core.management.commands.run_background_worker'
        with ExitStack() as stack:
            for name in ('register_finance_background_jobs','register_core_background_jobs','register_migration_background_jobs'):
                stack.enter_context(patch(module+'.'+name))
            stack.enter_context(patch(module+'.ShutdownStateService.is_shutting_down',return_value=False))
            stack.enter_context(patch(module+'.BackgroundJobService.recover_expired_jobs'))
            stack.enter_context(patch.object(Command,'_requeue_due_retries'))
            claim=stack.enter_context(patch(module+'.BackgroundJobService.claim_next_job',return_value=None))
            stack.enter_context(patch('apps.core.quotation.deliver_one',side_effect=RuntimeError('queue unavailable')))
            stack.enter_context(patch('apps.saas.alerts.deliver_one',side_effect=RuntimeError('another queue unavailable')))
            partner=stack.enter_context(patch('apps.saas.partner_mail.deliver_one'))
            stack.enter_context(patch.dict(os.environ,SUBSCRIPTION_ALERTS_ENABLED='false'))
            Command().handle(once=True,sleep=0,lease_seconds=300)
            partner.assert_called_once();claim.assert_called_once()
