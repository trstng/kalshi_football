"""
Kalshi Trading API Client for placing real orders.
"""
import logging
import time
from typing import Optional, Literal
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """Represents a Kalshi order."""
    order_id: str
    market_ticker: str
    side: Literal["yes", "no"]
    action: Literal["buy", "sell"]
    count: int
    price: int  # In cents
    status: str


class KalshiTradingClient:
    """
    Client for Kalshi Trading API.
    Handles authentication and order placement.
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.Session()
        self.token = None

        # Authenticate
        if api_key and api_secret:
            self._login_with_api_key(api_key, api_secret)
        elif email and password:
            self._login_with_email(email, password)
        else:
            raise ValueError("Must provide either (email, password) or (api_key, api_secret)")

    def _login_with_email(self, email: str, password: str):
        """Login using email and password."""
        url = f"{self.base_url}/login"
        response = self.session.post(url, json={"email": email, "password": password})
        response.raise_for_status()

        data = response.json()
        self.token = data["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

        logger.info("Successfully authenticated with email")

    def _login_with_api_key(self, api_key: str, api_secret: str):
        """Login using API key and secret."""
        # Kalshi API key authentication
        # See: https://docs.kalshi.com/
        self.session.headers.update({
            "X-Api-Key": api_key,
        })
        logger.info("Successfully authenticated with API key")

    def get_balance(self) -> int:
        """Get account balance in cents."""
        url = f"{self.base_url}/portfolio/balance"
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        return data["balance"]

    def get_positions(self) -> list[dict]:
        """Get all open positions."""
        url = f"{self.base_url}/portfolio/positions"
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get("positions", [])

    def place_order(
        self,
        market_ticker: str,
        side: Literal["yes", "no"],
        action: Literal["buy", "sell"],
        count: int,
        price: int,  # In cents
        order_type: Literal["limit", "market"] = "limit",
    ) -> Order:
        """
        Place a limit or market order.

        Args:
            market_ticker: Market ticker (e.g., "KXNFLGAME-25OCT13BUFATL")
            side: "yes" or "no"
            action: "buy" or "sell"
            count: Number of contracts
            price: Price in cents (0-100)
            order_type: "limit" or "market"

        Returns:
            Order object with order details
        """
        url = f"{self.base_url}/portfolio/orders"

        payload = {
            "ticker": market_ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": order_type,
        }

        if order_type == "limit":
            payload["yes_price"] = price if side == "yes" else None
            payload["no_price"] = price if side == "no" else None

        logger.info(
            f"Placing order: {action} {count} {side} @ {price}¢ on {market_ticker}"
        )

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        order = Order(
            order_id=data["order_id"],
            market_ticker=market_ticker,
            side=side,
            action=action,
            count=count,
            price=price,
            status=data.get("status", "pending"),
        )

        logger.info(f"Order placed successfully: {order.order_id}")
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        url = f"{self.base_url}/portfolio/orders/{order_id}"

        response = self.session.delete(url)
        response.raise_for_status()

        logger.info(f"Order {order_id} cancelled")
        return True

    def get_order_status(self, order_id: str) -> dict:
        """Get status of an order."""
        url = f"{self.base_url}/portfolio/orders/{order_id}"

        response = self.session.get(url)
        response.raise_for_status()

        return response.json()

    def close(self):
        """Close the session."""
        self.session.close()
