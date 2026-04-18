"""Tests for GET /dashboard — Property 7 and unit tests.

# Feature: laundry-order-management, Property 7: Dashboard Metrics Correctness
"""

from collections import Counter

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

import app as app_module
from app import app, UNIT_PRICES, VALID_STATUSES
from tests.conftest import valid_order_strategy


# ---------------------------------------------------------------------------
# Property 7: Dashboard Metrics Correctness
# Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
# ---------------------------------------------------------------------------


@given(orders=st.lists(valid_order_strategy(), min_size=0, max_size=50))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_dashboard_metrics_correctness(orders):
    # Feature: laundry-order-management, Property 7: Dashboard Metrics Correctness
    app.config["TESTING"] = True
    app_module.order_store.clear()

    # Populate the store directly with generated orders
    for order in orders:
        app_module.order_store[order["order_id"]] = order

    with app.test_client() as client:
        response = client.get("/dashboard")

    assert response.status_code == 200

    body = response.get_json()
    assert "data" in body
    data = body["data"]

    # Assert all 5 keys are present
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "orders_per_status" in data
    assert "average_order_value" in data
    assert "most_common_garment" in data

    # Compute expected values manually
    expected_total_orders = len(orders)
    expected_total_revenue = sum(o["total_bill"] for o in orders)

    expected_orders_per_status: dict[str, int] = {}
    for o in orders:
        s = o["status"]
        expected_orders_per_status[s] = expected_orders_per_status.get(s, 0) + 1

    if expected_total_orders > 0:
        expected_avg = round(expected_total_revenue / expected_total_orders, 2)
    else:
        expected_avg = 0

    # Compute most_common_garment
    garment_totals: dict[str, int] = {}
    for o in orders:
        for g in o["garments"]:
            gtype = g["type"]
            garment_totals[gtype] = garment_totals.get(gtype, 0) + g["quantity"]

    if garment_totals:
        max_qty = max(garment_totals.values())
        top_garments = [g for g, qty in garment_totals.items() if qty == max_qty]
    else:
        top_garments = []

    # Assert total_orders
    assert data["total_orders"] == expected_total_orders

    # Assert total_revenue (allow small float tolerance)
    assert abs(data["total_revenue"] - expected_total_revenue) < 1e-6

    # Assert orders_per_status counts
    assert data["orders_per_status"] == expected_orders_per_status

    # Assert average_order_value
    assert data["average_order_value"] == expected_avg

    # Assert most_common_garment
    if expected_total_orders == 0:
        assert data["most_common_garment"] is None
    else:
        # In case of ties, any of the top garments is acceptable
        assert data["most_common_garment"] in top_garments
        assert data["most_common_garment"] in UNIT_PRICES

    # Cleanup
    app_module.order_store.clear()


# ---------------------------------------------------------------------------
# Unit tests for GET /dashboard (Task 9.4)
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a Flask test client and clear the order_store before each test."""
    app.config["TESTING"] = True
    app_module.order_store.clear()
    with app.test_client() as test_client:
        yield test_client
    app_module.order_store.clear()


def test_dashboard_empty_store(client):
    """Empty store returns zeroed metrics with most_common_garment null and orders_per_status {}."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_orders"] == 0
    assert data["total_revenue"] == 0
    assert data["orders_per_status"] == {}
    assert data["average_order_value"] == 0
    assert data["most_common_garment"] is None


def test_dashboard_single_order(client):
    """Single order produces correct metrics."""
    order = {
        "order_id": "test-order-001",
        "customer_name": "Alice",
        "phone": "1234567890",
        "garments": [{"type": "Shirt", "quantity": 2}, {"type": "Saree", "quantity": 1}],
        "status": "RECEIVED",
        "total_bill": 200.0,  # 2*50 + 1*100
        "estimated_delivery_date": "2025-12-01",
    }
    app_module.order_store["test-order-001"] = order

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["total_orders"] == 1
    assert data["total_revenue"] == 200.0
    assert data["orders_per_status"] == {"RECEIVED": 1}
    assert data["average_order_value"] == 200.0
    # Shirt qty=2, Saree qty=1 → Shirt is most common
    assert data["most_common_garment"] == "Shirt"


def test_dashboard_multiple_orders_average_order_value(client):
    """Multiple orders with known totals produce correct average_order_value."""
    orders = [
        {
            "order_id": "order-1",
            "customer_name": "Bob",
            "phone": "111",
            "garments": [{"type": "Pants", "quantity": 1}],
            "status": "RECEIVED",
            "total_bill": 80.0,
            "estimated_delivery_date": "2025-12-01",
        },
        {
            "order_id": "order-2",
            "customer_name": "Carol",
            "phone": "222",
            "garments": [{"type": "Shirt", "quantity": 3}],
            "status": "PROCESSING",
            "total_bill": 150.0,
            "estimated_delivery_date": "2025-12-01",
        },
        {
            "order_id": "order-3",
            "customer_name": "Dave",
            "phone": "333",
            "garments": [{"type": "Saree", "quantity": 2}],
            "status": "READY",
            "total_bill": 200.0,
            "estimated_delivery_date": "2025-12-01",
        },
    ]
    for o in orders:
        app_module.order_store[o["order_id"]] = o

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["total_orders"] == 3
    assert data["total_revenue"] == 430.0
    # (80 + 150 + 200) / 3 = 143.33
    assert data["average_order_value"] == round(430.0 / 3, 2)
    assert data["orders_per_status"] == {"RECEIVED": 1, "PROCESSING": 1, "READY": 1}


def test_dashboard_most_common_garment(client):
    """most_common_garment is correctly identified as the type with highest total quantity."""
    orders = [
        {
            "order_id": "order-a",
            "customer_name": "Eve",
            "phone": "444",
            "garments": [{"type": "Shirt", "quantity": 5}],
            "status": "RECEIVED",
            "total_bill": 250.0,
            "estimated_delivery_date": "2025-12-01",
        },
        {
            "order_id": "order-b",
            "customer_name": "Frank",
            "phone": "555",
            "garments": [{"type": "Pants", "quantity": 3}, {"type": "Saree", "quantity": 2}],
            "status": "DELIVERED",
            "total_bill": 440.0,
            "estimated_delivery_date": "2025-12-01",
        },
    ]
    for o in orders:
        app_module.order_store[o["order_id"]] = o

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.get_json()["data"]

    # Shirt=5, Pants=3, Saree=2 → Shirt is most common
    assert data["most_common_garment"] == "Shirt"


def test_dashboard_orders_per_status_all_statuses(client):
    """orders_per_status correctly counts orders across all status values."""
    statuses = ["RECEIVED", "PROCESSING", "READY", "DELIVERED"]
    for i, status in enumerate(statuses):
        order = {
            "order_id": f"order-{i}",
            "customer_name": f"Customer {i}",
            "phone": str(i),
            "garments": [{"type": "Shirt", "quantity": 1}],
            "status": status,
            "total_bill": 50.0,
            "estimated_delivery_date": "2025-12-01",
        }
        app_module.order_store[f"order-{i}"] = order

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["orders_per_status"] == {
        "RECEIVED": 1,
        "PROCESSING": 1,
        "READY": 1,
        "DELIVERED": 1,
    }
    assert data["total_orders"] == 4
