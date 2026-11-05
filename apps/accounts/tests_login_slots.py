from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mongomock
from django.test import SimpleTestCase, override_settings

from apps.accounts.services import AuthenticationService


@override_settings(NEXEASE_MOBILE_ENABLED=True)
class LoginSlotTests(SimpleTestCase):
    def test_new_login_replaces_only_same_platform_and_legacy_is_rejected(self):
        user = SimpleNamespace(id="user-1", is_active=True,
                               organization=SimpleNamespace(is_active=True))
        slots = mongomock.MongoClient().db.slots

        def request(key, **meta):
            session = MagicMock(session_key=key)
            data = {}
            session.__setitem__.side_effect = data.__setitem__
            session.get.side_effect = data.get
            return SimpleNamespace(META=meta, session=session)

        android = {"HTTP_ORIGIN": "https://localhost",
                   "HTTP_X_NEXEASE_CLIENT": "android"}
        web1, web2 = request("web1"), request("web2")
        apk1 = request("apk1", HTTP_ORIGIN="https://localhost",
                       HTTP_USER_AGENT="Dalvik (Android 16)")
        apk2 = request("apk2", **android)
        legacy = request("legacy")
        legacy.session[AuthenticationService.SESSION_USER_ID] = user.id

        with patch.object(AuthenticationService, "_slots", return_value=slots), \
             patch("apps.accounts.services.User") as model:
            model.objects.return_value.first.return_value = user
            for req in (web1, apk1, web2):
                AuthenticationService.login(req, user)
            self.assertIsNone(AuthenticationService.get_user(web1))
            self.assertIs(AuthenticationService.get_user(web2), user)
            self.assertIs(AuthenticationService.get_user(apk1), user)
            AuthenticationService.login(apk2, user)
            self.assertIsNone(AuthenticationService.get_user(apk1))
            self.assertIs(AuthenticationService.get_user(apk2), user)
            self.assertIs(AuthenticationService.get_user(web2), user)
            self.assertIsNone(AuthenticationService.get_user(legacy))
