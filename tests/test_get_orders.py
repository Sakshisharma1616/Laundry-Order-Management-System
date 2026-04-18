"""Property-based and unit tests for GET /orders endpoint."""

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

import app as app_module
from tests.conftest import valid_order_strategy, filter_combination_strategy


# ---------------------------------------------------------------------------
# Property 6: Order Filtering Correctness
# ---------------------------------------------------------------------------


@given(
    orders=st.lists(valid_order_strategy(), min_size=0, max_size=20),
    filters=filter_combination_strategy(),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_order_filtering_correctness(client, orders, filters):
    # Feature: laundry-order-management, Property 6: Order Filtering Correctness
    # Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

    # Populate the store with generated orders (client fixture already cleared it)
    app_module.order_store.clear()
    for order in orders:
        app_module.order_store[order["order_id"]] = order

    # Build query params, skipping None values
    params = {k: v for k, v in filters.items() if v is not None}

    # GET /orders with the query params
    response = client.get("/orders", query_string=params)

    # Assert HTTP 200
    assert response.status_code == 200

    response_json = response.get_json()
    assert "data" in response_json

    returned_ids = {o["order_id"] for o in response_json["data"]}

    # Compute expected orders manually using the same filter logic
    status_filter = filters.get("status")
    customer_name_filter = filters.get("customer_name")
    phone_filter = filters.get("phone")

    expected_orders = []
    for order in orders:
        # status: exact match
        if status_filter is not None and order["status"] != status_filter:
            continue
        # customer_name: case-insensitive substring match
        if customer_name_filter is not None and customer_name_filter.lower() not in order["customer_name"].lower():
            continue
        # phone: exact match
        if phone_filter is not None and order["phone"] != phone_filter:
            continue
        expected_orders.append(order)

    expected_ids = {o["order_id"] for o in expected_orders}

    # Assert the response data list contains exactly the expected orders
    assert returned_ids == expected_ids


# ---------------------------------------------------------------------------
# Unit tests for GET /orders
# ---------------------------------------------------------------------------


def test_no_filters_returns_all_orders(client):
    """Test that GET /orders with no filters returns all orders."""
    orders = [
        {
            "order_id": "order-1",
            "customer_name": "Alice",
            "phone": "1234567890",
            "garments": [{"type": "Shirt", "quantity": 2}],
            "status": "RECEIVED",
            "total_bill": 100.0,
            "estimated_delivery_date": "2025-01-01",
        },
        {
            "order_id": "order-2",
            "customer_name": "Bob",
            "phone": "0987654321",
            "garments": [{"type": "Pants", "quantity": 1}],
            "status": "PROCESSING",
            "total_bill": 80.0,
            "estimated_delivery_date": "2025-01-01",
        },
    ]
    for order in orders:
        app_module.order_store[order["order_id"]] = order

    response = client.get("/orders")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 2


def test_status_filter_returns_only_matching_orders(client):
    """Test that status filter returns only orders with matching status."""
    app_module.order_store["o1"] = {
        "order_id": "o1", "customer_name": "Alice", "phone": "111",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }
    app_module.order_store["o2"] = {
        "order_id": "o2", "customer_name": "Bob", "phone": "222",
        "garments": [], "status": "PROCESSING", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }

    response = client.get("/orders", query_string={"status": "RECEIVED"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["order_id"] == "o1"


def test_customer_name_partial_case_insensitive_match(client):
    """Test that customer_name filter does case-insensitive partial matching."""
    app_module.order_store["o1"] = {
        "order_id": "o1", "customer_name": "Alice Smith", "phone": "111",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }
    app_module.order_store["o2"] = {
        "order_id": "o2", "customer_name": "Bob Jones", "phone": "222",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }

    # Partial match, different case
    response = client.get("/orders", query_string={"customer_name": "alice"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["order_id"] == "o1"


def test_phone_exact_match(client):
    """Test that phone filter does exact matching."""
    app_module.order_store["o1"] = {
        "order_id": "o1", "customer_name": "Alice", "phone": "1234567890",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }
    app_module.order_store["o2"] = {
        "order_id": "o2", "customer_name": "Bob", "phone": "0987654321",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }

    response = client.get("/orders", query_string={"phone": "1234567890"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["order_id"] == "o1"


def test_combined_filters(client):
    """Test that multiple filters are applied simultaneously (AND logic)."""
    app_module.order_store["o1"] = {
        "order_id": "o1", "customer_name": "Alice", "phone": "111",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }
    app_module.order_store["o2"] = {
        "order_id": "o2", "customer_name": "Alice", "phone": "222",
        "garments": [], "status": "PROCESSING", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }
    app_module.order_store["o3"] = {
        "order_id": "o3", "customer_name": "Bob", "phone": "111",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }

    # Only o1 matches both status=RECEIVED AND customer_name=Alice
    response = client.get("/orders", query_string={"status": "RECEIVED", "customer_name": "Alice"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["order_id"] == "o1"


def test_no_matches_returns_empty_list(client):
    """Test that when no orders match filters, an empty list is returned with HTTP 200."""
    app_module.order_store["o1"] = {
        "order_id": "o1", "customer_name": "Alice", "phone": "111",
        "garments": [], "status": "RECEIVED", "total_bill": 0.0, "estimated_delivery_date": "2025-01-01",
    }

    response = client.get("/orders", query_string={"status": "DELIVERED"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data == []


def test_invalid_status_query_param_returns_400(client):
    """Test that an invalid status query param returns HTTP 400."""
    response = client.get("/orders", query_string={"status": "UNKNOWN_STATUS"})
    assert response.status_code == 400
    assert "error" in response.get_json()
