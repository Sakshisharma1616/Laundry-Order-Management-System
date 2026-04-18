"""Tests for create order functionality — Property 3."""

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.conftest import invalid_payload_strategy
from validators import validate_create_order_payload


# Feature: laundry-order-management, Property 3: Create Order Validation Rejects Invalid Payloads
@given(payload=invalid_payload_strategy())
@settings(max_examples=100)
def test_create_order_validation_rejects_invalid_payloads(payload):
    """**Validates: Requirements 1.6, 1.7, 1.8, 1.9, 1.10**

    For any invalid create-order payload, validate_create_order_payload must
    return a non-empty list of error messages.
    """
    # Feature: laundry-order-management, Property 3: Create Order Validation Rejects Invalid Payloads
    errors = validate_create_order_payload(payload)
    assert isinstance(errors, list), "validate_create_order_payload must return a list"
    assert len(errors) > 0, (
        f"Expected at least one validation error for invalid payload {payload!r}, "
        f"but got an empty list"
    )


# Feature: laundry-order-management, Property 2: Pricing Calculation Correctness
UNIT_PRICES = {"Shirt": 50, "Pants": 80, "Saree": 100}


@given(
    garments=st.lists(
        st.fixed_dictionaries({
            "type": st.sampled_from(["Shirt", "Pants", "Saree"]),
            "quantity": st.integers(min_value=1, max_value=1000),
        }),
        min_size=1,
    )
)
@settings(max_examples=100)
def test_pricing_calculation_correctness(garments):
    """**Validates: Requirements 1.5**

    For any list of garments with valid types and positive quantities,
    calculate_total_bill must equal the sum of (unit_price * quantity).
    """
    # Feature: laundry-order-management, Property 2: Pricing Calculation Correctness
    from helpers import calculate_total_bill

    expected_total = sum(UNIT_PRICES[g["type"]] * g["quantity"] for g in garments)
    assert calculate_total_bill(garments) == float(expected_total)


import uuid
from datetime import date, timedelta

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


# Feature: laundry-order-management, Property 1: Order Creation Invariants
@given(
    customer_name=st.text(min_size=1),
    phone=st.text(min_size=1),
    garments=st.lists(
        st.fixed_dictionaries({
            "type": st.sampled_from(["Shirt", "Pants", "Saree"]),
            "quantity": st.integers(min_value=1, max_value=100),
        }),
        min_size=1,
    ),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_order_creation_invariants(client, customer_name, phone, garments):
    """**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    For any valid create-order payload, the system must respond with HTTP 201,
    a valid UUID4 order_id, status == "RECEIVED", and estimated_delivery_date
    equal to today + 2 calendar days.
    """
    # Feature: laundry-order-management, Property 1: Order Creation Invariants
    payload = {
        "customer_name": customer_name,
        "phone": phone,
        "garments": garments,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201, (
        f"Expected HTTP 201 but got {response.status_code} for payload {payload!r}"
    )
    body = response.get_json()
    data = body["data"]

    # Requirement 1.2: valid UUID4 order_id
    parsed = uuid.UUID(data["order_id"], version=4)
    assert str(parsed) == data["order_id"], (
        f"order_id {data['order_id']!r} is not a valid UUID4"
    )

    # Requirement 1.3: status == "RECEIVED"
    assert data["status"] == "RECEIVED", (
        f"Expected status 'RECEIVED' but got {data['status']!r}"
    )

    # Requirement 1.4: estimated_delivery_date == today + 2 days
    expected_date = (date.today() + timedelta(days=2)).isoformat()
    assert data["estimated_delivery_date"] == expected_date, (
        f"Expected estimated_delivery_date {expected_date!r} but got "
        f"{data['estimated_delivery_date']!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests for POST /orders (Task 4.3)
# ---------------------------------------------------------------------------


def test_create_order_known_total_bill(client):
    """2 Shirts (2×50=100) + 1 Saree (1×100=100) should produce total_bill == 200.0."""
    payload = {
        "customer_name": "Alice",
        "phone": "1234567890",
        "garments": [
            {"type": "Shirt", "quantity": 2},
            {"type": "Saree", "quantity": 1},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["total_bill"] == 200.0


def test_create_order_missing_customer_name(client):
    """POST without customer_name should return HTTP 400 with an 'error' key."""
    payload = {
        "phone": "1234567890",
        "garments": [{"type": "Shirt", "quantity": 1}],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body


def test_create_order_missing_phone(client):
    """POST without phone should return HTTP 400 with an 'error' key."""
    payload = {
        "customer_name": "Alice",
        "garments": [{"type": "Shirt", "quantity": 1}],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body


def test_create_order_missing_garments(client):
    """POST without garments field should return HTTP 400 with an 'error' key."""
    payload = {
        "customer_name": "Alice",
        "phone": "1234567890",
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body


def test_create_order_empty_garments(client):
    """POST with garments=[] should return HTTP 400 with an 'error' key."""
    payload = {
        "customer_name": "Alice",
        "phone": "1234567890",
        "garments": [],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body


def test_create_order_invalid_garment_type(client):
    """POST with an unsupported garment type should return HTTP 400 with an 'error' key."""
    payload = {
        "customer_name": "Alice",
        "phone": "1234567890",
        "garments": [{"type": "Jacket", "quantity": 1}],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body


def test_create_order_non_positive_quantity(client):
    """POST with quantity=0 should return HTTP 400 with an 'error' key."""
    payload = {
        "customer_name": "Alice",
        "phone": "1234567890",
        "garments": [{"type": "Shirt", "quantity": 0}],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert "error" in body
