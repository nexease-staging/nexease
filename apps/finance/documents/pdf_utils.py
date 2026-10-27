from decimal import Decimal


class PDFUtils:

    @staticmethod
    def money(
        value,
        currency="INR",
    ):
        """
        Format a monetary value safely.
        """

        if value is None:
            value = Decimal("0.00")

        value = Decimal(
            str(value)
        )

        value = value.quantize(
            Decimal("0.01")
        )

        currency = str(
            currency
            or ""
        ).strip().upper()

        if currency == "INR":
            return (
                f"INR {value:,.2f}"
            )

        if currency:
            return (
                f"{currency} "
                f"{value:,.2f}"
            )

        return (
            f"{value:,.2f}"
        )

    @staticmethod
    def decimal(
        value,
    ):
        if value is None:
            value = Decimal("0.00")

        value = Decimal(
            str(value)
        )

        value = value.quantize(
            Decimal("0.01")
        )

        return (
            f"{value:,.2f}"
        )

    @staticmethod
    def date(
        value,
    ):
        if not value:
            return ""

        return value.strftime(
            "%d-%m-%Y"
        )

    @staticmethod
    def datetime(
        value,
    ):
        if not value:
            return ""

        return value.strftime(
            "%d-%m-%Y %H:%M"
        )

    @staticmethod
    def safe_text(
        value,
        default="",
    ):
        if value is None:
            return default

        return str(
            value
        ).strip()