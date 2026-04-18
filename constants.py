"""Shared constants for the Laundry Order Management System.

Keeping constants in a dedicated module breaks the circular import that would
otherwise arise when validators.py and helpers.py import from app.py.
"""

# Pricing per garment type (in currency units)
UNIT_PRICES: dict[str, int] = {
    "Shirt": 50,
    "Pants": 80,
    "Saree": 100,
}

# Ordered list of valid order statuses
VALID_STATUSES: list[str] = ["RECEIVED", "PROCESSING", "READY", "DELIVERED"]

# Allowed one-step transitions: each status maps to its single valid successor.
# DELIVERED is intentionally absent — it has no valid next status.
STATUS_TRANSITIONS: dict[str, str] = {
    "RECEIVED": "PROCESSING",
    "PROCESSING": "READY",
    "READY": "DELIVERED",
}
