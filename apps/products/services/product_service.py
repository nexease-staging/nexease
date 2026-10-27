from decimal import Decimal
from apps.authorization.services import AuthorizationService
from mongoengine.errors import NotUniqueError

from apps.products.models import Product, Category

from apps.products.repositories.product_repository import (
    ProductRepository,
)
class ProductService:
    @staticmethod
    def _check_permission(user, permission_code):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
            )
        
    @staticmethod
    def create_product(
        *,
        user,
        organization,
        sku,
        name,
        category,
        unit,
        cost_price=0,
        selling_price=0,
        description="",
        brand="",
        barcode="",
    ):
        ProductService._check_permission(
            user,
            "products.create",
        )
        """
        Create a new product for an organization.
        """

        if not organization:
            raise ValueError("Organization is required.")

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        if not sku:
            raise ValueError("SKU is required.")

        if not name:
            raise ValueError("Product name is required.")

        if not category:
            raise ValueError("Category is required.")

        if category.organization.id != organization.id:
            raise ValueError(
                "Category does not belong to this organization."
            )

        cost_price = Decimal(str(cost_price))
        selling_price = Decimal(str(selling_price))

        if cost_price < 0:
            raise ValueError(
                "Cost price cannot be negative."
            )

        if selling_price < 0:
            raise ValueError(
                "Selling price cannot be negative."
            )

        product = Product(
            organization=organization,
            sku=sku,
            name=name,
            description=description,
            category=category,
            brand=brand,
            unit=unit,
            cost_price=cost_price,
            selling_price=selling_price,
            barcode=barcode,
        )

        try:
            product.save()
        except NotUniqueError:
            raise ValueError(
                f"Product with SKU '{sku}' already exists "
                "in this organization."
            )

        return product

    @staticmethod
    def get_product(*, user, organization, product_id):
        """
        Retrieve a product belonging to an organization.
        """
        ProductService._check_permission(
            user,
            "products.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organisation."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )
        
        product = ProductRepository.get_by_id(
            organization=organization,
            product_id=product_id,
        )

        if not product:
            raise ValueError("Product not found.")

        return product

    @staticmethod
    def get_product_by_sku(*, user, organization, sku):
        """
        Retrieve a product by SKU.
        """
        ProductService._check_permission(
            user,
            "products.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )
        
        product = ProductRepository.get_by_sku(
            organization=organization,
            sku=sku,
        )

        if not product:
            raise ValueError(
                f"Product with SKU '{sku}' was not found."
            )

        return product

    @staticmethod
    def update_product(
        *,
        user,
        organization,
        product_id,
        name=None,
        description=None,
        category=None,
        brand=None,
        unit=None,
        cost_price=None,
        selling_price=None,
        barcode=None,
    ):
        """
        Update product information.
        """
        ProductService._check_permission(
            user,
            "products.update"
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )
        
        product = ProductRepository.get_by_id(
            organization=organization,
            product_id=product_id,
        )

        if not product:
            raise ValueError("Product not found.")

        if not product.is_active:
            raise ValueError(
                "Inactive product cannot be updated. "
                "Activate the product first."
            )

        if name is not None:
            if not name.strip():
                raise ValueError("Product name cannot be empty.")

            product.name = name.strip()

        if description is not None:
            product.description = description

        if category is not None:

            if category.organization.id != organization.id:
                raise ValueError(
                    "Category does not belong to this organization."
                )

            product.category = category

        if brand is not None:
            product.brand = brand

        if unit is not None:
            product.unit = unit

        if cost_price is not None:

            cost_price = Decimal(str(cost_price))

            if cost_price < 0:
                raise ValueError(
                    "Cost price cannot be negative."
                )

            product.cost_price = cost_price

        if selling_price is not None:

            selling_price = Decimal(str(selling_price))

            if selling_price < 0:
                raise ValueError(
                    "Selling price cannot be negative."
                )

            product.selling_price = selling_price

        if barcode is not None:
            product.barcode = barcode

        product.save()

        return product

    @staticmethod
    def deactivate_product(*, user, organization, product_id):
        """
        Deactivate a product without deleting it.
        """
        ProductService._check_permission(
            user,
            "products.delete"
        )

        product = ProductRepository.get_by_id(
            organization=organization,
            product_id=product_id,
        )

        if not product:
            raise ValueError("Product not found.")


        if not product.is_active:
            raise ValueError("Product is already inactive.")

        product.is_active = False
        product.save()

        return product

    @staticmethod
    def activate_product(
        *,
        user,
        organization,
        product_id,
    ):
        ProductService._check_permission(
            user,
            "products.update",
        )

        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        product = ProductRepository.get_by_id(
            organization=organization,
            product_id=product_id,
        )

        if not product:
            raise ValueError(
                "Product not found."
            )

        if product.is_active:
            raise ValueError(
                "Product is already active."
            )

        product.is_active = True
        product.save()

        return product

    @staticmethod
    def list_products(
        *,
        user,
        organization,
        search_term=None,
        active_only=False,
    ):
        """
        Return products belonging to an organization.

        Supports:
        - all products
        - active-only products
        - name search
        - name search + active-only filtering
        """

        ProductService._check_permission(
            user,
            "products.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organisation."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        if search_term:
            products = ProductRepository.search_by_name(
                organization=organization,
                search_term=search_term,
            )
        else:
            products = ProductRepository.list_by_organization(
                organization=organization,
            )

        if active_only:
            products = products.filter(
                is_active=True
            )

        return products
    
    @staticmethod
    def list_active_products(*, user, organization):
        """
        Return active products only.
        """

        ProductService._check_permission(
            user,
            "products.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        return ProductRepository.list_active(
            organization=organization,
        )

    @staticmethod
    def search_products(
        *,
        user,
        organization,
        search_term,
    ):
        """
        Search products by SKU or name.
        """

        ProductService._check_permission(
            user,
            "products.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        return ProductRepository.search(
            organization=organization,
            search_term=search_term,
        )