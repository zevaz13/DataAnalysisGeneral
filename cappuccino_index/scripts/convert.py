"""Convert a currency amount to USD using ECB reference rates (frankfurter.dev).

Covers 30 currencies (ECB reference set) — see api.frankfurter.dev/v1/currencies.
"""

import requests

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1"


def convert_to_usd(amount: float, currency_code: str, date: str | None = None) -> float:
    """Convert `amount` in `currency_code` (e.g. "GBP") to USD.

    `date` is an ISO date string (e.g. "2024-12-01") for a historical rate;
    omit for the latest available rate. Raises requests.HTTPError if the
    currency or date isn't covered by the API.
    """
    endpoint = date if date else "latest"
    response = requests.get(f"{FRANKFURTER_BASE}/{endpoint}", params={"from": currency_code, "to": "USD"})
    response.raise_for_status()
    return amount * response.json()["rates"]["USD"]
