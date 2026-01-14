"""
Shopify Integration Nodes - E-commerce operations.

Uses Shopify Admin REST API with Access Token authentication.
"""

from typing import Optional

import httpx

from src.core.nodes.base import BaseNode, NodeField, FieldType


def _get_credential(credential_id: Optional[str]) -> Optional[dict]:
    """Load credential from vault if ID is provided."""
    if not credential_id:
        return None
    try:
        from src.data.credentials import CredentialVault
        vault = CredentialVault()
        cred = vault.get_credential(credential_id)
        if cred:
            return cred.get("data", {})
    except Exception:
        pass
    return None


def _get_auth(config: dict) -> tuple[str, str]:
    """Get shop domain and access token from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        shop = cred_data.get("shop", "")
        access_token = cred_data.get("access_token", "")
    else:
        shop = config.get("shop", "")
        access_token = config.get("access_token", "")

    return shop, access_token


def _get_base_url(shop: str) -> str:
    """Get base URL for Shopify API."""
    # Handle both full domain and shop name
    if ".myshopify.com" in shop:
        return f"https://{shop}/admin/api/2024-01"
    return f"https://{shop}.myshopify.com/admin/api/2024-01"


class ShopifyListProductsNode(BaseNode):
    """List products from Shopify store."""

    type = "shopify-list-products"
    name = "Shopify: List Products"
    category = "Apps"
    description = "List products from your Shopify store"
    icon = "package"
    color = "#96BF48"  # Shopify green

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name (e.g., 'mystore' or 'mystore.myshopify.com').",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Number of products to retrieve (max 250).",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "active", "label": "Active"},
                {"value": "archived", "label": "Archived"},
                {"value": "draft", "label": "Draft"},
            ],
            description="Filter by product status.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="products", label="Products", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify list products node."""
        shop, access_token = _get_auth(config)
        limit = min(config.get("limit", 50), 250)
        status = config.get("status", "")

        if not shop:
            raise ValueError("Shop is required")

        base_url = _get_base_url(shop)
        params = {"limit": limit}
        if status:
            params["status"] = status

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/products.json",
                    params=params,
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    return {
                        "success": True,
                        "products": products,
                        "count": len(products),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "products": [],
                        "count": 0,
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "products": [],
                "count": 0,
                "error": str(e),
            }


class ShopifyGetProductNode(BaseNode):
    """Get a product from Shopify."""

    type = "shopify-get-product"
    name = "Shopify: Get Product"
    category = "Apps"
    description = "Get a product by ID from Shopify"
    icon = "package"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="product_id",
            label="Product ID",
            type=FieldType.STRING,
            required=True,
            description="Shopify product ID.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="product", label="Product", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify get product node."""
        shop, access_token = _get_auth(config)
        product_id = config.get("product_id", "")

        if not shop:
            raise ValueError("Shop is required")
        if not product_id:
            raise ValueError("Product ID is required")

        base_url = _get_base_url(shop)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/products/{product_id}.json",
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "product": data.get("product", {}),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "product": {},
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "product": {},
                "error": str(e),
            }


class ShopifyListOrdersNode(BaseNode):
    """List orders from Shopify store."""

    type = "shopify-list-orders"
    name = "Shopify: List Orders"
    category = "Apps"
    description = "List orders from your Shopify store"
    icon = "shopping-cart"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Number of orders to retrieve (max 250).",
        ),
        NodeField(
            name="status",
            label="Status",
            type=FieldType.SELECT,
            required=False,
            default="any",
            options=[
                {"value": "any", "label": "Any"},
                {"value": "open", "label": "Open"},
                {"value": "closed", "label": "Closed"},
                {"value": "cancelled", "label": "Cancelled"},
            ],
            description="Filter by order status.",
        ),
        NodeField(
            name="financial_status",
            label="Financial Status",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "pending", "label": "Pending"},
                {"value": "authorized", "label": "Authorized"},
                {"value": "paid", "label": "Paid"},
                {"value": "refunded", "label": "Refunded"},
                {"value": "voided", "label": "Voided"},
            ],
            description="Filter by financial status.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="orders", label="Orders", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify list orders node."""
        shop, access_token = _get_auth(config)
        limit = min(config.get("limit", 50), 250)
        status = config.get("status", "any")
        financial_status = config.get("financial_status", "")

        if not shop:
            raise ValueError("Shop is required")

        base_url = _get_base_url(shop)
        params = {"limit": limit, "status": status}
        if financial_status:
            params["financial_status"] = financial_status

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/orders.json",
                    params=params,
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("orders", [])
                    return {
                        "success": True,
                        "orders": orders,
                        "count": len(orders),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "orders": [],
                        "count": 0,
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "orders": [],
                "count": 0,
                "error": str(e),
            }


class ShopifyGetOrderNode(BaseNode):
    """Get an order from Shopify."""

    type = "shopify-get-order"
    name = "Shopify: Get Order"
    category = "Apps"
    description = "Get an order by ID from Shopify"
    icon = "shopping-cart"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="order_id",
            label="Order ID",
            type=FieldType.STRING,
            required=True,
            description="Shopify order ID.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="order", label="Order", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify get order node."""
        shop, access_token = _get_auth(config)
        order_id = config.get("order_id", "")

        if not shop:
            raise ValueError("Shop is required")
        if not order_id:
            raise ValueError("Order ID is required")

        base_url = _get_base_url(shop)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/orders/{order_id}.json",
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "order": data.get("order", {}),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "order": {},
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "order": {},
                "error": str(e),
            }


class ShopifyListCustomersNode(BaseNode):
    """List customers from Shopify store."""

    type = "shopify-list-customers"
    name = "Shopify: List Customers"
    category = "Apps"
    description = "List customers from your Shopify store"
    icon = "users"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=50,
            description="Number of customers to retrieve (max 250).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="customers", label="Customers", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify list customers node."""
        shop, access_token = _get_auth(config)
        limit = min(config.get("limit", 50), 250)

        if not shop:
            raise ValueError("Shop is required")

        base_url = _get_base_url(shop)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/customers.json",
                    params={"limit": limit},
                    headers={"X-Shopify-Access-Token": access_token},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    customers = data.get("customers", [])
                    return {
                        "success": True,
                        "customers": customers,
                        "count": len(customers),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "customers": [],
                        "count": 0,
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "customers": [],
                "count": 0,
                "error": str(e),
            }


class ShopifyCreateCustomerNode(BaseNode):
    """Create a customer in Shopify."""

    type = "shopify-create-customer"
    name = "Shopify: Create Customer"
    category = "Apps"
    description = "Create a new customer in Shopify"
    icon = "user-plus"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Customer email address.",
        ),
        NodeField(
            name="first_name",
            label="First Name",
            type=FieldType.STRING,
            required=False,
            description="Customer first name.",
        ),
        NodeField(
            name="last_name",
            label="Last Name",
            type=FieldType.STRING,
            required=False,
            description="Customer last name.",
        ),
        NodeField(
            name="phone",
            label="Phone",
            type=FieldType.STRING,
            required=False,
            description="Customer phone number.",
        ),
        NodeField(
            name="tags",
            label="Tags",
            type=FieldType.STRING,
            required=False,
            description="Comma-separated tags for the customer.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="customer_id", label="Customer ID", type=FieldType.STRING),
        NodeField(name="customer", label="Customer", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify create customer node."""
        shop, access_token = _get_auth(config)
        email = config.get("email", "")
        first_name = config.get("first_name", "")
        last_name = config.get("last_name", "")
        phone = config.get("phone", "")
        tags = config.get("tags", "")

        if not shop:
            raise ValueError("Shop is required")
        if not email:
            raise ValueError("Email is required")

        base_url = _get_base_url(shop)

        # Build customer data
        customer_data = {"email": email}
        if first_name:
            customer_data["first_name"] = first_name
        if last_name:
            customer_data["last_name"] = last_name
        if phone:
            customer_data["phone"] = phone
        if tags:
            customer_data["tags"] = tags

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/customers.json",
                    json={"customer": customer_data},
                    headers={
                        "X-Shopify-Access-Token": access_token,
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 201:
                    data = response.json()
                    customer = data.get("customer", {})
                    return {
                        "success": True,
                        "customer_id": str(customer.get("id", "")),
                        "customer": customer,
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "customer_id": "",
                        "customer": {},
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "customer_id": "",
                "customer": {},
                "error": str(e),
            }


class ShopifyUpdateInventoryNode(BaseNode):
    """Update inventory level in Shopify."""

    type = "shopify-update-inventory"
    name = "Shopify: Update Inventory"
    category = "Apps"
    description = "Update inventory level for a product variant"
    icon = "box"
    color = "#96BF48"

    inputs = [
        NodeField(
            name="credential",
            label="Shopify Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Shopify credential.",
            credential_service="shopify",
        ),
        NodeField(
            name="shop",
            label="Shop",
            type=FieldType.STRING,
            required=False,
            description="Shop name.",
        ),
        NodeField(
            name="access_token",
            label="Access Token",
            type=FieldType.SECRET,
            required=False,
            description="Shopify Admin API access token.",
        ),
        NodeField(
            name="inventory_item_id",
            label="Inventory Item ID",
            type=FieldType.STRING,
            required=True,
            description="Shopify inventory item ID.",
        ),
        NodeField(
            name="location_id",
            label="Location ID",
            type=FieldType.STRING,
            required=True,
            description="Shopify location ID.",
        ),
        NodeField(
            name="adjustment",
            label="Adjustment",
            type=FieldType.NUMBER,
            required=True,
            description="Quantity adjustment (positive or negative).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="available", label="Available", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Shopify update inventory node."""
        shop, access_token = _get_auth(config)
        inventory_item_id = config.get("inventory_item_id", "")
        location_id = config.get("location_id", "")
        adjustment = config.get("adjustment", 0)

        if not shop:
            raise ValueError("Shop is required")
        if not inventory_item_id:
            raise ValueError("Inventory Item ID is required")
        if not location_id:
            raise ValueError("Location ID is required")

        base_url = _get_base_url(shop)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/inventory_levels/adjust.json",
                    json={
                        "inventory_item_id": int(inventory_item_id),
                        "location_id": int(location_id),
                        "available_adjustment": int(adjustment),
                    },
                    headers={
                        "X-Shopify-Access-Token": access_token,
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    inventory_level = data.get("inventory_level", {})
                    return {
                        "success": True,
                        "available": inventory_level.get("available", 0),
                        "error": "",
                    }
                else:
                    return {
                        "success": False,
                        "available": 0,
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "success": False,
                "available": 0,
                "error": str(e),
            }
