from django.utils.deprecation import MiddlewareMixin

from apps.accounts.services import AuthenticationService


class MongoAuthenticationMiddleware(MiddlewareMixin):

    def process_view(
        self,
        request,
        view_func,
        view_args,
        view_kwargs,
    ):
        user = AuthenticationService.get_user(request)

        if user:
            request.user = user
        else:
            request.user = AnonymousMongoUser()


class AnonymousMongoUser:

    is_authenticated = False
    is_anonymous = True
    is_active = False

    def has_permission(self, permission_code):
        return False

    def get_username(self):
        return ""