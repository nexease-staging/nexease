import os
import platform
import time

import django

from django.conf import settings


class RuntimeInfoService:

    PROCESS_START_TIME = (
        time.time()
    )

    @staticmethod
    def get_uptime_seconds():
        uptime = (
            time.time()
            -
            RuntimeInfoService
            .PROCESS_START_TIME
        )

        return round(
            uptime,
            2,
        )

    @staticmethod
    def get_info():
        return {
            "process_id":
                os.getpid(),

            "uptime_seconds":
                RuntimeInfoService
                .get_uptime_seconds(),

            "python_version":
                platform.python_version(),

            "django_version":
                django.get_version(),

            "environment":
                settings.APP_ENV,

            "application":
                settings.APP_NAME,
        }