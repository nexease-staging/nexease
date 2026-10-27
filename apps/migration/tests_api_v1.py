import json



from datetime import datetime

from types import SimpleNamespace

from unittest.mock import patch



from bson import ObjectId



from django.test import (

    Client,

    SimpleTestCase,

)



from apps.authorization.services import (

    AuthorizationService,

)

from apps.core.services.api_rate_limit_service import (

    APIRateLimitService,

)

from apps.core.services.application_logging_service import (

    ApplicationLoggingService,

)

from apps.core.services.mongodb_error_logging_service import (

    MongoDBErrorLoggingService,

)

from apps.migration.services.migration_api_service import (

    MigrationAPIService,

    MigrationAPIValidationError,

)

from apps.organizations.api_context_service import (

    APIOrganizationContextService,

)

from django.core.files.uploadedfile import (

    SimpleUploadedFile,

)

from apps.purchasing.repositories.purchase_return_repository import (

    PurchaseReturnRepository,

)

from apps.purchasing.repositories.vendor_debit_note_repository import (

    VendorDebitNoteRepository,

)





class MigrationAPIV1RegressionTestCase(

    SimpleTestCase

):



    MIGRATIONS_URL = (

        "/api/v1/migrations/"

    )



    def setUp(self):

        now = datetime.utcnow()



        self.organization = (

            SimpleNamespace(

                id=ObjectId(),

                name=(

                    "Migration Regression "

                    "Organization"

                ),

                is_active=True,

            )

        )



        self.other_organization = (

            SimpleNamespace(

                id=ObjectId(),

                name="Other Organization",

                is_active=True,

            )

        )



        self.user = SimpleNamespace(

            id=ObjectId(),

            organization=(

                self.organization

            ),

            email="admin@example.com",

            first_name="System",

            last_name="Administrator",

            is_active=True,

            is_authenticated=True,

            is_anonymous=False,

        )



        self.batch = SimpleNamespace(

            id=ObjectId(),

            organization=(

                self.organization

            ),

            created_by=self.user,

            source_system="ZOHO_INVENTORY",

            migration_type="PRODUCTS",

            status="CREATED",

            upload_id=None,

            job_id=None,

            mapping={

                "Product Name": "name",

            },

            options={

                "skip_duplicates": True,

            },

            total_rows=10,

            valid_rows=8,

            invalid_rows=2,

            imported_rows=0,

            skipped_rows=0,

            failed_rows=0,

            validation_result={},

            import_result={},

            error_summary={},

            started_at=None,

            completed_at=None,

            created_at=now,

            updated_at=now,

        )



        self.organization_context = {

            "user": self.user,

            "organization":

                self.organization,

        }



        self.patchers = [

            patch.object(

                ApplicationLoggingService,

                "log",

                return_value=None,

            ),

            patch.object(

                MongoDBErrorLoggingService,

                "log_exception",

                return_value=None,

            ),

            patch.object(

                APIOrganizationContextService,

                "resolve",

                return_value=(

                    self.organization_context

                ),

            ),

            patch.object(

                AuthorizationService,

                "has_permission",

                return_value=True,

            ),

            patch.object(

                PurchaseReturnRepository,

                "queryset_for_organization",

                return_value=[],

            ),

            patch.object(

                VendorDebitNoteRepository,

                "queryset_for_organization",

                return_value=[],

            ),

            patch.object(

                APIRateLimitService,

                "check",

                return_value={

                    "allowed": True,

                },

            ),

            patch.object(

                APIRateLimitService,

                "add_headers",

                side_effect=(

                    lambda response, result:

                    response

                ),

            ),

        ]



        for patcher in self.patchers:

            patcher.start()



        self.client = Client(

            raise_request_exception=False

        )



    def tearDown(self):

        for patcher in reversed(

            self.patchers

        ):

            patcher.stop()



    def detail_url(

        self,

        batch=None,

    ):

        batch = (

            batch

            or

            self.batch

        )



        return (

            f"{self.MIGRATIONS_URL}"

            f"{batch.id}/"

        )



    def upload_url(

        self,

        batch=None,

    ):

        batch = (

            batch

            or

            self.batch

        )



        return (

            f"{self.MIGRATIONS_URL}"

            f"{batch.id}/upload/"

        )



    def import_url(

        self,

        batch=None,

    ):

        batch = (

            batch

            or

            self.batch

        )



        return (

            f"{self.MIGRATIONS_URL}"

            f"{batch.id}/import/"

        )



    def validate_url(

        self,

        batch=None,

    ):

        batch = (

            batch

            or

            self.batch

        )



        return (

            f"{self.MIGRATIONS_URL}"

            f"{batch.id}/validate/"

        )



    def assert_success_contract(

        self,

        response,

        expected_status=200,

    ):

        body = response.json()



        self.assertEqual(

            response.status_code,

            expected_status,

        )



        self.assertTrue(

            body["success"]

        )



        self.assertIn(

            "data",

            body,

        )



        self.assertTrue(

            body.get(

                "request_id"

            )

        )



        self.assertEqual(

            response.headers.get(

                "X-Request-ID"

            ),

            body["request_id"],

        )



        self.assertEqual(

            response.headers.get(

                "Cache-Control"

            ),

            "no-store",

        )



        return body



    def assert_error_contract(

        self,

        response,

        expected_status,

        expected_code,

    ):

        body = response.json()



        self.assertEqual(

            response.status_code,

            expected_status,

        )



        self.assertFalse(

            body["success"]

        )



        self.assertEqual(

            body["error"]["code"],

            expected_code,

        )



        self.assertTrue(

            body.get(

                "request_id"

            )

        )



        self.assertEqual(

            response.headers.get(

                "X-Request-ID"

            ),

            body["request_id"],

        )



        self.assertEqual(

            response.headers.get(

                "Cache-Control"

            ),

            "no-store",

        )



        return body



    # ==================================================

    # AUTHENTICATION

    # ==================================================



    def test_anonymous_migration_list_is_rejected(

        self,

    ):

        with patch.object(

            APIOrganizationContextService,

            "resolve",

            side_effect=PermissionError(

                "Not authenticated."

            ),

        ):

            response = self.client.get(

                self.MIGRATIONS_URL

            )



        self.assert_error_contract(

            response,

            401,

            "UNAUTHORIZED",

        )



    # ==================================================

    # LIST

    # ==================================================



    def test_migration_list_returns_batches(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "list_batches",

            return_value=[

                self.batch,

            ],

        ) as list_mock:

            response = self.client.get(

                self.MIGRATIONS_URL

            )



        body = (

            self.assert_success_contract(

                response

            )

        )



        self.assertEqual(

            body["data"]["count"],

            1,

        )



        self.assertEqual(

            len(

                body["data"][

                    "migrations"

                ]

            ),

            1,

        )



        self.assertEqual(

            body["data"][

                "migrations"

            ][0]["id"],

            str(

                self.batch.id

            ),

        )



        list_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            limit=100,

        )



    def test_migration_list_accepts_limit(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "list_batches",

            return_value=[],

        ) as list_mock:

            response = self.client.get(

                (

                    self.MIGRATIONS_URL

                    +

                    "?limit=25"

                )

            )



        self.assert_success_contract(

            response

        )



        list_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            limit=25,

        )



    def test_migration_list_rejects_non_integer_limit(

        self,

    ):

        response = self.client.get(

            (

                self.MIGRATIONS_URL

                +

                "?limit=invalid"

            )

        )



        body = self.assert_error_contract(

            response,

            400,

            "VALIDATION_ERROR",

        )



        self.assertIn(

            "limit",

            body["error"]["details"],

        )



    def test_migration_list_rejects_out_of_range_limit(

        self,

    ):

        validation_error = (

            MigrationAPIValidationError(

                "Migration validation failed.",

                details={

                    "limit": [

                        (

                            "Limit must be an "

                            "integer between "

                            "1 and 100."

                        )

                    ],

                },

            )

        )



        with patch.object(

            MigrationAPIService,

            "list_batches",

            side_effect=validation_error,

        ):

            response = self.client.get(

                (

                    self.MIGRATIONS_URL

                    +

                    "?limit=101"

                )

            )



        body = self.assert_error_contract(

            response,

            400,

            "VALIDATION_ERROR",

        )



        self.assertIn(

            "limit",

            body["error"]["details"],

        )



    def test_migration_list_without_permission_is_forbidden(

        self,

    ):

        with patch.object(

            AuthorizationService,

            "has_permission",

            return_value=False,

        ):

            response = self.client.get(

                self.MIGRATIONS_URL

            )



        self.assert_error_contract(

            response,

            403,

            "FORBIDDEN",

        )



    # ==================================================

    # CREATE

    # ==================================================



    def test_create_migration_returns_201(

        self,

    ):

        payload = {

            "source_system":

                "ZOHO_INVENTORY",

            "migration_type":

                "PRODUCTS",

            "mapping": {

                "Product Name": "name",

            },

            "options": {

                "skip_duplicates": True,

            },

        }



        with patch.object(

            MigrationAPIService,

            "create_batch",

            return_value=self.batch,

        ) as create_mock:

            response = self.client.post(

                self.MIGRATIONS_URL,

                data=json.dumps(

                    payload

                ),

                content_type=(

                    "application/json"

                ),

            )



        body = (

            self.assert_success_contract(

                response,

                201,

            )

        )



        self.assertEqual(

            body["data"][

                "migration"

            ]["id"],

            str(

                self.batch.id

            ),

        )



        self.assertEqual(

            body["data"][

                "migration"

            ]["source_system"],

            "ZOHO_INVENTORY",

        )



        create_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            created_by=self.user,

            payload=payload,

        )



    def test_create_customer_migration_returns_201(

        self,

    ):

        customer_batch = SimpleNamespace(

            **{

                **self.batch.__dict__,

                "source_system": "GENERIC",

                "migration_type": "CUSTOMERS",

                "mapping": {

                    "Customer Code": "code",

                    "Customer Name": "name",

                },

                "options": {

                    "skip_duplicates": True,

                },

            }

        )



        payload = {

            "source_system": "GENERIC",

            "migration_type": "CUSTOMERS",

            "mapping": {

                "Customer Code": "code",

                "Customer Name": "name",

            },

            "options": {

                "skip_duplicates": True,

            },

        }



        with patch.object(

            MigrationAPIService,

            "create_batch",

            return_value=customer_batch,

        ) as create_mock:

            response = self.client.post(

                self.MIGRATIONS_URL,

                data=json.dumps(

                    payload

                ),

                content_type=(

                    "application/json"

                ),

            )



        body = (

            self.assert_success_contract(

                response,

                201,

            )

        )



        migration = (

            body["data"]["migration"]

        )



        self.assertEqual(

            migration["id"],

            str(

                customer_batch.id

            ),

        )



        self.assertEqual(

            migration[

                "source_system"

            ],

            "GENERIC",

        )



        self.assertEqual(

            migration[

                "migration_type"

            ],

            "CUSTOMERS",

        )



        self.assertEqual(

            migration["mapping"],

            {

                "Customer Code": "code",

                "Customer Name": "name",

            },

        )



        self.assertEqual(

            migration["options"],

            {

                "skip_duplicates": True,

            },

        )



        create_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            created_by=self.user,

            payload=payload,

        )



    def test_create_supplier_migration_returns_201(

        self,

    ):

        supplier_batch = SimpleNamespace(

            **{

                **self.batch.__dict__,

                "source_system": "GENERIC",

                "migration_type": "SUPPLIERS",

                "mapping": {

                    "Supplier Code": "code",

                    "Supplier Name": "name",

                },

                "options": {

                    "skip_duplicates": True,

                },

            }

        )



        payload = {

            "source_system": "GENERIC",

            "migration_type": "SUPPLIERS",

            "mapping": {

                "Supplier Code": "code",

                "Supplier Name": "name",

            },

            "options": {

                "skip_duplicates": True,

            },

        }



        with patch.object(

            MigrationAPIService,

            "create_batch",

            return_value=supplier_batch,

        ) as create_mock:

            response = self.client.post(

                self.MIGRATIONS_URL,

                data=json.dumps(

                    payload

                ),

                content_type=(

                    "application/json"

                ),

            )



        body = (

            self.assert_success_contract(

                response,

                201,

            )

        )



        migration = (

            body["data"]["migration"]

        )



        self.assertEqual(

            migration["id"],

            str(

                supplier_batch.id

            ),

        )



        self.assertEqual(

            migration[

                "source_system"

            ],

            "GENERIC",

        )



        self.assertEqual(

            migration[

                "migration_type"

            ],

            "SUPPLIERS",

        )



        self.assertEqual(

            migration["mapping"],

            {

                "Supplier Code": "code",

                "Supplier Name": "name",

            },

        )



        self.assertEqual(

            migration["options"],

            {

                "skip_duplicates": True,

            },

        )



        create_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            created_by=self.user,

            payload=payload,

        )



    def test_create_migration_rejects_invalid_skip_duplicates_type(

        self,

    ):

        response = self.client.post(

            "/api/v1/migrations/",

            data={

                "source_system": "GENERIC",

                "migration_type": "PRODUCTS",

                "options": {

                    "skip_duplicates": "yes",

                },

            },

            content_type="application/json",

        )



        body = self.assert_error_contract(

            response,

            400,

            "VALIDATION_ERROR",

        )



        self.assertIn(

            "options",

            body["error"]["details"],

        )





    def test_create_migration_rejects_unsupported_option(

        self,

    ):

        response = self.client.post(

            "/api/v1/migrations/",

            data={

                "source_system": "GENERIC",

                "migration_type": "PRODUCTS",

                "options": {

                    "dry_run": True,

                },

            },

            content_type="application/json",

        )



        body = self.assert_error_contract(

            response,

            400,

            "VALIDATION_ERROR",

        )



        self.assertIn(

            "options",

            body["error"]["details"],

        )



    def test_create_migration_validation_error(

        self,

    ):

        validation_error = (

            MigrationAPIValidationError(

                "Migration validation failed.",

                details={

                    "source_system": [

                        (

                            "Invalid migration "

                            "source system."

                        )

                    ],

                },

            )

        )



        with patch.object(

            MigrationAPIService,

            "create_batch",

            side_effect=validation_error,

        ):

            response = self.client.post(

                self.MIGRATIONS_URL,

                data=json.dumps({

                    "source_system":

                        "INVALID",

                    "migration_type":

                        "PRODUCTS",

                }),

                content_type=(

                    "application/json"

                ),

            )



        body = self.assert_error_contract(

            response,

            400,

            "VALIDATION_ERROR",

        )



        self.assertIn(

            "source_system",

            body["error"]["details"],

        )



    def test_create_migration_requires_json_content_type(

        self,

    ):

        response = self.client.post(

            self.MIGRATIONS_URL,

            data={

                "source_system":

                    "GENERIC",

                "migration_type":

                    "PRODUCTS",

            },

        )



        self.assert_error_contract(

            response,

            400,

            "BAD_REQUEST",

        )



    def test_create_migration_rejects_invalid_json(

        self,

    ):

        response = self.client.post(

            self.MIGRATIONS_URL,

            data="{invalid-json",

            content_type=(

                "application/json"

            ),

        )



        self.assert_error_contract(

            response,

            400,

            "BAD_REQUEST",

        )



    def test_create_migration_without_permission_is_forbidden(

        self,

    ):

        with patch.object(

            AuthorizationService,

            "has_permission",

            return_value=False,

        ):

            response = self.client.post(

                self.MIGRATIONS_URL,

                data=json.dumps({

                    "source_system":

                        "GENERIC",

                    "migration_type":

                        "PRODUCTS",

                }),

                content_type=(

                    "application/json"

                ),

            )



        self.assert_error_contract(

            response,

            403,

            "FORBIDDEN",

        )



    # ==================================================

    # DETAIL

    # ==================================================



    def test_migration_detail_returns_batch(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "get_batch",

            return_value=self.batch,

        ) as get_mock:

            response = self.client.get(

                self.detail_url()

            )



        body = (

            self.assert_success_contract(

                response

            )

        )



        self.assertEqual(

            body["data"][

                "migration"

            ]["id"],

            str(

                self.batch.id

            ),

        )



        get_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            batch_id=str(

                self.batch.id

            ),

        )



    def test_missing_migration_detail_returns_404(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "get_batch",

            side_effect=LookupError(

                "Migration batch not found."

            ),

        ):

            response = self.client.get(

                self.detail_url()

            )



        self.assert_error_contract(

            response,

            404,

            "NOT_FOUND",

        )



    def test_cross_tenant_migration_is_hidden(

        self,

    ):

        foreign_batch = (

            SimpleNamespace(

                id=ObjectId(),

                organization=(

                    self.other_organization

                ),

            )

        )



        with patch.object(

            MigrationAPIService,

            "get_batch",

            side_effect=LookupError(

                "Migration batch not found."

            ),

        ) as get_mock:

            response = self.client.get(

                self.detail_url(

                    foreign_batch

                )

            )



        self.assert_error_contract(

            response,

            404,

            "NOT_FOUND",

        )



        get_mock.assert_called_once_with(

            organization=(

                self.organization

            ),

            batch_id=str(

                foreign_batch.id

            ),

        )



    def test_migration_detail_without_permission_is_forbidden(

        self,

    ):

        with patch.object(

            AuthorizationService,

            "has_permission",

            return_value=False,

        ):

            response = self.client.get(

                self.detail_url()

            )



        self.assert_error_contract(

            response,

            403,

            "FORBIDDEN",

        )



    # ==================================================

    # METHODS

    # ==================================================



    def test_migration_collection_rejects_delete(

        self,

    ):

        response = self.client.delete(

            self.MIGRATIONS_URL

        )



        self.assert_error_contract(

            response,

            405,

            "METHOD_NOT_ALLOWED",

        )



    def test_migration_detail_rejects_post(

        self,

    ):

        response = self.client.post(

            self.detail_url(),

            data=json.dumps({}),

            content_type=(

                "application/json"

            ),

        )



        self.assert_error_contract(

            response,

            405,

            "METHOD_NOT_ALLOWED",

        )



    # ==================================================

    # RESPONSE SAFETY

    # ==================================================



    def test_migration_response_hides_internal_fields(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "get_batch",

            return_value=self.batch,

        ):

            response = self.client.get(

                self.detail_url()

            )



        body = (

            self.assert_success_contract(

                response

            )

        )



        migration = (

            body["data"][

                "migration"

            ]

        )



        self.assertNotIn(

            "organization",

            migration,

        )



        self.assertNotIn(

            "\_data",

            migration,

        )



        self.assertNotIn(

            "\_cls",

            migration,

        )





    # ==================================================

    # MIGRATION FILE UPLOAD

    # ==================================================



    def test_upload_migration_file_returns_201(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.csv",
            (
                b"sku,name\n"
                b"SKU-001,Product One\n"
                b"SKU-002,Product Two\n"
            ),
            content_type="text/csv",
        )

        upload = SimpleNamespace(
            id=ObjectId(),
            filename="products.csv",
            extension=".csv",
            size=len(uploaded_file.read()),
        )
        uploaded_file.seek(0)

        uploaded_batch = SimpleNamespace(
            **{
                **self.batch.__dict__,
                "status": "UPLOADED",
                "upload_id": str(upload.id),
            }
        )

        result = {
            "batch": uploaded_batch,
            "upload": upload,
            "file": {
                "columns": ["sku", "name"],
                "total_rows": 2,
                "sample_rows": [
                    {
                        "sku": "SKU-001",
                        "name": "Product One",
                    },
                    {
                        "sku": "SKU-002",
                        "name": "Product Two",
                    },
                ],
                "sheet_name": None,
            },
        }

        with patch.object(
            MigrationAPIService,
            "get_batch",
            return_value=self.batch,
        ) as get_mock:
            with patch.object(
                MigrationAPIService,
                "upload_file",
                return_value=result,
            ) as upload_mock:
                response = self.client.post(
                    self.upload_url(),
                    data={
                        "file": uploaded_file,
                    },
                )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["migration"]["status"],
            "UPLOADED",
        )
        self.assertEqual(
            body["data"]["file"]["filename"],
            "products.csv",
        )
        self.assertEqual(
            body["data"]["file"]["extension"],
            ".csv",
        )
        self.assertEqual(
            body["data"]["file"]["columns"],
            ["sku", "name"],
        )
        self.assertEqual(
            body["data"]["file"]["total_rows"],
            2,
        )
        self.assertEqual(
            len(body["data"]["file"]["sample_rows"]),
            2,
        )
        self.assertIsNone(
            body["data"]["file"]["sheet_name"]
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )
        upload_mock.assert_called_once()

        kwargs = upload_mock.call_args.kwargs

        self.assertIs(
            kwargs["user"],
            self.user,
        )
        self.assertIs(
            kwargs["batch"],
            self.batch,
        )
        self.assertEqual(
            kwargs["uploaded_file"].name,
            "products.csv",
        )

    def test_upload_migration_xlsx_returns_sheet_name(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.xlsx",
            b"fake-xlsx-content",
            content_type=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        upload = SimpleNamespace(
            id=ObjectId(),
            filename="products.xlsx",
            extension=".xlsx",
            size=17,
        )

        uploaded_batch = SimpleNamespace(
            **{
                **self.batch.__dict__,
                "status": "UPLOADED",
                "upload_id": str(upload.id),
            }
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            return_value=self.batch,
        ):
            with patch.object(
                MigrationAPIService,
                "upload_file",
                return_value={
                    "batch": uploaded_batch,
                    "upload": upload,
                    "file": {
                        "columns": [
                            "SKU",
                            "Name",
                        ],
                        "total_rows": 1,
                        "sample_rows": [
                            {
                                "SKU": "SKU-001",
                                "Name": "Product One",
                            },
                        ],
                        "sheet_name": "Products",
                    },
                },
            ):
                response = self.client.post(
                    self.upload_url(),
                    data={
                        "file": uploaded_file,
                    },
                )

        body = self.assert_success_contract(
            response,
            201,
        )

        self.assertEqual(
            body["data"]["file"]["extension"],
            ".xlsx",
        )
        self.assertEqual(
            body["data"]["file"]["sheet_name"],
            "Products",
        )

    def test_upload_migration_missing_file_is_rejected(
        self,
    ):
        validation_error = MigrationAPIValidationError(
            "Migration validation failed.",
            details={
                "file": [
                    "Migration file is required."
                ],
            },
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            return_value=self.batch,
        ):
            with patch.object(
                MigrationAPIService,
                "upload_file",
                side_effect=validation_error,
            ) as upload_mock:
                response = self.client.post(
                    self.upload_url(),
                    data={},
                )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "file",
            body["error"]["details"],
        )

        kwargs = upload_mock.call_args.kwargs
        self.assertIsNone(
            kwargs["uploaded_file"]
        )

    def test_upload_migration_invalid_file_is_rejected(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.txt",
            b"invalid",
            content_type="text/plain",
        )

        validation_error = MigrationAPIValidationError(
            "Migration validation failed.",
            details={
                "file": [
                    (
                        "Only CSV and XLSX migration "
                        "files are supported."
                    )
                ],
            },
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            return_value=self.batch,
        ):
            with patch.object(
                MigrationAPIService,
                "upload_file",
                side_effect=validation_error,
            ):
                response = self.client.post(
                    self.upload_url(),
                    data={
                        "file": uploaded_file,
                    },
                )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "file",
            body["error"]["details"],
        )

    def test_upload_migration_wrong_state_is_rejected(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.csv",
            b"sku,name\n1,Test\n",
            content_type="text/csv",
        )

        validation_error = MigrationAPIValidationError(
            "Migration validation failed.",
            details={
                "migration": [
                    (
                        "A file can only be uploaded "
                        "to a newly created migration."
                    )
                ],
            },
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            return_value=self.batch,
        ):
            with patch.object(
                MigrationAPIService,
                "upload_file",
                side_effect=validation_error,
            ):
                response = self.client.post(
                    self.upload_url(),
                    data={
                        "file": uploaded_file,
                    },
                )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "migration",
            body["error"]["details"],
        )

    def test_upload_missing_migration_returns_404(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.csv",
            b"sku,name\n1,Test\n",
            content_type="text/csv",
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            side_effect=LookupError(
                "Migration batch not found."
            ),
        ) as get_mock:
            with patch.object(
                MigrationAPIService,
                "upload_file",
            ) as upload_mock:
                response = self.client.post(
                    self.upload_url(),
                    data={
                        "file": uploaded_file,
                    },
                )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )
        upload_mock.assert_not_called()

    def test_upload_cross_tenant_migration_is_hidden(
        self,
    ):
        foreign_batch = SimpleNamespace(
            id=ObjectId(),
            organization=self.other_organization,
        )

        uploaded_file = SimpleUploadedFile(
            "products.csv",
            b"sku,name\n1,Test\n",
            content_type="text/csv",
        )

        with patch.object(
            MigrationAPIService,
            "get_batch",
            side_effect=LookupError(
                "Migration batch not found."
            ),
        ) as get_mock:
            with patch.object(
                MigrationAPIService,
                "upload_file",
            ) as upload_mock:
                response = self.client.post(
                    self.upload_url(
                        foreign_batch
                    ),
                    data={
                        "file": uploaded_file,
                    },
                )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(foreign_batch.id),
        )
        upload_mock.assert_not_called()

    def test_upload_migration_without_permission_is_forbidden(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.csv",
            b"sku,name\n1,Test\n",
            content_type="text/csv",
        )

        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            with patch.object(
                MigrationAPIService,
                "get_batch",
            ) as get_mock:
                with patch.object(
                    MigrationAPIService,
                    "upload_file",
                ) as upload_mock:
                    response = self.client.post(
                        self.upload_url(),
                        data={
                            "file": uploaded_file,
                        },
                    )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

        get_mock.assert_not_called()
        upload_mock.assert_not_called()

    def test_anonymous_migration_upload_is_rejected(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "products.csv",
            b"sku,name\n1,Test\n",
            content_type="text/csv",
        )

        with patch.object(
            APIOrganizationContextService,
            "resolve",
            side_effect=PermissionError(
                "Not authenticated."
            ),
        ):
            with patch.object(
                MigrationAPIService,
                "get_batch",
            ) as get_mock:
                with patch.object(
                    MigrationAPIService,
                    "upload_file",
                ) as upload_mock:
                    response = self.client.post(
                        self.upload_url(),
                        data={
                            "file": uploaded_file,
                        },
                    )

        self.assert_error_contract(
            response,
            401,
            "UNAUTHORIZED",
        )

        get_mock.assert_not_called()
        upload_mock.assert_not_called()

    def test_migration_upload_rejects_get(
        self,
    ):
        with patch.object(
            MigrationAPIService,
            "get_batch",
        ) as get_mock:
            with patch.object(
                MigrationAPIService,
                "upload_file",
            ) as upload_mock:
                response = self.client.get(
                    self.upload_url()
                )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

        get_mock.assert_not_called()
        upload_mock.assert_not_called()

    def test_validate_migration_returns_200(
        self,
    ):
        validation = {
            "migration_type": (
                self.batch.migration_type
            ),
            "total_rows": 3,
            "valid_rows": 3,
            "invalid_rows": 0,
            "mapping": {
                "product_sku": (
                    "Product SKU"
                ),
                "warehouse_code": (
                    "Warehouse Code"
                ),
                "quantity": (
                    "Opening Quantity"
                ),
            },
            "rows": [],
        }

        with patch.object(
            MigrationAPIService,
            "validate_batch",
            return_value={
                "batch": self.batch,
                "validation": validation,
            },
        ) as validate_mock:
            response = self.client.post(
                self.validate_url()
            )

        body = self.assert_success_contract(
            response,
            200,
        )

        self.assertEqual(
            body["data"]["migration"]["id"],
            str(self.batch.id),
        )

        self.assertEqual(
            body["data"]["validation"],
            validation,
        )

        validate_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )

        # ==================================================

        # MIGRATION VALIDATION

        # ==================================================



        def test_validate_migration_rejects_get(

            self,

        ):

            with patch.object(

                MigrationAPIService,

                "validate_batch",

            ) as validate_mock:

                response = self.client.get(

                    self.validate_url()

                )



            self.assert_error_contract(

                response,

                405,

                "METHOD_NOT_ALLOWED",

            )



            validate_mock.assert_not_called()



        def test_validate_migration_without_permission_is_forbidden(

            self,

        ):

            with patch.object(

                AuthorizationService,

                "has_permission",

                return_value=False,

            ):

                with patch.object(

                    MigrationAPIService,

                    "validate_batch",

                ) as validate_mock:

                    response = self.client.post(

                        self.validate_url()

                    )



            self.assert_error_contract(

                response,

                403,

                "FORBIDDEN",

            )



            validate_mock.assert_not_called()



        def test_anonymous_migration_validation_is_rejected(

            self,

        ):

            with patch.object(

                APIOrganizationContextService,

                "resolve",

                side_effect=PermissionError(

                    "Not authenticated."

                ),

            ):

                with patch.object(

                    MigrationAPIService,

                    "validate_batch",

                ) as validate_mock:

                    response = self.client.post(

                        self.validate_url()

                    )



            self.assert_error_contract(

                response,

                401,

                "UNAUTHORIZED",

            )



            validate_mock.assert_not_called()



        def test_validate_missing_migration_returns_404(

            self,

        ):

            with patch.object(

                MigrationAPIService,

                "validate_batch",

                side_effect=LookupError(

                    "Migration batch not found."

                ),

            ) as validate_mock:

                response = self.client.post(

                    self.validate_url()

                )



            self.assert_error_contract(

                response,

                404,

                "NOT_FOUND",

            )



            validate_mock.assert_called_once_with(

                organization=self.organization,

                batch_id=str(self.batch.id),

            )



        def test_validate_migration_validation_error_is_rejected(

            self,

        ):

            validation_error = (

                MigrationAPIValidationError(

                    "Migration validation failed.",

                    details={

                        "migration": [

                            (

                                "Migration cannot be "

                                "validated in its "

                                "current state."

                            )

                        ],

                    },

                )

            )



            with patch.object(

                MigrationAPIService,

                "validate_batch",

                side_effect=validation_error,

            ) as validate_mock:

                response = self.client.post(

                    self.validate_url()

                )



            body = self.assert_error_contract(

                response,

                400,

                "VALIDATION_ERROR",

            )



            self.assertIn(

                "migration",

                body["error"]["details"],

            )



            validate_mock.assert_called_once_with(

                organization=self.organization,

                batch_id=str(self.batch.id),

            )



        # ==================================================

        # MIGRATION IMPORT

        # ==================================================

    def test_import_migration_returns_200(
        self,
    ):
        import_result = {
            "migration_type": "INVENTORY",
            "imported_rows": 3,
            "skipped_rows": 0,
            "failed_rows": 0,
            "rows": [],
        }

        with patch.object(
            MigrationAPIService,
            "import_batch",
            return_value={
                "batch": self.batch,
                "import": import_result,
            },
        ) as import_mock:
            response = self.client.post(
                self.import_url()
            )

        body = self.assert_success_contract(
            response,
            200,
        )

        self.assertEqual(
            body["data"]["migration"]["id"],
            str(self.batch.id),
        )

        self.assertEqual(
            body["data"]["import"]["migration_type"],
            "INVENTORY",
        )

        self.assertEqual(
            body["data"]["import"]["imported_rows"],
            3,
        )

        self.assertEqual(
            body["data"]["import"]["skipped_rows"],
            0,
        )

        self.assertEqual(
            body["data"]["import"]["failed_rows"],
            0,
        )

        self.assertEqual(
            body["data"]["import"]["rows"],
            [],
        )

        self.assertEqual(
            body["message"],
            "Migration imported successfully.",
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )

    def test_import_migration_rejects_get(

        self,

    ):

        with patch.object(

            MigrationAPIService,

            "import_batch",

        ) as import_mock:

            response = self.client.get(

                self.import_url()

            )



        self.assert_error_contract(

            response,

            405,

            "METHOD_NOT_ALLOWED",

        )



        import_mock.assert_not_called()



    def test_import_migration_without_permission_is_forbidden(

        self,

    ):

        with patch.object(

            AuthorizationService,

            "has_permission",

            return_value=False,

        ):

            with patch.object(

                MigrationAPIService,

                "import_batch",

            ) as import_mock:

                response = self.client.post(

                    self.import_url()

                )



        self.assert_error_contract(

            response,

            403,

            "FORBIDDEN",

        )



        import_mock.assert_not_called()



    def test_anonymous_migration_import_is_rejected(

        self,

    ):

        with patch.object(

            APIOrganizationContextService,

            "resolve",

            side_effect=PermissionError(

                "Not authenticated."

            ),

        ):

            with patch.object(

                MigrationAPIService,

                "import_batch",

            ) as import_mock:

                response = self.client.post(

                    self.import_url()

                )



        self.assert_error_contract(

            response,

            401,

            "UNAUTHORIZED",

        )



        import_mock.assert_not_called()

    def test_import_missing_migration_returns_404(
        self,
    ):
        with patch.object(
            MigrationAPIService,
            "import_batch",
            side_effect=LookupError(
                "Migration batch not found."
            ),
        ) as import_mock:
            response = self.client.post(
                self.import_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )

    def test_import_migration_validation_error_is_rejected(
        self,
    ):
        validation_error = (
            MigrationAPIValidationError(
                "Migration import failed.",
                details={
                    "migration": [
                        (
                            "Migration is not ready "
                            "for import."
                        )
                    ],
                },
            )
        )

        with patch.object(
            MigrationAPIService,
            "import_batch",
            side_effect=validation_error,
        ) as import_mock:
            response = self.client.post(
                self.import_url()
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "migration",
            body["error"]["details"],
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch_id=str(self.batch.id),
        )