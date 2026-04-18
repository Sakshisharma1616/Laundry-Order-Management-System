"""Business-logic helper functions for the Laundry Order Management System.

Route handlers delegate all computation here, keeping them thin.
"""

from __future__ import annotations

from constants import UNIT_PRICES


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------


def calculate_total_bill(garments: list[dict]) -> float:
    """Sum (unit_price × quantity) for each garment.

    Args:
        garments: List of dicts with 'type' (str) and 'quantity' (int) keys.

    Returns:
        Total bill as a float.
    """
    return float(
        sum(UNIT_PRICES[garment["type"]] * garment["quantity"] for garment in garments)
    )


# ---------------------------------------------------------------------------
# Order filtering
# ---------------------------------------------------------------------------


def filter_orders(
    orders: list[dict],
    status: str | None,
    customer_name: str | None,
    phone: str | None,
) -> list[dict]:
    """Return orders that satisfy all provided filters simultaneously.

    Filter semantics:
    - status: exact match
    - customer_name: case-insensitive substring match
    - phone: exact match
    - A None value for any filter means that filter is not applied.

    Args:
        orders: All orders to search through.
        status: Optional status filter.
        customer_name: Optional customer name filter.
        phone: Optional phone filter.

    Returns:
        Subset of orders matching every non-None filter.
    """
    return [
        order for order in orders
        if _matches_status(order, status)
        and _matches_customer_name(order, customer_name)
        and _matches_phone(order, phone)
    ]


def _matches_status(order: dict, status: str | None) -> bool:
    """Return True if the order matches the status filter (or no filter is set)."""
    return status is None or order["status"] == status


def _matches_customer_name(order: dict, customer_name: str | None) -> bool:
    """Return True if the order matches the customer_name filter (case-insensitive substring)."""
    return customer_name is None or customer_name.lower() in order["customer_name"].lower()


def _matches_phone(order: dict, phone: str | None) -> bool:
    """Return True if the order matches the phone filter (exact match)."""
    return phone is None or order["phone"] == phone


# ---------------------------------------------------------------------------
# Dashboard metrics
# ---------------------------------------------------------------------------


def compute_dashboard(orders: list[dict]) -> dict:
    """Compute aggregated business metrics from a list of orders.

    Args:
        orders: All orders in the store.

    Returns:
        Dict with keys: total_orders, total_revenue, orders_per_status,
        average_order_value, most_common_garment.
    """
    total_orders = len(orders)

    if total_orders == 0:
        return _empty_dashboard()

    total_revenue = sum(order["total_bill"] for order in orders)
    orders_per_status = _count_orders_per_status(orders)
    average_order_value = round(total_revenue / total_orders, 2)
    most_common_garment = _find_most_common_garment(orders)

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "orders_per_status": orders_per_status,
        "average_order_value": average_order_value,
        "most_common_garment": most_common_garment,
    }


def _empty_dashboard() -> dict:
    """Return the zeroed dashboard response used when there are no orders."""
    return {
        "total_orders": 0,
        "total_revenue": 0,
        "orders_per_status": {},
        "average_order_value": 0,
        "most_common_garment": None,
    }


def _count_orders_per_status(orders: list[dict]) -> dict[str, int]:
    """Count how many orders are in each status."""
    counts: dict[str, int] = {}
    for order in orders:
        status = order["status"]
        counts[status] = counts.get(status, 0) + 1
    return counts


def _find_most_common_garment(orders: list[dict]) -> str | None:
    """Return the garment type with the highest total quantity across all orders.

    Returns None when there are no garments at all (e.g. all orders have
    empty garment lists, which should not happen in practice).
    """
    totals: dict[str, int] = {}
    for order in orders:
        for garment in order["garments"]:
            gtype = garment["type"]
            totals[gtype] = totals.get(gtype, 0) + garment["quantity"]

    return max(totals, key=lambda g: totals[g]) if totals else None
