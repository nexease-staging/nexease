class TenantService:

    @staticmethod
    def belongs_to_user(user, document):
        if not user:
            return False

        if not user.is_active:
            return False

        if not user.organization:
            return False

        if not document:
            return False

        if not getattr(document, "organization", None):
            return False

        return (
            document.organization.id
            == user.organization.id
        )