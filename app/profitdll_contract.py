"""Read-only callback boundary; no guessed SDK ABI, credentials or order methods."""
from collections import deque
from typing import Protocol
import threading
from profit_bridge import MarketEvent, QuoteSnapshot, SourceBatch, SourceHealth


class AuthorizedMarketDataSDK(Protocol):
    def subscribe_market_data(self, symbol: str, on_trade, on_quote, on_disconnect) -> None: ...
    def close(self) -> None: ...


class ProfitMarketDataAdapter:
    def __init__(self, symbol, *, sdk=None, capacity=10000, sequence_is_per_symbol=False):
        if not isinstance(symbol, str) or not symbol.startswith('WIN') or type(capacity) is not int or not 1 <= capacity <= 100000 or type(sequence_is_per_symbol) is not bool:
            raise ValueError('Invalid subscription')
        self.symbol, self.sdk, self.capacity = symbol, sdk, capacity
        self.sequence_is_per_symbol = sequence_is_per_symbol
        self.events, self.quotes, self.issues = deque(), deque(maxlen=1), set()
        self.lock, self.connected, self.last_sequence = threading.Lock(), False, None

    def connect(self):
        if self.sdk is None:
            raise RuntimeError('SDK autorizado e licença Market Data da Nelogica são necessários')
        self.sdk.subscribe_market_data(self.symbol, self.on_trade, self.on_quote, self.on_disconnect)
        self.connected = True

    def on_trade(self, value, sequence=None):
        from decision_engine import decimal
        if value.get('symbol') != self.symbol or type(value.get('ts_ms')) is not int or type(value.get('quantity')) is not int or value['quantity'] <= 0 or value.get('aggressor') not in ('buy', 'sell', 'unknown') or decimal(str(value.get('price_points'))) <= 0:
            raise ValueError('Invalid market data callback')
        event = MarketEvent(value.get('id'), self.symbol, value['ts_ms'], float(value['price_points']), value['quantity'], value['aggressor'])
        with self.lock:
            if sequence is not None and type(sequence) is not int:
                raise ValueError('Invalid sequence')
            if self.sequence_is_per_symbol and sequence is not None and self.last_sequence is not None and sequence != self.last_sequence+1:
                # Interpret increments only when the licensed SDK documents this scope.
                self.issues.add('SEQUENCE_GAP')
            self.last_sequence = sequence
            if len(self.events) >= self.capacity:
                self.events.popleft(); self.issues.add('QUEUE_OVERFLOW')
            self.events.append(event)

    def on_quote(self, value):
        quote = QuoteSnapshot(**value)
        if quote.symbol != self.symbol:
            raise ValueError('Wrong quote symbol')
        with self.lock: self.quotes.append(quote)

    def on_disconnect(self):
        with self.lock:
            self.connected = False; self.issues.add('DISCONNECTED')

    def read(self, *, observed_at_ms):
        with self.lock:
            events, quotes = tuple(self.events), tuple(self.quotes)
            self.events.clear(); self.quotes.clear()
            # No automatic promotion to full tape, even with increasing sequence.
            health = SourceHealth('PROFITDLL_MARKET_DATA', self.connected, False, events[-1].ts_ms if events else None, observed_at_ms,
                                  issue=';'.join(sorted(self.issues)), sequence_ok=self.sequence_is_per_symbol and self.last_sequence is not None and not self.issues)
            return SourceBatch(events, quotes, health, tuple(sorted(self.issues)))

    def close(self):
        if self.sdk is not None: self.sdk.close()
        self.on_disconnect()
