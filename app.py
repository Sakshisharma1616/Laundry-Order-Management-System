"""Laundry Order Management System — Flask application.

Route handlers are intentionally thin: they parse the request, delegate to
validators and helpers, then wrap the result in the standard envelope.
"""

import uuid
from datetime import date, timedelta

from flask import Flask, jsonify, request, send_from_directory

from constants import UNIT_PRICES, VALID_STATUSES, STATUS_TRANSITIONS
from helpers import calculate_total_bill, compute_dashboard, filter_orders
from validators import (
    validate_create_order_payload,
    validate_status_transition,
    validate_status_value,
)

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------

# Maps order_id (str) → order dict.  Cleared between test runs via conftest.
order_store: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder="static")


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Serve the single-page frontend."""
    return send_from_directory("static", "index.html")


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def success(data, status_code: int = 200):
    """Wrap data in the standard success envelope."""
    return jsonify({"data": data}), status_code


def error(message: str, status_code: int):
    """Wrap a message in the standard error envelope."""
    return jsonify({"error": message}), status_code


def join_errors(errors: list[str]) -> str:
    """Join multiple validation error messages into a single string."""
    return "; ".join(errors)


# ---------------------------------------------------------------------------
# Order creation
# ---------------------------------------------------------------------------


@app.route("/orders", methods=["POST"])
def create_order():
    """POST /orders — create a new laundry order.

    Request body (JSON):
        customer_name (str), phone (str), garments (list)

    Returns:
        201 with the created order, or 400 on validation failure.
    """
    payload = request.get_json(silent=True) or {}

    errors = validate_create_order_payload(payload)
    if errors:
        return error(join_errors(errors), 400)

    order = _build_order(payload)
    order_store[order["order_id"]] = order

    return success(order, 201)


def _build_order(payload: dict) -> dict:
    """Construct a new order dict from a validated create-order payload."""
    return {
        "order_id": str(uuid.uuid4()),
        "customer_name": payload["customer_name"],
        "phone": payload["phone"],
        "garments": payload["garments"],
        "status": "RECEIVED",
        "total_bill": calculate_total_bill(payload["garments"]),
        "estimated_delivery_date": _delivery_date(),
    }


def _delivery_date() -> str:
    """Return the estimated delivery date as an ISO string (today + 2 days)."""
    return (date.today() + timedelta(days=2)).isoformat()


# ---------------------------------------------------------------------------
# Status update
# ---------------------------------------------------------------------------


@app.route("/orders/<order_id>/status", methods=["PUT"])
def update_order_status(order_id: str):
    """PUT /orders/<order_id>/status — advance an order's status.

    Request body (JSON):
        status (str)

    Returns:
        200 with the updated order, 400 for invalid input,
        404 if the order does not exist, 422 for an invalid transition.
    """
    if order_id not in order_store:
        return error(f"Order not found: {order_id}", 404)

    payload = request.get_json(silent=True) or {}

    if "status" not in payload:
        return error("Missing required field: status", 400)

    new_status = payload["status"]

    status_errors = validate_status_value(new_status)
    if status_errors:
        return error(join_errors(status_errors), 400)

    current_status = order_store[order_id]["status"]
    transition_errors = validate_status_transition(current_status, new_status)
    if transition_errors:
        return error(join_errors(transition_errors), 422)

    order_store[order_id]["status"] = new_status
    return success(order_store[order_id])


# ---------------------------------------------------------------------------
# Order retrieval
# ---------------------------------------------------------------------------


@app.route("/orders", methods=["GET"])
def get_orders():
    """GET /orders — list orders with optional filtering.

    Query parameters (all optional):
        status (str): exact match
        customer_name (str): case-insensitive substring match
        phone (str): exact match

    Returns:
        200 with a (possibly empty) list of matching orders,
        or 400 if the status query param is invalid.
    """
    status = request.args.get("status")
    customer_name = request.args.get("customer_name")
    phone = request.args.get("phone")

    if status is not None:
        status_errors = validate_status_value(status)
        if status_errors:
            return error(join_errors(status_errors), 400)

    filtered = filter_orders(list(order_store.values()), status, customer_name, phone)
    return success(filtered)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@app.route("/dashboard", methods=["GET"])
def get_dashboard():
    """GET /dashboard — aggregated business metrics.

    Returns:
        200 with total_orders, total_revenue, orders_per_status,
        average_order_value, and most_common_garment.
    """
    metrics = compute_dashboard(list(order_store.values()))
    return success(metrics)


if __name__ == "__main__":
    app.run(debug=True)
