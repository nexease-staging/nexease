from django.conf import settings


class BuildInfoService:

    @staticmethod
    def get_info():
        commit_sha = getattr(
            settings,
            "GIT_COMMIT_SHA",
            "",
        )

        commit_short = (
            commit_sha[:12]
            if commit_sha
            else None
        )

        return {
            "application":
                settings.APP_NAME,

            "version":
                settings.APP_VERSION,

            "build":
                settings.APP_BUILD,

            "environment":
                settings.APP_ENV,

            "commit":
                commit_short,
        }