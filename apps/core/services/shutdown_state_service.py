import threading


class ShutdownStateService:

    _lock = (
        threading.Lock()
    )

    _shutting_down = False

    @classmethod
    def begin_shutdown(
        cls,
    ):
        with cls._lock:

            cls._shutting_down = True

    @classmethod
    def reset(
        cls,
    ):
        with cls._lock:

            cls._shutting_down = False

    @classmethod
    def is_shutting_down(
        cls,
    ):
        with cls._lock:

            return cls._shutting_down