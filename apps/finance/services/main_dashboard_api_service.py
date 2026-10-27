from datetime import datetime

from apps.finance.services.main_dashboard_service import (
    MainDashboardService,
)


class MainDashboardAPIValidationError(
    ValueError
):
    def __init__(
        self,
        message,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = (
            details
            if details is not None
            else {}
        )


class MainDashboardAPIService:

    @staticmethod
    def _parse_optional_date(
        value,
        field_name,
    ):
        if value in (
            None,
            "",
        ):
            return None

        try:
            return (
                datetime.strptime(
                    str(value).strip(),
                    "%Y-%m-%d",
                )
                .date()
            )

        except (
            TypeError,
            ValueError,
        ):
            raise (
                MainDashboardAPIValidationError(
                    message=(
                        f"Invalid {field_name}. "
                        "Use YYYY-MM-DD."
                    ),
                    details={
                        field_name:
                            "Use YYYY-MM-DD.",
                    },
                )
            )

    @staticmethod
    def get_dashboard(
        *,
        user,
        organization,
        start_date=None,
        end_date=None,
    ):
        parsed_start_date = (
            MainDashboardAPIService
            ._parse_optional_date(
                start_date,
                "start_date",
            )
        )

        parsed_end_date = (
            MainDashboardAPIService
            ._parse_optional_date(
                end_date,
                "end_date",
            )
        )

        if (
            parsed_start_date
            and
            parsed_end_date
            and
            parsed_start_date
            >
            parsed_end_date
        ):
            raise (
                MainDashboardAPIValidationError(
                    message=(
                        "start_date cannot be "
                        "after end_date."
                    ),
                    details={
                        "start_date": (
                            "Must be on or before "
                            "end_date."
                        ),
                    },
                )
            )

        try:
            return (
                MainDashboardService
                .get_dashboard(
                    user=user,
                    organization=organization,
                    start_date=(
                        parsed_start_date
                    ),
                    end_date=(
                        parsed_end_date
                    ),
                )
            )

        except ValueError as exc:
            raise (
                MainDashboardAPIValidationError(
                    message=str(exc),
                )
            )