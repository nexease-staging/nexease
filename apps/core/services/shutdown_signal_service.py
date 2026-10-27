import signal

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)

from apps.core.services.shutdown_state_service import (
    ShutdownStateService,
)


class ShutdownSignalService:

    _registered = False

    @classmethod
    def _handle_signal(
        cls,
        signum,
        frame,
    ):
        ShutdownStateService.begin_shutdown()

        ApplicationLoggingService.log(
            level="WARNING",
            message=(
                "Application shutdown initiated."
            ),
            module="core",
            action="shutdown",
            status="started",
            signal_number=signum,
        )

    @classmethod
    def register(
        cls,
    ):
        if cls._registered:
            return

        signal.signal(
            signal.SIGTERM,
            cls._handle_signal,
        )

        cls._registered = True