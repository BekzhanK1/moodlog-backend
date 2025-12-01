"""
Webkassa.kz payment gateway integration service.
"""

import requests
from typing import Dict, Any
from app.core.config import settings


class WebkassaService:
    """Service for interacting with Webkassa.kz payment gateway."""

    def __init__(self):
        self.api_url = settings.webkassa_api_url
        self.api_key = settings.webkassa_api_key
        self.cashbox_id = settings.webkassa_cashbox_id

    def create_payment_order(
        self,
        amount: float,
        user_email: str,
        plan_name: str,
        order_id: str,
    ) -> Dict[str, Any]:
        """
        Create a payment order in Webkassa.kz.

        Args:
            amount: Payment amount in KZT
            user_email: User's email address
            plan_name: Name of the subscription plan
            order_id: Unique order identifier

        Returns:
            Dictionary with payment order details including payment_url

        Raises:
            requests.RequestException: If API request fails
        """
        payload = {
            "cashbox_id": self.cashbox_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "KZT",
            "description": f"Подписка {plan_name} - Moodlog",
            "customer_email": user_email,
            "return_url": f"{settings.frontend_url}/payment/success",
            "cancel_url": f"{settings.frontend_url}/payment/cancel",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.api_url}/orders/create",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """
        Check payment status in Webkassa.kz.

        Args:
            order_id: Order identifier

        Returns:
            Dictionary with payment status information

        Raises:
            requests.RequestException: If API request fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.get(
            f"{self.api_url}/orders/{order_id}/status",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def issue_fiscal_receipt(
        self,
        order_id: str,
        amount: float,
        user_email: str,
    ) -> Dict[str, Any]:
        """
        Issue fiscal receipt after successful payment.
        This is required for Kazakhstan tax compliance.

        Args:
            order_id: Order identifier
            amount: Payment amount in KZT
            user_email: User's email address

        Returns:
            Dictionary with receipt information including receipt_id

        Raises:
            requests.RequestException: If API request fails
        """
        payload = {
            "cashbox_id": self.cashbox_id,
            "order_id": order_id,
            "amount": amount,
            "customer_email": user_email,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.api_url}/receipts/issue",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


# Global service instance
webkassa_service = WebkassaService()
