"""Property 8: Response Envelope Format tests."""

import app as app_module
from app import app

import pytest
from hypothesis import given, settings, HealthCheck

from tests.conftest import any_request_strategy


@pytest.fixture
def client():
    """Create a Flask test client and clear the order_store before each test."""
    app.config["TESTING"] = True
    app_module.order_store.clear()
    with app.test_client() as test_client:
        yield test_client
    app_module.order_store.clear()


@given(request_data=any_request_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_response_envelope_format(client, request_data):
    # Feature: laundry-order-management, Property 8: Response Envelope Format
    """For any request to any endpoint, every response SHALL have Content-Type: application/json
    and the JSON body SHALL have exactly one of 'data' or 'error' key (not both, not neither).
    If 'error' key is present, it must be a string.

    Validates: Requirements 5.1, 5.2, 5.3
    """
    endpoint = request_data["endpoint"]

    if endpoint == "POST /orders":
        response = client.post("/orders", json=request_data["body"])
    elif endpoint == "PUT /orders/<id>/status":
        order_id = request_data["order_id"]
        response = client.put(f"/orders/{order_id}/status", json=request_data["body"])
    elif endpoint == "GET /orders":
        filters = {k: v for k, v in request_data["filters"].items() if v is not None}
        response = client.get("/orders", query_string=filters)
    elif endpoint == "GET /dashboard":
        response = client.get("/dashboard")
    else:
        raise ValueError(f"Unknown endpoint: {endpoint}")

    # Assert Content-Type is application/json
    assert "application/json" in response.content_type, (
        f"Expected Content-Type to contain 'application/json', got '{response.content_type}'"
    )

    # Parse JSON body
    body = response.get_json()
    assert body is not None, "Response body must be valid JSON"

    has_data = "data" in body
    has_error = "error" in body

    # Assert exactly one of 'data' or 'error' is present (not both, not neither)
    assert has_data != has_error, (
        f"Response body must have exactly one of 'data' or 'error' key, got keys: {list(body.keys())}"
    )

    # If 'error' key is present, it must be a string
    if has_error:
        assert isinstance(body["error"], str), (
            f"'error' value must be a string, got {type(body['error'])}: {body['error']!r}"
        )
