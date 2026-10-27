from .employee_access import employee_migration_access
import json

from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.migration.services.migration_api_service import (
    MigrationAPIService,
    MigrationAPIValidationError,
)


@api_login_required
@employee_migration_access
@api_rate_limit(
    scope="migrations.collection",
    limit=120,
    window_seconds=60,
)
def migration_collection_api(
    request,
):
    # ==================================================
    # GET: LIST MIGRATION BATCHES
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "migration.read",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        raw_limit = (
            request.GET.get(
                "limit",
                "100",
            )
        )

        try:
            limit = int(
                raw_limit
            )

        except (
            TypeError,
            ValueError,
        ):
            return (
                APIResponseService
                .validation_error(
                    message=(
                        "Migration validation "
                        "failed."
                    ),
                    details={
                        "limit": [
                            (
                                "Limit must be an "
                                "integer between "
                                "1 and 100."
                            )
                        ],
                    },
                    request=request,
                )
            )

        try:
            batches = (
                MigrationAPIService
                .list_batches(
                    organization=(
                        request
                        .api_organization
                    ),
                    limit=limit,
                )
            )

        except MigrationAPIValidationError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        if not AuthorizationService.has_permission(request.api_user,"payroll.read"):
            batches=[b for b in batches if b.migration_type!="EMPLOYEES"]
        serialized_batches = [
            (
                MigrationAPIService
                .serialize_batch(
                    batch
                )
            )
            for batch
            in batches
        ]

        return (
            APIResponseService
            .success(
                data={
                    "migrations":
                        serialized_batches,
                    "count":
                        len(
                            serialized_batches
                        ),
                },
                message=(
                    "Migration batches retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST: CREATE MIGRATION BATCH
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "migration.create",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        content_type = (
            request.content_type
            or
            ""
        ).lower()

        if (
            "application/json"
            not in content_type
        ):
            return (
                APIResponseService
                .bad_request(
                    message=(
                        "Content-Type must be "
                        "application/json."
                    ),
                    request=request,
                )
            )

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
            return (
                APIResponseService
                .bad_request(
                    message=(
                        "Invalid JSON body."
                    ),
                    request=request,
                )
            )

        try:
            batch = (
                MigrationAPIService
                .create_batch(
                    organization=(
                        request
                        .api_organization
                    ),
                    created_by=(
                        request.api_user
                    ),
                    payload=payload,
                )
            )

        except MigrationAPIValidationError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "migration": (
                        MigrationAPIService
                        .serialize_batch(
                            batch
                        )
                    ),
                },
                message=(
                    "Migration batch created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    # ==================================================
    # UNSUPPORTED METHOD
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or POST for "
                "the migration collection."
            ),
            request=request,
        )
    )


@api_login_required
@employee_migration_access
@api_rate_limit(
    scope="migrations.detail",
    limit=120,
    window_seconds=60,
)
def migration_detail_api(
    request,
    batch_id,
):
    # ==================================================
    # GET: MIGRATION BATCH DETAIL
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "migration.read",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        try:
            batch = (
                MigrationAPIService
                .get_batch(
                    organization=(
                        request
                        .api_organization
                    ),
                    batch_id=batch_id,
                )
            )

        except LookupError:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Migration batch not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "migration": (
                        MigrationAPIService
                        .serialize_batch(
                            batch
                        )
                    ),
                },
                message=(
                    "Migration batch retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET for a migration batch."
            ),
            request=request,
        )
    )

@api_login_required
@employee_migration_access
@api_rate_limit(
    scope="migrations.upload",
    limit=30,
    window_seconds=60,
)
def migration_upload_api(
    request,
    batch_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to upload a "
                    "migration file."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "migration.create",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    uploaded_file = (
        request.FILES.get("file")
    )

    try:
        batch = (
            MigrationAPIService
            .get_batch(
                organization=(
                    request.api_organization
                ),
                batch_id=batch_id,
            )
        )

        result = (
            MigrationAPIService
            .upload_file(
                user=(
                    request.api_user
                ),
                batch=batch,
                uploaded_file=uploaded_file,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Migration batch not found."
                ),
                request=request,
            )
        )

    except MigrationAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    batch = result["batch"]
    upload = result["upload"]
    parsed_file = result["file"]

    return (
        APIResponseService
        .success(
            data={
                "migration": (
                    MigrationAPIService
                    .serialize_batch(
                        batch
                    )
                ),
                "file": {
                    "upload_id": str(
                        upload.id
                    ),
                    "filename": (
                        upload.filename
                    ),
                    "extension": (
                        upload.extension
                    ),
                    "size": upload.size,
                    "columns": (
                        parsed_file.get(
                            "columns",
                            [],
                        )
                    ),
                    "total_rows": (
                        parsed_file.get(
                            "total_rows",
                            0,
                        )
                    ),
                    "sample_rows": (
                        parsed_file.get(
                            "sample_rows",
                            [],
                        )
                    ),
                    "sheet_name": (
                        parsed_file.get(
                            "sheet_name"
                        )
                    ),
                },
            },
            message=(
                "Migration file uploaded "
                "successfully."
            ),
            status=201,
            request=request,
        )
    )

@api_login_required
@employee_migration_access
@api_rate_limit(
    scope="migrations.validate",
    limit=20,
    window_seconds=60,
)
def migration_validate_api(
    request,
    batch_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to validate a "
                    "migration."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "migration.validate",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            MigrationAPIService
            .validate_batch(
                organization=(
                    request.api_organization
                ),
                batch_id=batch_id,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Migration batch not found."
                ),
                request=request,
            )
        )

    except MigrationAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    batch = result["batch"]
    validation = result["validation"]

    return (
        APIResponseService
        .success(
            data={
                "migration": (
                    MigrationAPIService
                    .serialize_batch(
                        batch
                    )
                ),
                "validation":
                    validation,
            },
            message=(
                "Migration validated "
                "successfully."
            ),
            status=200,
            request=request,
        )
    )

@api_login_required
@employee_migration_access
@api_rate_limit(
    scope="migrations.import",
    limit=10,
    window_seconds=60,
)
def migration_import_api(
    request,
    batch_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to import a "
                    "migration."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "migration.import",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            MigrationAPIService
            .import_batch(
                organization=(
                    request.api_organization
                ),
                batch_id=batch_id,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Migration batch not found."
                ),
                request=request,
            )
        )

    except MigrationAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    batch = result["batch"]
    import_result = result["import"]

    return (
        APIResponseService
        .success(
            data={
                "migration": (
                    MigrationAPIService
                    .serialize_batch(
                        batch
                    )
                ),
                "import": import_result,
            },
            message=(
                "Migration imported "
                "successfully."
            ),
            status=200,
            request=request,
        )
    )
@api_login_required
@employee_migration_access
def migration_template_api(request, migration_type):
    from apps.migration.services.migration_schema_service import MigrationSchemaService
    from apps.business.views import workbook_response
    if request.method != 'GET':
        return APIResponseService.bad_request(message='Use GET.',request=request)
    if not AuthorizationService.has_permission(request.api_user,'migration.read'):
        return APIResponseService.forbidden(message='Permission denied.',request=request)
    try:
        schema=MigrationSchemaService.get_schema(migration_type)
    except ValueError as e:
        return APIResponseService.validation_error(message=str(e),request=request)
    from apps.migration.services.template_examples import EXAMPLES
    fields=schema['fields']
    guides=[['Column','Required','Instructions']]
    for key,spec in fields.items():
        note='Use an existing organization record.' if key.endswith(('_id','_code','_sku','_number')) else 'Enter a value.'
        if key.endswith('_date'):note='Use YYYY-MM-DD.'
        if key=='bank_account_id':note='Copy the ID from the bank account detail/API; bank account must be active.'
        guides.append([key,'Yes' if spec.get('required') else 'No',note])
    return workbook_response({'Data':[list(fields)],'Example only':[list(fields),[('Example worker' if k=='name' else EXAMPLES.get(k,'')) if migration_type=='EMPLOYEES' else EXAMPLES.get(k,'Example') for k in fields]],'Column guide':guides,'Read me':[['NexEase migration template'],['Fill the Data sheet. Do not rename the column headers.'],['Import master records before transactions. Run validation before import.'],['Opening inventory requires existing product and warehouse codes.'],['Sales invoices require fulfilled sales orders; vendor bills require fully received purchase orders.'],['Payment imports require issued/posted documents and an existing bank account.'],['Use one payment allocation per row with a unique reference number.'],['Review the validation results. Imported draft invoices/bills must be issued/posted separately.']]},'NexEase-'+migration_type)
