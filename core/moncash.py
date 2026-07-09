"""MonCash (Digicel Haiti) REST API client.

Implements the flow from the MonCash REST API documentation:

  1. OAuth2 client-credentials token (short-lived, ~59s) via HTTP Basic auth.
  2. CreatePayment(amount, orderId) -> a payment token -> we redirect the
     buyer to the MonCash gateway to pay.
  3. On return, RetrieveOrderPayment(orderId) is called SERVER-SIDE to confirm
     the payment before anything is delivered. The browser redirect is never
     trusted on its own — only the API's "successful" verdict counts.

Credentials live in settings.MONCASH (env-driven). Nothing is hardcoded.

Endpoints (per the doc):
  REST host  : {sandbox.,}moncashbutton.digicelgroup.com/Api
  Gateway    : https://{sandbox.,}moncashbutton.digicelgroup.com/Moncash-middleware
"""
from __future__ import annotations

import requests
from django.conf import settings


class MonCashError(Exception):
    """Any failure talking to MonCash (network, auth, or API error)."""


class MonCashClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        mode: str | None = None,
        timeout: int = 20,
    ) -> None:
        cfg = getattr(settings, "MONCASH", {})
        self.client_id = client_id if client_id is not None else cfg.get("client_id", "")
        self.client_secret = (
            client_secret if client_secret is not None else cfg.get("client_secret", "")
        )
        self.mode = (mode or cfg.get("mode", "sandbox")).lower()
        self.timeout = timeout

        if self.mode == "live":
            self.rest_host = "https://moncashbutton.digicelgroup.com/Api"
            self.gateway_base = "https://moncashbutton.digicelgroup.com/Moncash-middleware"
        else:  # sandbox / anything else
            self.rest_host = "https://sandbox.moncashbutton.digicelgroup.com/Api"
            self.gateway_base = (
                "https://sandbox.moncashbutton.digicelgroup.com/Moncash-middleware"
            )

    @property
    def configured(self) -> bool:
        """True only when real credentials are present."""
        return bool(self.client_id and self.client_secret)

    # -- internals ---------------------------------------------------------
    def _token(self) -> str:
        """Fetch a fresh bearer token (they expire in ~59s, so never cache)."""
        url = f"{self.rest_host}/oauth/token"
        try:
            resp = requests.post(
                url,
                auth=(self.client_id, self.client_secret),
                data={"scope": "read,write", "grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise MonCashError(f"MonCash auth request failed: {exc}") from exc
        if resp.status_code != 200:
            raise MonCashError(
                f"MonCash auth failed ({resp.status_code}): {resp.text[:200]}"
            )
        token = (resp.json() or {}).get("access_token")
        if not token:
            raise MonCashError("MonCash auth returned no access_token")
        return token

    def _auth_headers(self, token: str) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # -- public API --------------------------------------------------------
    def create_payment(self, amount, order_id: str) -> dict:
        """Create a payment and return the gateway redirect URL.

        Returns {"payment_token", "redirect_url", "raw"}.
        """
        url = f"{self.rest_host}/v1/CreatePayment"
        payload = {"amount": float(amount), "orderId": str(order_id)}
        try:
            resp = requests.post(
                url, json=payload, headers=self._auth_headers(self._token()),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise MonCashError(f"MonCash CreatePayment request failed: {exc}") from exc
        if resp.status_code not in (200, 202):
            raise MonCashError(
                f"MonCash CreatePayment error ({resp.status_code}): {resp.text[:200]}"
            )
        data = resp.json() or {}
        token = (data.get("payment_token") or {}).get("token")
        if not token:
            raise MonCashError("MonCash CreatePayment returned no payment token")
        return {
            "payment_token": token,
            "redirect_url": f"{self.gateway_base}/Payment/Redirect?token={token}",
            "raw": data,
        }

    def retrieve_order_payment(self, order_id: str) -> dict | None:
        """Confirm a payment by our orderId. Returns the payment dict or None.

        The payment dict looks like:
          {"reference", "transaction_id", "cost", "message", "payer"}
        `message == "successful"` means the money moved.
        """
        return self._retrieve("RetrieveOrderPayment", {"orderId": str(order_id)})

    def retrieve_transaction_payment(self, transaction_id: str) -> dict | None:
        """Confirm a payment by MonCash transactionId. Returns dict or None."""
        return self._retrieve(
            "RetrieveTransactionPayment", {"transactionId": str(transaction_id)}
        )

    def _retrieve(self, resource: str, body: dict) -> dict | None:
        url = f"{self.rest_host}/v1/{resource}"
        try:
            resp = requests.post(
                url, json=body, headers=self._auth_headers(self._token()),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise MonCashError(f"MonCash {resource} request failed: {exc}") from exc
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise MonCashError(
                f"MonCash {resource} error ({resp.status_code}): {resp.text[:200]}"
            )
        return (resp.json() or {}).get("payment")
