"""Fixed-endpoint, read-only Binance Spot market-data transport."""

from __future__ import annotations

import json
import ssl
import threading
import urllib.error
import urllib.request
from typing import Any, Callable


METADATA_URL = "https://data-api.binance.vision/api/v3/exchangeInfo?symbol=BTCUSDT"
STREAM_URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@trade/btcusdt@bookTicker"
MAX_METADATA_BYTES = 1_048_576


class NetworkError(RuntimeError):
    """Sanitized failure from the public, market-only transport."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise NetworkError("Binance metadata redirects are disabled.")


def _reject_json_constant(_value: str) -> None:
    raise NetworkError("Binance metadata contains a non-finite JSON number.")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise NetworkError("Binance metadata contains duplicate JSON keys.")
        result[key] = value
    return result


class BinancePublicTransport:
    """HTTP/WSS transport with immutable URLs and certificate validation."""

    def __init__(self, *, request_timeout_seconds: float = 5.0, stream_timeout_seconds: float = 1.0):
        for value, name in (
            (request_timeout_seconds, "request timeout"),
            (stream_timeout_seconds, "stream timeout"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be positive.")
        self._request_timeout_seconds = float(request_timeout_seconds)
        self._stream_timeout_seconds = float(stream_timeout_seconds)
        self._connection_lock = threading.Lock()
        self._connection = None

    def get_metadata(self, symbol: str = "BTCUSDT") -> dict:
        if symbol != "BTCUSDT":
            raise NetworkError("Only the BTCUSDT public spot pilot is supported.")

        context = ssl.create_default_context()
        request = urllib.request.Request(
            METADATA_URL,
            headers={"Accept": "application/json", "User-Agent": "JeveTrader-MarketObserver/1"},
            method="GET",
        )
        opener = urllib.request.build_opener(
            _NoRedirect(), urllib.request.HTTPSHandler(context=context)
        )
        try:
            with opener.open(request, timeout=self._request_timeout_seconds) as response:
                if response.status != 200 or response.geturl() != METADATA_URL:
                    raise NetworkError("Binance metadata response was not accepted.")
                raw = response.read(MAX_METADATA_BYTES + 1)
            if len(raw) > MAX_METADATA_BYTES:
                raise NetworkError("Binance metadata response exceeded the size limit.")
            value = json.loads(
                raw.decode("utf-8"),
                parse_constant=_reject_json_constant,
                object_pairs_hook=_unique_object,
            )
            if not isinstance(value, dict):
                raise NetworkError("Binance metadata schema is invalid.")
            return value
        except NetworkError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeError, ValueError, TypeError):
            raise NetworkError("Binance metadata request failed or could not be decoded.") from None

    def consume(
        self,
        stop_event: threading.Event,
        *,
        on_message: Callable[[str | bytes], None],
        on_open: Callable[[], None],
    ) -> None:
        """Read the fixed public stream until stopped or disconnected."""
        try:
            import websocket
        except ImportError:
            raise NetworkError("The websocket-client runtime dependency is unavailable.") from None

        try:
            connection = websocket.create_connection(
                STREAM_URL,
                timeout=self._request_timeout_seconds,
                sslopt={"cert_reqs": ssl.CERT_REQUIRED, "check_hostname": True},
                enable_multithread=True,
            )
        except Exception:
            raise NetworkError("Binance public WebSocket connection failed.") from None

        with self._connection_lock:
            self._connection = connection
        try:
            connection.settimeout(self._stream_timeout_seconds)
            if stop_event.is_set():
                return
            on_open()
            while not stop_event.is_set():
                try:
                    message = connection.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if message in (None, "", b""):
                    raise NetworkError("Binance public WebSocket disconnected.")
                on_message(message)
        except NetworkError:
            raise
        except Exception:
            if not stop_event.is_set():
                raise NetworkError("Binance public WebSocket stream failed.") from None
        finally:
            with self._connection_lock:
                if self._connection is connection:
                    self._connection = None
            try:
                connection.close()
            except Exception:
                pass

    def close(self) -> None:
        """Interrupt a blocking receive so adapter shutdown stays bounded."""
        with self._connection_lock:
            connection = self._connection
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
