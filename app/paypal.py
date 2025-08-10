"""Helpers for interacting with the PayPal API."""

from __future__ import annotations

from typing import Any

import requests
from flask import current_app


def _get_paypal_access_token() -> str:
    """Retrieve an OAuth access token from PayPal."""
    auth = (
        current_app.config["PAYPAL_CLIENT_ID"],
        current_app.config["PAYPAL_CLIENT_SECRET"],
    )
    resp = requests.post(
        f"{current_app.config['PAYPAL_API_BASE']}/v1/oauth2/token",
        data={"grant_type": "client_credentials"},
        auth=auth,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_order(total: str, currency: str = "USD") -> dict[str, Any]:
    """Create a PayPal order for the given ``total`` amount."""
    token = _get_paypal_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": currency, "value": total}}
        ],
    }
    resp = requests.post(
        f"{current_app.config['PAYPAL_API_BASE']}/v2/checkout/orders",
        json=payload,
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_subscription_status(subscription_id: str) -> str:
    """Return the status of a PayPal subscription."""
    token = _get_paypal_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        f"{current_app.config['PAYPAL_API_BASE']}/v1/billing/subscriptions/{subscription_id}",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("status", "")

