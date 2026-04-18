"""Input validation functions for the Laundry Order Management System.

Each function returns a list of human-readable error strings.
An empty list means the input is valid.
"""

from __future__ import annotations

from constants import UNIT_PRICES, VALID_STATUSES, STATUS_TRANSITIONS

# Fields that every create-order payload must contain
_REQUIRED_ORDER_FIELDS = ("customer_name", "phone", "garments")

# Fields that every garment entry must contain
_REQUIRED_GARMENT_FIELDS = ("type", "quantity")


# ---------------------------------------------------------------------------
# Order creation validation
# ---------------------------------------------------------------------------


def validate_create_order_payload(payload: dict) -> list[str]:
    """Validate the payload for POST /orders.

    Checks required top-level fields, garments list, and each garment entry.

    Returns:
        List of error messages; empty list means the payload is valid.
    """
    errors: list[str] = []

    # Check required top-level fields
    for field in _REQUIRED_ORDER_FIELDS:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    # Cannot validate garment contents if the field is absent
    if "garments" not in payload:
        return errors

    errors.extend(_validate_garments_list(payload["garments"]))
    return errors


def _validate_garments_list(garments: object) -> list[str]:
    """Validate the garments field: must be a non-empty list of valid entries."""
    if not isinstance(garments, list) or len(garments) == 0:
        return ["At least one garment is required"]

    errors: list[str] = []
    for index, garment in enumerate(garments):
        errors.extend(_validate_garment_entry(index, garment))
    return errors


def _validate_garment_entry(index: int, garment: object) -> list[str]:
    """Validate a single garment dict at the given list index."""
    if not isinstance(garment, dict):
        return [f"Garment at index {index} must be an object"]

    errors: list[str] = []

    # Check for missing sub-fields; skip further checks if any are absent
    missing = [f for f in _REQUIRED_GARMENT_FIELDS if f not in garment]
    if missing:
        for field in missing:
            errors.append(f"Garment at index {index} is missing required field: {field}")
        return errors

    errors.extend(_validate_garment_type(garment["type"]))
    errors.extend(_validate_garment_quantity(garment["quantity"]))
    return errors


def _validate_garment_type(garment_type: object) -> list[str]:
    """Validate that garment_type is one of the supported types."""
    valid_types = list(UNIT_PRICES.keys())
    if garment_type not in valid_types:
        supported = ", ".join(valid_types)
        return [f"Invalid garment type '{garment_type}'. Supported types: {supported}"]
    return []


def _validate_garment_quantity(quantity: object) -> list[str]:
    """Validate that quantity is a positive integer (booleans are rejected)."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return ["Quantity must be a positive integer"]
    return []


# ---------------------------------------------------------------------------
# Status validation
# ---------------------------------------------------------------------------


def validate_status_value(status: str) -> list[str]:
    """Validate that status is one of the allowed status values.

    Returns:
        List with one error message if invalid; empty list if valid.
    """
    if status not in VALID_STATUSES:
        valid_str = ", ".join(VALID_STATUSES)
        return [f"Invalid status '{status}'. Valid statuses: {valid_str}"]
    return []


def validate_status_transition(current: str, next_status: str) -> list[str]:
    """Validate that transitioning from current to next_status is permitted.

    Returns:
        List with one error message if the transition is not allowed;
        empty list if the transition is valid.
    """
    if current not in STATUS_TRANSITIONS:
        # DELIVERED (or any unknown status) has no valid successor
        return [
            f"Cannot transition from {current} to {next_status}."
            " No further transitions are allowed"
        ]

    allowed_next = STATUS_TRANSITIONS[current]
    if allowed_next != next_status:
        return [
            f"Cannot transition from {current} to {next_status}."
            f" Allowed next status: {allowed_next}"
        ]

    return []
