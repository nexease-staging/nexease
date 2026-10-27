from django.core.exceptions import (
    ValidationError,
)
from django.http import Http404

from mongoengine.errors import (
    NotUniqueError,
)
from pymongo.errors import (
    NetworkTimeout,
)

from apps.core.api_exceptions import (
    APIBusinessRuleError,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)


# ==================================================
# RESPONSE CONTRACT TEST VIEWS
# ==================================================

def test_contract_success(
    request,
):
    return (
        APIResponseService
        .success(
            data={
                "resource_id":
                    "contract-test-001",
            },
            message=(
                "Contract success."
            ),
            request=request,
        )
    )


def test_contract_validation(
    request,
):
    return (
        APIResponseService
        .validation_error(
            message=(
                "Validation failed."
            ),
            details={
                "email": [
                    "This field is invalid.",
                ],

                "name": [
                    "This field is required.",
                ],
            },
            request=request,
        )
    )


def test_contract_conflict(
    request,
):
    return (
        APIResponseService
        .conflict(
            message=(
                "Resource already exists."
            ),
            details={
                "field":
                    "email",
            },
            request=request,
        )
    )


def test_contract_unprocessable(
    request,
):
    return (
        APIResponseService
        .unprocessable_entity(
            message=(
                "Business rule rejected "
                "the request."
            ),
            details={
                "rule":
                    "inventory_negative",
            },
            request=request,
        )
    )


# ==================================================
# EXCEPTION NORMALIZATION TEST VIEWS
# ==================================================

def test_exception_validation(
    request,
):
    raise ValidationError(
        {
            "email": [
                "Invalid email value.",
            ],
        }
    )


def test_exception_not_found(
    request,
):
    raise Http404(
        "Internal resource detail."
    )


def test_exception_conflict(
    request,
):
    raise NotUniqueError(
        "Internal duplicate-key detail."
    )


def test_exception_business_rule(
    request,
):
    raise APIBusinessRuleError(
        (
            "Business rule rejected "
            "the request."
        ),
        details={
            "rule":
                "inventory_negative",
        },
    )


def test_exception_mongodb(
    request,
):
    raise NetworkTimeout(
        "Internal MongoDB timeout detail."
    )


def test_exception_unexpected(
    request,
):
    raise RuntimeError(
        "Sensitive internal exception detail."
    )