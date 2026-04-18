"""Tests for update order status functionality — Properties 4, 5 + unit tests."""

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

import app as app_module
from app import app, order_store, VALID_STATUSES, STATUS_TRANSITIONS


# ---------------------------------------------------------------------------
# Property 4: Status Transition Rules Are Enforced
# ---------------------------------------------------------------------------

# Feature: laundry-order-management, Property 4: Status Transition Rules Are Enforced
@given(
    current_status=st.sampled_from(["RECEIVED", "PROCESSING", "READY", "DELIVERED"]),
    target_status=st.sampled_from(["RECEIVED", "PROCESSING", "READY", "DELIVERED", "INVALID"]),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_status_transition_rules_are_enforced(client, current_status, target_status):
    """**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

    For any order in the store and any target status string:
    - If target_status is not in VALID_STATUSES: assert HTTP 400
    - If target_status is valid but the transition is not permitted: assert HTTP 422
    - If the transition is valid: assert HTTP 200 and data["status"] == target_status
    """
    # Feature: laundry-order-management, Property 4: Status Transition Rules Are Enforced
    order_id = "test-order-id"

    # Directly insert an order with current_status into the store
    app_module.order_store[order_id] = {
        "order_id": order_id,
        "customer_name": "Test Customer",
        "phone": "1234567890",
        "garments": [{"type": "Shirt", "quantity": 1}],
        "status": current_status,
        "total_bill": 50.0,
        "estimated_delivery_date": "2099-01-01",
    }

    response = client.put(f"/orders/{order_id}/status", json={"status": target_status})

    if target_status not in VALID_STATUSES:
        # Invalid status value → HTTP 400
        assert response.status_code == 400, (
            f"Expected HTTP 400 for invalid status {target_status!r}, "
            f"but got {response.status_code}"
        )
    elif STATUS_TRANSITIONS.get(current_status) != target_status:
        # Valid status value but invalid transition → HTTP 422
        assert response.status_code == 422, (
            f"Expected HTTP 422 for invalid transition {current_status!r} → {target_status!r}, "
            f"but got {response.status_code}"
        )
    else:
        # Valid transition → HTTP 200 with updated status
        assert response.status_code == 200, (
            f"Expected HTTP 200 for valid transition {current_status!r} → {target_status!r}, "
            f"but got {response.status_code}"
        )
        body = response.get_json()
        assert body["data"]["status"] == target_status, (
            f"Expected status {target_status!r} in response but got {body['data']['status']!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: Non-Existent Order Returns 404
# ---------------------------------------------------------------------------

# Feature: laundry-order-management, Property 5: Non-Existent Order Returns 404
@given(order_id=st.uuids(version=4).map(str))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_existent_order_returns_404(client, order_id):
    """**Validates: Requirements 2.6**

    For any UUID string not present in the Order_Store, a PUT request to
    /orders/<order_id>/status SHALL return HTTP 404 with an `error` key in
    the response body.
    """
    # Feature: laundry-order-management, Property 5: Non-Existent Order Returns 404

    # The client fixture clears order_store, so order_id is guaranteed absent
    response = client.put(f"/orders/{order_id}/status", json={"status": "PROCESSING"})

    assert response.status_code == 404, (
        f"Expected HTTP 404 for non-existent order {order_id!r}, "
        f"but got {response.status_code}"
    )
    body = response.get_json()
    assert "error" in body, (
        f"Expected 'error' key in response body for non-existent order, got: {body}"
    )


# ---------------------------------------------------------------------------
# Unit tests for PUT /orders/<order_id>/status
# ---------------------------------------------------------------------------

def test_full_valid_transition_sequence(client):
    """Test full valid transition sequence: RECEIVED → PROCESSING → READY → DELIVERED.

    Validates: Requirements 2.1–2.7
    """
    # Create an order via POST
    payload = {
        "customer_name": "Alice",
        "phone": "555-1234",
        "garments": [{"type": "Shirt", "quantity": 2}],
    }
    create_resp = client.post("/orders", json=payload)
    assert create_resp.status_code == 201
    order_id = create_resp.get_json()["data"]["order_id"]

    # RECEIVED → PROCESSING
    resp = client.put(f"/orders/{order_id}/status", json={"status": "PROCESSING"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "PROCESSING"

    # PROCESSING → READY
    resp = client.put(f"/orders/{order_id}/status", json={"status": "READY"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "READY"

    # READY → DELIVERED
    resp = client.put(f"/orders/{order_id}/status", json={"status": "DELIVERED"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "DELIVERED"


def test_update_delivered_order_returns_422(client):
    """Test that attempting to update a DELIVERED order returns HTTP 422.

    Validates: Requirements 2.3, 2.5
    """
    # Create and advance to DELIVERED
    payload = {
        "customer_name": "Bob",
        "phone": "555-5678",
        "garments": [{"type": "Pants", "quantity": 1}],
    }
    create_resp = client.post("/orders", json=payload)
    assert create_resp.status_code == 201
    order_id = create_resp.get_json()["data"]["order_id"]

    # Advance through all valid transitions
    for status in ["PROCESSING", "READY", "DELIVERED"]:
        resp = client.put(f"/orders/{order_id}/status", json={"status": status})
        assert resp.status_code == 200

    # Now try to update the DELIVERED order — any status should return 422
    resp = client.put(f"/orders/{order_id}/status", json={"status": "RECEIVED"})
    assert resp.status_code == 422


def test_update_status_missing_status_field(client):
    """Test that a PUT request without the `status` field returns HTTP 400 with an `error` key.

    Validates: Requirements 2.7
    """
    # Create an order
    payload = {
        "customer_name": "Carol",
        "phone": "555-9999",
        "garments": [{"type": "Saree", "quantity": 1}],
    }
    create_resp = client.post("/orders", json=payload)
    assert create_resp.status_code == 201
    order_id = create_resp.get_json()["data"]["order_id"]

    # PUT without status field
    resp = client.put(f"/orders/{order_id}/status", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert "error" in body


def test_update_status_unknown_order_id(client):
    """Test that a PUT to a non-existent order_id returns HTTP 404 with an `error` key.

    Validates: Requirements 2.6
    """
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.put(f"/orders/{fake_id}/status", json={"status": "PROCESSING"})
    assert resp.status_code == 404
    body = resp.get_json()
    assert "error" in body
