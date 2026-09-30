
"""
Supplychainer Currency Service

All route calculations use USD as the internal/base currency.
This module converts the calculated USD amount into the
currency selected by the dashboard.

IMPORTANT:
The rates below are configuration/demo rates.
They should not be treated as live FX rates.
For production, replace them with a live/cached FX provider.
"""

from typing import Dict, Any


BASE_CURRENCY = "USD"


# Base USD -> target currency.
# Example:
# 1 USD = 83.94 INR
# 1 USD = 0.85 EUR
EXCHANGE_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.85,
    "GBP": 0.74,
    "INR": 83.94,
    "AED": 3.67,
    "CNY": 7.18,
}


CURRENCY_INFO: Dict[str, Dict[str, str]] = {
    "USD": {
        "name": "US Dollar",
        "symbol": "$",
    },
    "EUR": {
        "name": "Euro",
        "symbol": "€",
    },
    "GBP": {
        "name": "British Pound",
        "symbol": "£",
    },
    "INR": {
        "name": "Indian Rupee",
        "symbol": "₹",
    },
    "AED": {
        "name": "UAE Dirham",
        "symbol": "د.إ",
    },
    "CNY": {
        "name": "Chinese Yuan",
        "symbol": "¥",
    },
}


def get_supported_currencies() -> Dict[str, Dict[str, str]]:
    """Return currencies supported by the dashboard."""
    return CURRENCY_INFO


def normalize_currency(currency: str) -> str:
    """
    Normalize and validate a currency code.

    Raises:
        ValueError: if the currency is not supported.
    """
    currency = (currency or BASE_CURRENCY).upper().strip()

    if currency not in EXCHANGE_RATES:
        supported = ", ".join(EXCHANGE_RATES.keys())
        raise ValueError(
            f"Unsupported currency '{currency}'. "
            f"Supported currencies: {supported}"
        )

    return currency


def convert_from_usd(amount: float, currency: str) -> float:
    """
    Convert an amount from the internal USD base currency
    to the requested display currency.
    """
    currency = normalize_currency(currency)
    converted = float(amount) * EXCHANGE_RATES[currency]
    return round(converted, 2)


def get_currency_details(currency: str) -> Dict[str, Any]:
    """Return complete information for one currency."""
    currency = normalize_currency(currency)

    return {
        "code": currency,
        "name": CURRENCY_INFO[currency]["name"],
        "symbol": CURRENCY_INFO[currency]["symbol"],
        "exchange_rate": EXCHANGE_RATES[currency],
        "base_currency": BASE_CURRENCY,
    }


def convert_cost_breakdown(
    transit: float,
    transfer: float,
    scenario: float,
    currency: str
) -> Dict[str, float]:
    """Convert an audit-trace cost breakdown from USD."""
    return {
        "transit": convert_from_usd(transit, currency),
        "transfer": convert_from_usd(transfer, currency),
        "scenario": convert_from_usd(scenario, currency),
        "total": convert_from_usd(
            transit + transfer + scenario,
            currency
        ),
    }

