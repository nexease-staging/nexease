import json

from bson import ObjectId
from bson.errors import InvalidId

from django.http import JsonResponse

from apps.finance.services.generic_document_email_service import (
    GenericDocumentEmailService,
)
class DocumentEmailAPIService:

    @staticmethod
    def handle(
        *,
        request,
        document_type,
        document_id,
    ):
        # ==================================================
        # AUTHENTICATION
        # ==================================================

        user = request.user

        if not user.is_authenticated:
            return JsonResponse(
                {
                    "error":
                        "Not authenticated."
                },
                status=401,
            )

        # ==================================================
        # METHOD
        # ==================================================

        if request.method != "POST":
            return JsonResponse(
                {
                    "error":
                        "Method not allowed."
                },
                status=405,
            )

        # ==================================================
        # OBJECT ID
        # ==================================================

        try:

            ObjectId(
                str(
                    document_id
                )
            )

        except (
            InvalidId,
            TypeError,
        ):

            return JsonResponse(
                {
                    "error":
                        "Invalid document ID."
                },
                status=400,
            )

        # ==================================================
        # ORGANIZATION
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:
            return JsonResponse(
                {
                    "error":
                        "Organization not found."
                },
                status=403,
            )

        # ==================================================
        # GENERIC DELIVERY
        # ==================================================

        try:

            # ==================================================
            # OPTIONAL OVERRIDES
            # ==================================================

            recipient_email_override = None
            subject_override = None
            body_override = None

            # ==================================================
            # OPTIONAL JSON BODY
            # ==================================================

            if (
                request.content_type
                ==
                "application/json"
                and
                request.body
            ):

                try:

                    payload = json.loads(
                        request.body.decode(
                            "utf-8"
                        )
                    )

                except (
                    json.JSONDecodeError,
                    UnicodeDecodeError,
                ):

                    return JsonResponse(
                        {
                            "error":
                                "Invalid JSON body."
                        },
                        status=400,
                    )

                # ==============================================
                # JSON MUST BE AN OBJECT
                # ==============================================

                if not isinstance(
                    payload,
                    dict,
                ):

                    return JsonResponse(
                        {
                            "error":
                                "JSON body must be an object."
                        },
                        status=400,
                    )

                # ==============================================
                # RECIPIENT OVERRIDE
                # ==============================================

                recipient_email_override = (
                    payload.get(
                        "recipient_email"
                    )
                )

                # ==============================================
                # SUBJECT OVERRIDE
                # ==============================================

                subject_override = (
                    payload.get(
                        "subject"
                    )
                )

                # ==============================================
                # MESSAGE OVERRIDE
                # ==============================================

                body_override = (
                    payload.get(
                        "message"
                    )
                )

            # ==================================================
            # SEND DOCUMENT EMAIL
            # ==================================================

            result = (
                GenericDocumentEmailService
                .send(
                    user=user,
                    organization=organization,
                    document_type=document_type,
                    document_id=str(
                        document_id
                    ),
                    recipient_email_override=(
                        recipient_email_override
                    ),
                    subject_override=(
                        subject_override
                    ),
                    body_override=(
                        body_override
                    ),
                )
            )

            # ==================================================
            # DOCUMENT NOT FOUND
            # ==================================================

            if result is None:

                return JsonResponse(
                    {
                        "error":
                            "Document not found."
                    },
                    status=404,
                )

            # ==================================================
            # RESULT DATA
            # ==================================================

            document = (
                result[
                    "document"
                ]
            )

            delivery = (
                result[
                    "delivery"
                ]
            )

            delivery_data = (
                result[
                    "delivery_data"
                ]
            )

            # Make sure we have the latest saved state.

            delivery.reload()

            # ==================================================
            # SUCCESS
            # ==================================================

            return JsonResponse(
                {
                    "message":
                        "Document email sent.",

                    "document": {
                        "id":
                            str(
                                document.id
                            ),

                        "type":
                            delivery_data[
                                "document_type"
                            ],

                        "number":
                            delivery_data[
                                "document_number"
                            ],
                    },

                    "recipient": {
                        "name":
                            delivery_data[
                                "recipient_name"
                            ],

                        "email":
                            result[
                                "actual_recipient_email"
                            ],
                    },

                    "delivery": {
                        "id":
                            str(
                                delivery.id
                            ),

                        "channel":
                            delivery.channel,

                        "status":
                            delivery.status,

                        "sent_at": (
                            delivery.sent_at
                            .isoformat()
                            if delivery.sent_at
                            else None
                        ),
                    },
                },
                status=200,
            )

        # ==================================================
        # PERMISSION
        # ==================================================

        except PermissionError as exc:

            message = str(
                exc
            )

            status_code = (
                401
                if message
                ==
                "Not authenticated."
                else 403
            )

            return JsonResponse(
                {
                    "error":
                        message
                },
                status=status_code,
            )

        # ==================================================
        # CONTROLLED VALIDATION
        # ==================================================

        except ValueError as exc:

            return JsonResponse(
                {
                    "error":
                        str(
                            exc
                        )
                },
                status=400,
            )

        # ==================================================
        # UNEXPECTED DELIVERY FAILURE
        # ==================================================

        except Exception:

            return JsonResponse(
                {
                    "error":
                        "Document email "
                        "delivery failed."
                },
                status=500,
            )