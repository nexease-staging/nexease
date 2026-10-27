import time


class PasswordResetTimingService:
    MINIMUM_RESPONSE_SECONDS = 0.8
    SLEEP_EPSILON_SECONDS = 0.000001

    @staticmethod
    def start():
        return time.perf_counter()

    @classmethod
    def wait_for_minimum_duration(
        cls,
        *,
        started_at,
    ):
        elapsed = (
            time.perf_counter()
            -
            started_at
        )

        remaining = (
            cls.MINIMUM_RESPONSE_SECONDS
            -
            elapsed
        )

        sleep_seconds = (
            remaining
            if remaining
            >
            cls.SLEEP_EPSILON_SECONDS
            else 0
        )

        if sleep_seconds > 0:
            time.sleep(
                sleep_seconds
            )

        return {
            "elapsed_seconds": elapsed,
            "slept_seconds": sleep_seconds,
        }