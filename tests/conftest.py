"""Shared pytest fixtures and Hypothesis strategies for the Laundry Order Management tests."""

import uuid
from datetime import date, timedelta

import pytest
from hypothesis import strategies as st

import app as app_module
from app import app, VALID_STATUSES, UNIT_PRICES


# ---------------------------------------------------------------------------
# Flask test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a Flask test client and clear the order_store before each test."""
    app.config["TESTING"] = True
    app_module.order_store.clear()
    with app.test_client() as test_client:
        yield test_client
    app_module.order_store.clear()


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def valid_order_strategy():
    """Generate a valid order dict with all required fields."""
    return st.fixed_dictionaries(
        {
            "order_id": st.uuids(version=4).map(str),
            "customer_name": st.text(min_size=1, max_size=50),
            "phone": st.text(min_size=1, max_size=20),
            "garments": st.lists(
                st.fixed_dictionaries(
                    {
                        "type": st.sampled_from(list(UNIT_PRICES.keys())),
                        "quantity": st.integers(min_value=1, max_value=100),
                    }
                ),
                min_size=1,
                max_size=5,
            ),
            "status": st.sampled_from(VALID_STATUSES),
            "total_bill": st.floats(min_value=0.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
            "estimated_delivery_date": st.dates(
                min_value=date.today(),
                max_value=date.today() + timedelta(days=365),
            ).map(lambda d: d.isoformat()),
        }
    )


def filter_combination_strategy():
    """Generate a dict with optional filter keys: status, customer_name, phone."""
    return st.fixed_dictionaries(
        {
            "status": st.one_of(st.none(), st.sampled_from(VALID_STATUSES)),
            "customer_name": st.one_of(st.none(), st.text(min_size=0, max_size=30)),
            "phone": st.one_of(st.none(), st.text(min_size=0, max_size=20)),
        }
    )


def _missing_field_strategy():
    """Generate payloads missing one or more required top-level fields."""
    all_fields = {
        "customer_name": st.text(min_size=1),
        "phone": st.text(min_size=1),
        "garments": st.lists(
            st.fixed_dictionaries(
                {
                    "type": st.sampled_from(list(UNIT_PRICES.keys())),
                    "quantity": st.integers(min_value=1, max_value=100),
                }
            ),
            min_size=1,
        ),
    }
    required_keys = list(all_fields.keys())

    @st.composite
    def _build(draw):
        # Pick at least one key to omit
        keys_to_omit = draw(
            st.lists(st.sampled_from(required_keys), min_size=1, unique=True)
        )
        payload = {}
        for key, strategy in all_fields.items():
            if key not in keys_to_omit:
                payload[key] = draw(strategy)
        return payload

    return _build()


def _empty_garments_strategy():
    """Generate a payload with an empty garments list."""
    return st.fixed_dictionaries(
        {
            "customer_name": st.text(min_size=1),
            "phone": st.text(min_size=1),
            "garments": st.just([]),
        }
    )


def _garment_missing_field_strategy():
    """Generate a payload where at least one garment entry is missing type or quantity."""

    @st.composite
    def _build(draw):
        garment_keys = ["type", "quantity"]
        keys_to_omit = draw(
            st.lists(st.sampled_from(garment_keys), min_size=1, unique=True)
        )
        garment = {}
        if "type" not in keys_to_omit:
            garment["type"] = draw(st.sampled_from(list(UNIT_PRICES.keys())))
        if "quantity" not in keys_to_omit:
            garment["quantity"] = draw(st.integers(min_value=1, max_value=100))
        return {
            "customer_name": draw(st.text(min_size=1)),
            "phone": draw(st.text(min_size=1)),
            "garments": [garment],
        }

    return _build()


def _invalid_garment_type_strategy():
    """Generate a payload with an invalid garment type."""
    valid_types = set(UNIT_PRICES.keys())
    return st.fixed_dictionaries(
        {
            "customer_name": st.text(min_size=1),
            "phone": st.text(min_size=1),
            "garments": st.lists(
                st.fixed_dictionaries(
                    {
                        "type": st.text(min_size=1).filter(lambda t: t not in valid_types),
                        "quantity": st.integers(min_value=1, max_value=100),
                    }
                ),
                min_size=1,
            ),
        }
    )


def _non_positive_quantity_strategy():
    """Generate a payload with a non-positive garment quantity."""
    return st.fixed_dictionaries(
        {
            "customer_name": st.text(min_size=1),
            "phone": st.text(min_size=1),
            "garments": st.lists(
                st.fixed_dictionaries(
                    {
                        "type": st.sampled_from(list(UNIT_PRICES.keys())),
                        "quantity": st.integers(max_value=0),
                    }
                ),
                min_size=1,
            ),
        }
    )


def invalid_payload_strategy():
    """Generate invalid create-order payloads covering all validation failure cases."""
    return st.one_of(
        _missing_field_strategy(),
        _empty_garments_strategy(),
        _garment_missing_field_strategy(),
        _invalid_garment_type_strategy(),
        _non_positive_quantity_strategy(),
    )


def any_request_strategy():
    """Generate request data for any of the 4 endpoints."""
    valid_garments = st.lists(
        st.fixed_dictionaries(
            {
                "type": st.sampled_from(list(UNIT_PRICES.keys())),
                "quantity": st.integers(min_value=1, max_value=100),
            }
        ),
        min_size=1,
    )

    # POST /orders — valid payload
    valid_create = st.fixed_dictionaries(
        {
            "endpoint": st.just("POST /orders"),
            "body": st.fixed_dictionaries(
                {
                    "customer_name": st.text(min_size=1),
                    "phone": st.text(min_size=1),
                    "garments": valid_garments,
                }
            ),
        }
    )

    # POST /orders — invalid payload
    invalid_create = st.fixed_dictionaries(
        {
            "endpoint": st.just("POST /orders"),
            "body": invalid_payload_strategy(),
        }
    )

    # PUT /orders/<id>/status — valid status
    valid_status_update = st.fixed_dictionaries(
        {
            "endpoint": st.just("PUT /orders/<id>/status"),
            "order_id": st.uuids(version=4).map(str),
            "body": st.fixed_dictionaries(
                {"status": st.sampled_from(VALID_STATUSES)}
            ),
        }
    )

    # PUT /orders/<id>/status — invalid status
    invalid_status_update = st.fixed_dictionaries(
        {
            "endpoint": st.just("PUT /orders/<id>/status"),
            "order_id": st.uuids(version=4).map(str),
            "body": st.fixed_dictionaries(
                {
                    "status": st.text().filter(lambda s: s not in VALID_STATUSES),
                }
            ),
        }
    )

    # GET /orders — with or without filters
    get_orders = st.fixed_dictionaries(
        {
            "endpoint": st.just("GET /orders"),
            "filters": filter_combination_strategy(),
        }
    )

    # GET /dashboard — no body
    get_dashboard = st.just({"endpoint": "GET /dashboard"})

    return st.one_of(
        valid_create,
        invalid_create,
        valid_status_update,
        invalid_status_update,
        get_orders,
        get_dashboard,
    )
