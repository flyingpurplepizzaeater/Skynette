"""
Stripe Integration Nodes - Payment processing.

Uses Stripe REST API with Secret Key authentication.
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


def _get_api_key(config: dict) -> str:
    """Get API key from config or credential."""
    credential_id = config.get("credential")
    cred_data = _get_credential(credential_id) if credential_id else None

    if cred_data:
        return cred_data.get("secret_key", "")
    return config.get("secret_key", "")


class StripeCreateCustomerNode(BaseNode):
    """Create a customer in Stripe."""

    type = "stripe-create-customer"
    name = "Stripe: Create Customer"
    category = "Apps"
    description = "Create a new customer in Stripe"
    icon = "user-plus"
    color = "#635BFF"  # Stripe purple

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key (sk_...).",
        ),
        NodeField(
            name="email",
            label="Email",
            type=FieldType.STRING,
            required=True,
            description="Customer email address.",
        ),
        NodeField(
            name="name",
            label="Name",
            type=FieldType.STRING,
            required=False,
            description="Customer full name.",
        ),
        NodeField(
            name="phone",
            label="Phone",
            type=FieldType.STRING,
            required=False,
            description="Customer phone number.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.STRING,
            required=False,
            description="Description for the customer.",
        ),
        NodeField(
            name="metadata",
            label="Metadata",
            type=FieldType.JSON,
            required=False,
            default={},
            description="Additional metadata (JSON object).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="customer_id", label="Customer ID", type=FieldType.STRING),
        NodeField(name="customer", label="Customer", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe create customer node."""
        api_key = _get_api_key(config)
        email = config.get("email", "")
        name = config.get("name", "")
        phone = config.get("phone", "")
        description = config.get("description", "")
        metadata = config.get("metadata", {})

        if not email:
            raise ValueError("Email is required")

        # Build form data
        data = {"email": email}
        if name:
            data["name"] = name
        if phone:
            data["phone"] = phone
        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = str(value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/customers",
                    data=data,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    customer = response.json()
                    return {
                        "success": True,
                        "customer_id": customer.get("id", ""),
                        "customer": customer,
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "customer_id": "",
                        "customer": {},
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "customer_id": "",
                "customer": {},
                "error": str(e),
            }


class StripeGetCustomerNode(BaseNode):
    """Get a customer from Stripe."""

    type = "stripe-get-customer"
    name = "Stripe: Get Customer"
    category = "Apps"
    description = "Retrieve a customer from Stripe"
    icon = "user"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="customer_id",
            label="Customer ID",
            type=FieldType.STRING,
            required=True,
            description="Stripe customer ID (cus_...).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="customer", label="Customer", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe get customer node."""
        api_key = _get_api_key(config)
        customer_id = config.get("customer_id", "")

        if not customer_id:
            raise ValueError("Customer ID is required")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.stripe.com/v1/customers/{customer_id}",
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    customer = response.json()
                    return {
                        "success": True,
                        "customer": customer,
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "customer": {},
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "customer": {},
                "error": str(e),
            }


class StripeCreatePaymentIntentNode(BaseNode):
    """Create a payment intent in Stripe."""

    type = "stripe-create-payment-intent"
    name = "Stripe: Create Payment Intent"
    category = "Apps"
    description = "Create a payment intent for processing payments"
    icon = "credit-card"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="amount",
            label="Amount",
            type=FieldType.NUMBER,
            required=True,
            description="Amount in cents (e.g., 1000 = $10.00).",
        ),
        NodeField(
            name="currency",
            label="Currency",
            type=FieldType.STRING,
            required=True,
            default="usd",
            description="Three-letter ISO currency code (e.g., usd, eur).",
        ),
        NodeField(
            name="customer_id",
            label="Customer ID",
            type=FieldType.STRING,
            required=False,
            description="Stripe customer ID to attach to the payment.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.STRING,
            required=False,
            description="Description for the payment.",
        ),
        NodeField(
            name="metadata",
            label="Metadata",
            type=FieldType.JSON,
            required=False,
            default={},
            description="Additional metadata (JSON object).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="payment_intent_id", label="Payment Intent ID", type=FieldType.STRING),
        NodeField(name="client_secret", label="Client Secret", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe create payment intent node."""
        api_key = _get_api_key(config)
        amount = config.get("amount", 0)
        currency = config.get("currency", "usd")
        customer_id = config.get("customer_id", "")
        description = config.get("description", "")
        metadata = config.get("metadata", {})

        if not amount or amount <= 0:
            raise ValueError("Amount must be greater than 0")

        # Build form data
        data = {
            "amount": int(amount),
            "currency": currency.lower(),
        }
        if customer_id:
            data["customer"] = customer_id
        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = str(value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/payment_intents",
                    data=data,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    intent = response.json()
                    return {
                        "success": True,
                        "payment_intent_id": intent.get("id", ""),
                        "client_secret": intent.get("client_secret", ""),
                        "status": intent.get("status", ""),
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "payment_intent_id": "",
                        "client_secret": "",
                        "status": "",
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "payment_intent_id": "",
                "client_secret": "",
                "status": "",
                "error": str(e),
            }


class StripeListChargesNode(BaseNode):
    """List charges from Stripe."""

    type = "stripe-list-charges"
    name = "Stripe: List Charges"
    category = "Apps"
    description = "List recent charges from Stripe"
    icon = "list"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="customer_id",
            label="Customer ID",
            type=FieldType.STRING,
            required=False,
            description="Filter by customer ID.",
        ),
        NodeField(
            name="limit",
            label="Limit",
            type=FieldType.NUMBER,
            required=False,
            default=10,
            description="Number of charges to retrieve (max 100).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="charges", label="Charges", type=FieldType.JSON),
        NodeField(name="count", label="Count", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe list charges node."""
        api_key = _get_api_key(config)
        customer_id = config.get("customer_id", "")
        limit = config.get("limit", 10)

        params = {"limit": min(int(limit), 100)}
        if customer_id:
            params["customer"] = customer_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.stripe.com/v1/charges",
                    params=params,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    charges = data.get("data", [])
                    return {
                        "success": True,
                        "charges": charges,
                        "count": len(charges),
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "charges": [],
                        "count": 0,
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "charges": [],
                "count": 0,
                "error": str(e),
            }


class StripeCreateInvoiceNode(BaseNode):
    """Create an invoice in Stripe."""

    type = "stripe-create-invoice"
    name = "Stripe: Create Invoice"
    category = "Apps"
    description = "Create an invoice for a customer"
    icon = "file-text"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="customer_id",
            label="Customer ID",
            type=FieldType.STRING,
            required=True,
            description="Stripe customer ID.",
        ),
        NodeField(
            name="auto_advance",
            label="Auto Advance",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Whether to automatically finalize and send.",
        ),
        NodeField(
            name="collection_method",
            label="Collection Method",
            type=FieldType.SELECT,
            required=False,
            default="charge_automatically",
            options=[
                {"value": "charge_automatically", "label": "Charge Automatically"},
                {"value": "send_invoice", "label": "Send Invoice"},
            ],
            description="How to collect payment.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.STRING,
            required=False,
            description="Description for the invoice.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="invoice_id", label="Invoice ID", type=FieldType.STRING),
        NodeField(name="invoice_url", label="Invoice URL", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe create invoice node."""
        api_key = _get_api_key(config)
        customer_id = config.get("customer_id", "")
        auto_advance = config.get("auto_advance", True)
        collection_method = config.get("collection_method", "charge_automatically")
        description = config.get("description", "")

        if not customer_id:
            raise ValueError("Customer ID is required")

        # Build form data
        data = {
            "customer": customer_id,
            "auto_advance": str(auto_advance).lower(),
            "collection_method": collection_method,
        }
        if description:
            data["description"] = description

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/invoices",
                    data=data,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    invoice = response.json()
                    return {
                        "success": True,
                        "invoice_id": invoice.get("id", ""),
                        "invoice_url": invoice.get("hosted_invoice_url", ""),
                        "status": invoice.get("status", ""),
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "invoice_id": "",
                        "invoice_url": "",
                        "status": "",
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "invoice_id": "",
                "invoice_url": "",
                "status": "",
                "error": str(e),
            }


class StripeCreateProductNode(BaseNode):
    """Create a product in Stripe."""

    type = "stripe-create-product"
    name = "Stripe: Create Product"
    category = "Apps"
    description = "Create a product in Stripe"
    icon = "package"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="name",
            label="Name",
            type=FieldType.STRING,
            required=True,
            description="Product name.",
        ),
        NodeField(
            name="description",
            label="Description",
            type=FieldType.STRING,
            required=False,
            description="Product description.",
        ),
        NodeField(
            name="active",
            label="Active",
            type=FieldType.BOOLEAN,
            required=False,
            default=True,
            description="Whether the product is active.",
        ),
        NodeField(
            name="metadata",
            label="Metadata",
            type=FieldType.JSON,
            required=False,
            default={},
            description="Additional metadata (JSON object).",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="product_id", label="Product ID", type=FieldType.STRING),
        NodeField(name="product", label="Product", type=FieldType.JSON),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe create product node."""
        api_key = _get_api_key(config)
        name = config.get("name", "")
        description = config.get("description", "")
        active = config.get("active", True)
        metadata = config.get("metadata", {})

        if not name:
            raise ValueError("Product name is required")

        # Build form data
        data = {
            "name": name,
            "active": str(active).lower(),
        }
        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = str(value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/products",
                    data=data,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    product = response.json()
                    return {
                        "success": True,
                        "product_id": product.get("id", ""),
                        "product": product,
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "product_id": "",
                        "product": {},
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "product_id": "",
                "product": {},
                "error": str(e),
            }


class StripeCreateRefundNode(BaseNode):
    """Create a refund in Stripe."""

    type = "stripe-create-refund"
    name = "Stripe: Create Refund"
    category = "Apps"
    description = "Create a refund for a charge or payment intent"
    icon = "rotate-ccw"
    color = "#635BFF"

    inputs = [
        NodeField(
            name="credential",
            label="Stripe Credential",
            type=FieldType.CREDENTIAL,
            required=False,
            description="Select a saved Stripe credential.",
            credential_service="stripe",
        ),
        NodeField(
            name="secret_key",
            label="Secret Key",
            type=FieldType.SECRET,
            required=False,
            description="Stripe secret key.",
        ),
        NodeField(
            name="charge_id",
            label="Charge ID",
            type=FieldType.STRING,
            required=False,
            description="Charge ID to refund (ch_...).",
        ),
        NodeField(
            name="payment_intent_id",
            label="Payment Intent ID",
            type=FieldType.STRING,
            required=False,
            description="Payment Intent ID to refund (pi_...).",
        ),
        NodeField(
            name="amount",
            label="Amount",
            type=FieldType.NUMBER,
            required=False,
            description="Amount to refund in cents (leave empty for full refund).",
        ),
        NodeField(
            name="reason",
            label="Reason",
            type=FieldType.SELECT,
            required=False,
            options=[
                {"value": "duplicate", "label": "Duplicate"},
                {"value": "fraudulent", "label": "Fraudulent"},
                {"value": "requested_by_customer", "label": "Requested by Customer"},
            ],
            description="Reason for the refund.",
        ),
    ]

    outputs = [
        NodeField(name="success", label="Success", type=FieldType.BOOLEAN),
        NodeField(name="refund_id", label="Refund ID", type=FieldType.STRING),
        NodeField(name="status", label="Status", type=FieldType.STRING),
        NodeField(name="amount", label="Amount", type=FieldType.NUMBER),
        NodeField(name="error", label="Error", type=FieldType.STRING),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Execute the Stripe create refund node."""
        api_key = _get_api_key(config)
        charge_id = config.get("charge_id", "")
        payment_intent_id = config.get("payment_intent_id", "")
        amount = config.get("amount")
        reason = config.get("reason", "")

        if not charge_id and not payment_intent_id:
            raise ValueError("Either Charge ID or Payment Intent ID is required")

        # Build form data
        data = {}
        if charge_id:
            data["charge"] = charge_id
        if payment_intent_id:
            data["payment_intent"] = payment_intent_id
        if amount and amount > 0:
            data["amount"] = int(amount)
        if reason:
            data["reason"] = reason

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/refunds",
                    data=data,
                    auth=(api_key, ""),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    refund = response.json()
                    return {
                        "success": True,
                        "refund_id": refund.get("id", ""),
                        "status": refund.get("status", ""),
                        "amount": refund.get("amount", 0),
                        "error": "",
                    }
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "refund_id": "",
                        "status": "",
                        "amount": 0,
                        "error": error_msg,
                    }

        except Exception as e:
            return {
                "success": False,
                "refund_id": "",
                "status": "",
                "amount": 0,
                "error": str(e),
            }
