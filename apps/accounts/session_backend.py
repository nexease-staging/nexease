from datetime import datetime

from django.contrib.sessions.backends.base import (
    CreateError,
    SessionBase,
)

from apps.accounts.session_models import (
    MongoSession,
)


class SessionStore(SessionBase):

    def load(self):

        if not self.session_key:
            return {}

        session = (
            MongoSession.objects(
                session_key=self.session_key,
                expire_date__gt=datetime.utcnow(),
            )
            .first()
        )

        if not session:
            self._session_key = None
            return {}

        try:

            return self.decode(
                session.session_data
            )

        except Exception:

            self._session_key = None
            return {}

    def exists(
        self,
        session_key,
    ):

        return (
            MongoSession.objects(
                session_key=session_key,
                expire_date__gt=datetime.utcnow(),
            )
            .first()
            is not None
        )

    def create(self):

        while True:

            self._session_key = (
                self._get_new_session_key()
            )

            try:

                self.save(
                    must_create=True
                )

                return

            except CreateError:

                continue

    def save(
        self,
        must_create=False,
    ):

        if self.session_key is None:

            return self.create()

        session_data = (
            self.encode(
                self._get_session(
                    no_load=must_create
                )
            )
        )

        expire_date = (
            self.get_expiry_date()
        )

        now = datetime.utcnow()

        existing = (
            MongoSession.objects(
                session_key=self.session_key
            )
            .first()
        )

        if must_create:

            if existing:

                raise CreateError

            MongoSession(
                session_key=self.session_key,
                session_data=session_data,
                expire_date=expire_date,
                created_at=now,
                updated_at=now,
            ).save()

            return

        if existing:

            existing.session_data = (
                session_data
            )

            existing.expire_date = (
                expire_date
            )

            existing.updated_at = now

            existing.save()

        else:

            MongoSession(
                session_key=self.session_key,
                session_data=session_data,
                expire_date=expire_date,
                created_at=now,
                updated_at=now,
            ).save()

    def delete(
        self,
        session_key=None,
    ):

        key = (
            session_key
            or
            self.session_key
        )

        if not key:
            return

        MongoSession.objects(
            session_key=key
        ).delete()

        if (
            key
            ==
            self.session_key
        ):

            self._session_key = None

    @classmethod
    def clear_expired(cls):

        MongoSession.objects(
            expire_date__lte=datetime.utcnow()
        ).delete()