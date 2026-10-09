"""Read-only Profit RTD/DDE Excel snapshots and explicit trade CSV replay.

No ProfitDLL, account access, order submission, Excel launch or workbook mutation.
Excel is attached through native COM (comtypes) to an already-open workbook.
PowerShell is used only when the optional comtypes package is absent.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import unicodedata
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_EVENTS = 10000


class BridgeError(ValueError):
    """Actionable, sanitized data source failure."""


@dataclass(frozen=True)
class MarketEvent:
    trade_id: str | None
    symbol: str
    ts_ms: int
    price_points: float
    quantity: int
    aggressor: str
    buyer_broker: str | None = None
    seller_broker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result['id'] = result.pop('trade_id')
        return result


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    last: float
    bid: float | None = None
    ask: float | None = None
    bidqty: int | None = None
    askqty: int | None = None
    ts_ms: int | None = None


@dataclass(frozen=True)
class SourceHealth:
    kind: str
    connected: bool
    complete: bool
    last_event_ts_ms: int | None
    observed_at_ms: int
    issue: str = ''
    sequence_ok: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.update(feed_connected=None if self.kind == 'EXCEL_COMBINED_SNAPSHOT' else self.connected, full_tape=self.complete,
                      data_origin=self.kind)
        return result


@dataclass(frozen=True)
class SourceBatch:
    events: tuple[MarketEvent, ...]
    quotes: tuple[QuoteSnapshot, ...]
    health: SourceHealth
    warnings: tuple[str, ...] = ()
    books: tuple[dict, ...] = ()
    aggregates: tuple[dict, ...] = ()
    capabilities: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(events=[event.to_dict() for event in self.events],
                    quotes=[asdict(quote) for quote in self.quotes],
                    health=self.health.to_dict(), warnings=list(self.warnings), books=list(self.books),
                    aggregates=list(self.aggregates), capabilities=dict(self.capabilities), evidence=dict(self.evidence))


class SeenTradeIds:
    """Bounded explicit-ID deduplication, scoped by symbol and trade date.

    Identical prints with no ID are kept distinct. Eviction is observable.
    """
    def __init__(self, capacity: int = 50000):
        if capacity < 1:
            raise BridgeError('Capacidade de IDs deve ser positiva.')
        self.capacity = capacity
        self.ids: OrderedDict[tuple[str, str, str], MarketEvent] = OrderedDict()
        self.evictions = 0

    def accept(self, event: MarketEvent) -> bool:
        if event.trade_id is None:
            return True
        date = datetime.fromtimestamp(event.ts_ms / 1000, timezone.utc).date().isoformat()
        key = (event.symbol, date, event.trade_id)
        if key in self.ids:
            if self.ids[key] != event:
                raise BridgeError('ID de negócio reutilizado com conteúdo diferente; reinicie a captura após corrigir a fonte.')
            self.ids.move_to_end(key)
            return False
        self.ids[key] = event
        if len(self.ids) > self.capacity:
            self.ids.popitem(last=False)
            self.evictions += 1
        return True


# Export headings vary by selected Profit attributes. Only explicit aliases map.
ALIASES = {
    'id': {'id', 'tradeid', 'tradeno', 'negocioid', 'numeronegocio', 'numerodonegocio'},
    'symbol': {'symbol', 'ativo', 'ticker', 'contrato'},
    'timestamp': {'timestamp', 'datetime', 'datahora', 'instante', 'ts'},
    'ts_ms': {'tsms', 'timestampms', 'epochms'},
    'date': {'date', 'data', 'dat'},
    'time': {'time', 'hora', 'hor', 'horario'},
    'price': {'pricepoints', 'price', 'preco', 'last', 'ultimo', 'ult'},
    'quantity': {'quantity', 'qty', 'quantidade', 'qtd', 'quant'},
    'aggressor': {'aggressor', 'agressor', 'agressao', 'ladoagressor'},
    'bid': {'bid', 'ocp', 'ofertacompra', 'ofcompra'},
    'ask': {'ask', 'ovd', 'ofertavenda', 'ofvenda'},
    'bidqty': {'bidqty', 'voc', 'quantidadecompra', 'volumedeofertadecompra'},
    'askqty': {'askqty', 'vov', 'quantidadevenda', 'volumedeofertadevenda'},
    'buyer_broker': {'buyerbroker', 'buyfirm', 'corretoracompradora', 'corretoracompra'},
    'seller_broker': {'sellerbroker', 'sellfirm', 'corretoravendedora', 'corretoravenda'},
}


def _heading(value: Any) -> str:
    text = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', text.lower())


def _columns(headers: Iterable[Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for index, heading in enumerate(headers):
        key = _heading(heading)
        for canonical, aliases in ALIASES.items():
            if key in aliases:
                if canonical in result:
                    raise BridgeError(f'Coluna duplicada/ambígua: {canonical}.')
                result[canonical] = index
    return result


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise BridgeError('Valor numérico ausente/inválido.')
    text = str(value).strip().replace('\xa0', '').replace(' ', '')
    if not text:
        raise BridgeError('Valor numérico ausente.')
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    # No decimal comma: numeric . is decimal, never guessed as thousands.
    try:
        result = Decimal(text)
    except InvalidOperation as exc:
        raise BridgeError('Valor numérico inválido.') from exc
    if not result.is_finite():
        raise BridgeError('Valor numérico não finito.')
    return result


def _price(value: Any) -> float:
    result = float(_decimal(value))
    if not math.isfinite(result) or result <= 0:
        raise BridgeError('Preço deve ser positivo e finito.')
    return result


def _quantity(value: Any, *, allow_zero: bool = False) -> int:
    result = _decimal(value)
    if result != result.to_integral_value() or result < (0 if allow_zero else 1):
        raise BridgeError('Quantidade deve ser inteira e positiva (zero apenas no livro).')
    return int(result)


def _market_timezone():
    # B3 dates before 2019 need the historical IANA rules; tzdata is used if present.
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('America/Sao_Paulo')
    except Exception:
        return timezone(timedelta(hours=-3))


def _timestamp(value: Any, *, epoch_ms: bool = False, date_value: Any = None) -> int:
    if epoch_ms:
        number = _decimal(value)
        if number != number.to_integral_value() or not 0 < number < 10**14:
            raise BridgeError('ts_ms deve ser epoch UTC em milissegundos inteiro positivo.')
        return int(number)
    text = str(value).strip() if value is not None else ''
    if not text:
        raise BridgeError('Timestamp da origem ausente.')
    # Excel Value2 dates are serial numbers. Require combined date+time, not time only.
    if isinstance(value, (int, float)) and value > 10000:
        dt = datetime(1899, 12, 30) + timedelta(days=float(value))
    else:
        if date_value is not None and str(date_value).strip():
            date_text = str(date_value).strip()
            if isinstance(date_value, (int, float)):
                date_text = (datetime(1899, 12, 30) + timedelta(days=float(date_value))).strftime('%Y-%m-%d')
            if isinstance(value, (int, float)) and 0 <= value < 1:
                value = (datetime(2000, 1, 1) + timedelta(days=float(value))).strftime('%H:%M:%S.%f')
            text = f'{date_text} {value}'
        if not re.search(r'[T ]\d{1,2}:\d{2}', text):
            raise BridgeError('Timestamp precisa de data e hora; data isolada não é suficiente.')
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            dt = None
            for fmt in ('%d/%m/%Y %H:%M:%S.%f', '%d/%m/%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S.%f'):
                try:
                    dt = datetime.strptime(text.replace(',', '.'), fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                raise BridgeError('Timestamp precisa de data e hora; hora isolada não é suficiente.')
    if dt.tzinfo is None:
        tz = _market_timezone()
        if isinstance(tz, timezone) and dt.year < 2020:
            raise BridgeError('Datas históricas exigem tzdata para America/Sao_Paulo.')
        dt = dt.replace(tzinfo=tz)
    result = int(dt.timestamp() * 1000)
    if result <= 0:
        raise BridgeError('Timestamp inválido.')
    return result


def _aggressor(value: Any) -> str:
    normalized = _heading(value)
    if normalized in {'buy', 'compra', 'comprador', 'c', 'b'}:
        return 'BUY'
    if normalized in {'sell', 'venda', 'vendedor', 'v', 's'}:
        return 'SELL'
    return 'UNKNOWN'


def _parse_rows(rows: list[list[Any]], symbol: str, *, mode: str, kind: str,
                seen_ids: SeenTradeIds | None = None, max_events: int = MAX_EVENTS,
                initial_warnings: Iterable[str] = ()) -> SourceBatch:
    now_ms = int(time.time() * 1000)
    warnings = list(initial_warnings)
    if not rows:
        raise BridgeError('Fonte vazia; informe intervalo com cabeçalho e dados.')
    columns = _columns(rows[0])
    required = {'price'} if mode == 'quote' else {'price', 'quantity', 'aggressor'}
    missing = required - columns.keys()
    if missing:
        raise BridgeError('Colunas ausentes: ' + ', '.join(sorted(missing)))
    if mode == 'tape' and not ({'ts_ms', 'timestamp'} & columns.keys() or {'date', 'time'} <= columns.keys()):
        raise BridgeError('Negócios exigem timestamp/ts_ms ou colunas data e hora.')
    if max_events < 1 or max_events > MAX_EVENTS:
        raise BridgeError(f'max_events deve estar entre 1 e {MAX_EVENTS}.')
    events: list[MarketEvent] = []
    quotes: list[QuoteSnapshot] = []
    # Even without a caller-owned cache, IDs are deduplicated within this read.
    dedup = seen_ids if seen_ids is not None else SeenTradeIds()
    observed_events: list[MarketEvent] = []
    valid_ids = True
    invalid = 0
    raw_events = 0
    for row_no, row in enumerate(rows[1:], 2):
        if not any(value is not None and str(value).strip() for value in row):
            continue
        def cell(key: str, default: Any = None):
            index = columns.get(key)
            return row[index] if index is not None and index < len(row) else default
        try:
            row_symbol = str(cell('symbol', symbol) or symbol).strip().upper()
            if not row_symbol:
                raise BridgeError('Informe o contrato explícito.')
            if symbol and row_symbol != symbol.strip().upper():
                continue
            ts = None
            if 'ts_ms' in columns:
                ts = _timestamp(cell('ts_ms'), epoch_ms=True)
            elif 'timestamp' in columns:
                ts = _timestamp(cell('timestamp'))
            elif {'date', 'time'} <= columns.keys():
                ts = _timestamp(cell('time'), date_value=cell('date'))
            if mode == 'quote':
                def optional_price(key):
                    return _price(cell(key)) if cell(key) not in (None, '') else None
                def optional_qty(key):
                    return _quantity(cell(key), allow_zero=True) if cell(key) not in (None, '') else None
                quotes.append(QuoteSnapshot(row_symbol, _price(cell('price')),
                                            optional_price('bid'), optional_price('ask'),
                                            optional_qty('bidqty'), optional_qty('askqty'), ts))
            else:
                if ts is None:
                    raise BridgeError('Timestamp ausente.')
                trade_id = str(cell('id', '') or '').strip() or None
                valid_ids = valid_ids and trade_id is not None
                event = MarketEvent(trade_id, row_symbol, ts, _price(cell('price')),
                                    _quantity(cell('quantity')), _aggressor(cell('aggressor')),
                                    str(cell('buyer_broker') or '').strip()[:80] or None,
                                    str(cell('seller_broker') or '').strip()[:80] or None)
                raw_events += 1
                observed_events.append(event)
                if dedup.accept(event):
                    events.append(event)
        except BridgeError as exc:
            invalid += 1
            if invalid <= 5:
                warnings.append(f'Linha {row_no} ignorada: {exc}')
    if len(events) > max_events or len(quotes) > max_events:
        warnings.append('Limite de eventos atingido; janela truncada e cobertura incompleta.')
        events, quotes = events[-max_events:], quotes[-max_events:]
    if invalid:
        warnings.append(f'{invalid} linha(s) inválida(s); cobertura incompleta.')
    if mode == 'tape' and not valid_ids:
        warnings.append('Há negócios sem ID: repetições não podem ser distinguidas; cobertura incompleta.')
    if mode == 'quote':
        warnings.append('RTD/DDE é snapshot de cotação; não representa todos os negócios ou livro completo.')
        if any(quote.ts_ms is None for quote in quotes):
            warnings.append('Cotação sem timestamp da origem: idade real desconhecida.')
    if seen_ids is not None and seen_ids.evictions:
        warnings.append('Cache de IDs atingiu o limite; repetições antigas podem reaparecer.')
    sequence_ok = all(a.ts_ms <= b.ts_ms for a, b in zip(observed_events, observed_events[1:]))
    if not sequence_ok:
        warnings.append('Ordem temporal regressiva; eventos preservados, sequência não íntegra.')
    # An unchanged snapshot still has its original timestamp. Deduplication must
    # not erase source time or stamp it with the current read time.
    timestamps = [e.ts_ms for e in observed_events] + [q.ts_ms for q in quotes if q.ts_ms is not None]
    # Even a valid CSV is a replay subset, never proof of complete live tape.
    health = SourceHealth(kind, bool(events or quotes or raw_events), False,
                          max(timestamps, default=None), now_ms,
                          '; '.join(warnings), sequence_ok=sequence_ok and bool(observed_events) and not invalid)
    return SourceBatch(tuple(events), tuple(quotes), health, tuple(warnings))


def read_csv_events(path: str | Path, symbol: str = '', *, seen_ids: SeenTradeIds | None = None,
                    max_events: int = MAX_EVENTS, mode: str = 'tape') -> SourceBatch:
    """Read a bounded snapshot of CSV; failed/partial records are never invented.

    Supported timestamp columns: ts_ms, timestamp with date/time, or data + hora.
    PT-BR semicolon CSV accepts decimal comma. UTF-8 BOM and CP1252 are supported.
    """
    if mode not in {'tape', 'quote'}:
        raise BridgeError('Modo deve ser tape ou quote.')
    file_path = Path(path)
    try:
        before = file_path.stat()
        if before.st_size > MAX_FILE_BYTES:
            raise BridgeError('CSV excede 8 MiB; exporte uma janela menor.')
        with file_path.open('rb') as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        after = file_path.stat()
    except OSError as exc:
        raise BridgeError('Não foi possível ler CSV; confira arquivo e permissão.') from exc
    if len(data) > MAX_FILE_BYTES:
        raise BridgeError('CSV excede 8 MiB.')
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise BridgeError('CSV mudou durante leitura; aguarde gravação completa ou use substituição atômica.')
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = data.decode('cp1252')
    warnings: list[str] = []
    first = text.splitlines()[0] if text.splitlines() else ''
    # Excel's optional separator hint is metadata, not a column header.
    sep_hint = re.fullmatch(r'sep=([;,\t])', first.strip(), re.IGNORECASE)
    if sep_hint:
        delimiter = sep_hint.group(1)
        text = text[text.find('\n') + 1:]
    else:
        delimiter = ';' if first.count(';') > first.count(',') else ('\t' if '\t' in first else ',')
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise BridgeError('CSV incompleto ou inválido; salve a exportação antes de ler.') from exc
    # A too-short final row can be a concurrent writer's partial line.
    if rows and len(rows[-1]) != len(rows[0]):
        rows.pop()
        warnings.append('Última linha incompleta ignorada.')
    if len(rows) > MAX_EVENTS * 10 + 1:
        raise BridgeError('CSV possui linhas demais; exporte janela menor.')
    return _parse_rows(rows, symbol, mode=mode,
                       kind='CSV_REPLAY' if mode == 'tape' else 'CSV_QUOTE_SNAPSHOT',
                       seen_ids=seen_ids, max_events=max_events, initial_warnings=warnings)


def _validate_range(cell_range: str) -> str:
    match = re.fullmatch(r'\$?([A-Za-z]{1,3})\$?([1-9][0-9]*):\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)', cell_range.strip())
    if not match:
        raise BridgeError('Intervalo deve ser retangular A1:H200, incluindo cabeçalho.')
    def col_number(column):
        result = 0
        for character in column.upper():
            result = result * 26 + ord(character) - 64
        return result
    first_col, first_row, last_col, last_row = match.groups()
    width = col_number(last_col) - col_number(first_col) + 1
    height = int(last_row) - int(first_row) + 1
    if width < 1 or width > 64 or height < 2 or height > 5001 or col_number(last_col) > 16384 or int(last_row) > 1048576:
        raise BridgeError('Intervalo máximo: 64 colunas e 5001 linhas; inclua cabeçalho e dados.')
    return cell_range.strip().upper()


def _load_comtypes():
    """Return native modules, or None only if comtypes is genuinely absent."""
    try:
        import comtypes
        import comtypes.client
    except ModuleNotFoundError as exc:
        if exc.name == 'comtypes':
            return None
        raise BridgeError('Leitor COM incompleto; reinstale o pacote do aplicativo.') from exc
    except Exception as exc:
        raise BridgeError('Leitor COM não pôde carregar; reinstale o pacote Windows.') from exc
    return comtypes, comtypes.client


def _read_excel_com_rows(workbook: str, sheet: str, cell_range: str, *, com_modules=None) -> list[list[Any]]:
    return _read_excel_com_ranges(workbook, [(sheet, cell_range)], com_modules=com_modules)[0]


def discover_open_excel(*, com_modules=None):
    """Metadata only, from the attached Excel instance; never open or read cells."""
    modules = com_modules if com_modules is not None else _load_comtypes()
    if modules is None:
        raise BridgeError('Leitor COM não instalado.')
    comtypes, client = modules
    initialized = False
    excel = books = book = sheets = sheet = None
    try:
        comtypes.CoInitialize()
        initialized = True
        excel = client.GetActiveObject('Excel.Application', dynamic=True)
        books = excel.Workbooks
        if type(books.Count) is not int or not 0 <= books.Count <= 100:
            raise BridgeError('Quantidade de arquivos excede o limite de descoberta.')
        found = []
        for index in range(1, books.Count+1):
            book = books.Item(index)
            sheets = book.Worksheets
            if type(sheets.Count) is not int or not 0 <= sheets.Count <= 100:
                raise BridgeError('Quantidade de planilhas excede o limite de descoberta.')
            names = []
            for number in range(1, sheets.Count+1):
                sheet = sheets.Item(number)
                names.append(str(sheet.Name)[:256])
                sheet = None
            found.append(dict(workbook=str(book.Name)[:256], sheets=names))
            sheets = book = None
        return dict(workbooks=found, scope='attached_excel_instance', cells_read=False)
    except BridgeError:
        raise
    except Exception:
        raise BridgeError('Excel não encontrado ou ocupado na mesma sessão; abra a planilha e feche diálogos.') from None
    finally:
        sheet = sheets = book = books = excel = None
        if initialized:
            comtypes.CoUninitialize()


def _read_excel_com_ranges(workbook: str, ranges: list[tuple[str, str]], *, com_modules=None, property_name='Value2') -> list[list[list[Any]]]:
    """Attach existing Excel, copy values, then release pointers on this thread.

    Dynamic dispatch avoids generating Excel type-library wrappers. No Excel
    object is retained or passed to another thread. Never launch/open/write.
    """
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 4:
        raise BridgeError('Informe de um a quatro intervalos Excel.')
    selections = []
    for sheet, cell_range in ranges:
        if not isinstance(sheet, str) or not sheet.strip():
            raise BridgeError('Informe o nome da planilha.')
        selections.append((sheet, _validate_range(cell_range)))
    modules = com_modules if com_modules is not None else _load_comtypes()
    if modules is None:
        raise BridgeError('Leitor COM não instalado.')
    comtypes, client = modules
    initialized = False
    excel = books = candidate = selected = worksheets = selected_sheet = selected_range = values = None
    stage = 'initialize'
    failure = None
    try:
        comtypes.CoInitialize()
        initialized = True
        stage = 'attach'
        excel = client.GetActiveObject('Excel.Application', dynamic=True)
        stage = 'workbook'
        books = excel.Workbooks
        count = books.Count
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 100:
            raise BridgeError('Feche arquivos Excel extras; limite de 100 arquivos abertos por instância.')
        for index in range(1, count + 1):
            candidate = books.Item(index)
            # Read only identification of already-open workbooks, never cells
            # of an unselected workbook. FullName supports a user-selected path.
            if (str(candidate.Name).casefold() == workbook.casefold() or
                    str(candidate.FullName).casefold() == workbook.casefold()):
                selected = candidate
                break
            candidate = None
        if selected is None:
            raise BridgeError('Arquivo não encontrado entre os arquivos Excel já abertos.')
        worksheets = selected.Worksheets
        all_rows = []
        for sheet, cell_range in selections:
            stage = 'sheet'
            selected_sheet = worksheets.Item(sheet)
            stage = 'read'
            selected_range = selected_sheet.Range[cell_range]
            values = selected_range.Formula if property_name == 'Formula' else selected_range.Value2
            if not isinstance(values, (tuple, list)) or not 2 <= len(values) <= 5001:
                raise BridgeError('Excel retornou intervalo inválido; inclua cabeçalho e dados.')
            rows = []
            width = None
            for row in values:
                if not isinstance(row, (tuple, list)) or not 1 <= len(row) <= 64:
                    raise BridgeError('Excel retornou intervalo inválido.')
                if width is None:
                    width = len(row)
                if len(row) != width or any(not isinstance(value, (str, int, float, bool, type(None))) for value in row):
                    raise BridgeError('Excel retornou valores não suportados.')
                rows.append(list(row))
            all_rows.append(rows)
            values = selected_range = selected_sheet = None
        return all_rows
    except BridgeError:
        raise
    except Exception:
        messages = {
            'initialize': 'COM não inicializado; verifique a instalação Windows.',
            'attach': 'Excel não encontrado na mesma sessão; abra Excel e sua planilha RTD.',
            'workbook': 'Não foi possível identificar o arquivo Excel já aberto.',
            'sheet': 'Planilha não encontrada no arquivo aberto.',
            'read': 'Excel recusou leitura; feche diálogos e confira permissão/sessão.',
        }
        # Leave the handler before apartment teardown so the original COM
        # traceback cannot retain interface pointers or leak private details.
        failure = messages[stage]
    finally:
        # Python/comtypes release interface references before apartment teardown.
        # Never call Quit, Close or explicit Release on shared dynamic wrappers.
        values = selected_range = selected_sheet = worksheets = selected = candidate = books = excel = None
        if initialized:
            comtypes.CoUninitialize()
    if failure is not None:
        raise BridgeError(failure)


class ExcelBridge:
    def __init__(self, workbook: str, sheet: str, cell_range: str,
                 mode: str = 'quote', symbol: str = '', timeout_seconds: float = 8):
        if not workbook.strip() or not sheet.strip():
            raise BridgeError('Informe nome do arquivo aberto e nome da planilha.')
        if mode not in {'quote', 'tape'}:
            raise BridgeError('Modo deve ser quote ou tape.')
        if not 1 <= timeout_seconds <= 30:
            raise BridgeError('Timeout deve estar entre 1 e 30 segundos.')
        self.workbook, self.sheet = workbook, sheet
        self.cell_range, self.mode = _validate_range(cell_range), mode
        self.symbol, self.timeout_seconds = symbol.strip().upper(), timeout_seconds
        self.seen_ids = SeenTradeIds()
        # The application constructs this object on its UI thread. Importing
        # comtypes there establishes its initial apartment; workers explicitly
        # initialize and balance their own COM access in the reader above.
        self._com_modules = _load_comtypes() if os.name == 'nt' else None

    def read(self) -> SourceBatch:
        if os.name != 'nt':
            raise BridgeError('Excel RTD requer Windows e Microsoft Excel já aberto; use CSV para replay.')
        modules = self._com_modules if self._com_modules is not None else _load_comtypes()
        if modules is not None:
            rows = _read_excel_com_rows(self.workbook, self.sheet, self.cell_range, com_modules=modules)
            backend = 'COM nativo'
        else:
            rows = self._read_powershell_rows()
            backend = 'PowerShell (comtypes ausente)'
        return _parse_rows(rows, self.symbol, mode=self.mode,
                           kind='RTD_SNAPSHOT' if self.mode == 'quote' else 'EXCEL_TAPE_SNAPSHOT',
                           seen_ids=self.seen_ids,
                           initial_warnings=(f'Leitor: {backend}. Excel lido por amostragem; linhas podem mudar entre leituras e perder negócios.',))

    def _read_powershell_rows(self) -> list[list[Any]]:
        helper_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
        helper = helper_root / 'helpers' / 'read_excel.ps1'
        if not helper.is_file():
            raise BridgeError('Leitor Excel não encontrado; reinstale o pacote completo.')
        config = dict(workbook=self.workbook, sheet=self.sheet, cell_range=self.cell_range)
        encoded = base64.b64encode(json.dumps(config, ensure_ascii=False).encode('utf-8')).decode('ascii')
        powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
        try:
            result = subprocess.run([str(powershell), '-NoLogo', '-NoProfile', '-NonInteractive',
                                     '-File', str(helper), '-ConfigBase64', encoded],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace',
                                    timeout=self.timeout_seconds, shell=False,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except subprocess.TimeoutExpired as exc:
            raise BridgeError('Excel não respondeu no prazo; verifique janelas de diálogo e conexão RTD.') from exc
        except OSError as exc:
            raise BridgeError('Não foi possível iniciar leitor do Excel no Windows.') from exc
        if result.returncode:
            # Raw shell/COM messages can contain sensitive local paths; never surface them.
            raise BridgeError('Leitura Excel falhou: abra a planilha indicada na mesma sessão e verifique a política PowerShell.')
        try:
            payload = json.loads(result.stdout.lstrip('\ufeff').strip())
        except (ValueError, TypeError) as exc:
            raise BridgeError('Leitor Excel retornou resposta inválida.') from exc
        if not isinstance(payload, dict) or payload.get('ok') is not True:
            code = payload.get('error', '') if isinstance(payload, dict) else ''
            messages = {
                'EXCEL_NOT_RUNNING': 'Excel não encontrado na mesma sessão; abra Excel e sua planilha RTD.',
                'WORKBOOK_NOT_FOUND': 'Arquivo não encontrado entre os arquivos Excel já abertos.',
                'SHEET_NOT_FOUND': 'Planilha não encontrada no arquivo aberto.',
                'READ_FAILED': 'Excel recusou leitura; feche diálogos e confira permissão/sessão.',
                'INVALID_CONFIG': 'Configuração do leitor Excel inválida.',
            }
            raise BridgeError(messages.get(code, 'Falha na leitura do Excel.'))
        rows = payload.get('rows')
        if not isinstance(rows, list) or any(not isinstance(row, list) for row in rows):
            raise BridgeError('Leitor Excel retornou intervalo inválido.')
        return rows


class CombinedExcelBridge:
    """Read quote and actual trade tables in one COM cycle, without cached halves.

    Both tables must already be populated by the user/their authorized export.
    Native COM is required; no unverified Times & Trades exporter is provided.
    Values are sequential snapshots, not an atomic exchange transaction.
    """
    def __init__(self, workbook: str, quote_sheet: str, quote_range: str,
                 tape_sheet: str, tape_range: str, *, symbol: str,
                 book_sheet: str = '', book_range: str = '', vap_sheet: str = '', vap_range: str = '',
                 window_mode: str = '', filters: str = '',
                 timeout_seconds: float = 8):
        if not all(isinstance(value, str) and value.strip()
                   for value in (workbook, quote_sheet, symbol)) or bool(tape_sheet) != bool(tape_range):
            raise BridgeError('Informe arquivo, cotação e contrato; negócios são opcionais com planilha e intervalo juntos.')
        if not 1 <= timeout_seconds <= 30:
            raise BridgeError('Timeout deve estar entre 1 e 30 segundos.')
        self.workbook, self.quote_sheet, self.tape_sheet = workbook, quote_sheet, tape_sheet
        self.quote_range = _validate_range(quote_range)
        self.tape_range = _validate_range(tape_range) if tape_sheet else ''
        for sheet, interval in ((book_sheet,book_range), (vap_sheet,vap_range)):
            if bool(sheet) != bool(interval):
                raise BridgeError('Informe planilha e intervalo juntos para livro/VAP.')
            if sheet: _validate_range(interval)
        self.last_capture_ms = None
        self.last_values = None
        self.last_change_ms = None
        self.change_interval_ms = None
        self.book_sheet, self.book_range = book_sheet, book_range
        self.vap_sheet, self.vap_range = vap_sheet, vap_range
        self.window_mode, self.filters = window_mode, filters
        self.symbol = symbol.strip().upper()
        self.timeout_seconds = timeout_seconds  # no hard interruption for native COM
        self.seen_ids = SeenTradeIds()
        self._com_modules = _load_comtypes() if os.name == 'nt' else None

    def read(self) -> SourceBatch:
        if os.name != 'nt':
            raise BridgeError('Leitura combinada requer Windows e Excel já aberto.')
        modules = self._com_modules if self._com_modules is not None else _load_comtypes()
        if modules is None:
            raise BridgeError('Leitura combinada requer COM nativo; use o pacote completo com comtypes.')
        selections = [(self.quote_sheet, self.quote_range)]
        if self.tape_sheet:
            selections.append((self.tape_sheet, self.tape_range))
        if self.book_sheet:
            selections.append((self.book_sheet,self.book_range))
        if self.vap_sheet:
            selections.append((self.vap_sheet,self.vap_range))
        matrices = _read_excel_com_ranges(self.workbook, selections, com_modules=modules)
        if len(matrices) != len(selections):
            raise BridgeError('Leitura combinada incompleta; nenhuma tabela foi aplicada.')
        # Parse each new cycle with a transactional dedup cache. Failure of one
        # table must not consume IDs or return the other table plus old values.
        staged_ids = SeenTradeIds(self.seen_ids.capacity)
        staged_ids.ids = self.seen_ids.ids.copy()
        staged_ids.evictions = self.seen_ids.evictions
        quote_batch = _parse_rows(matrices[0], self.symbol, mode='quote', kind='RTD_SNAPSHOT')
        tape_batch = _parse_rows(matrices[1], self.symbol, mode='tape',
                                 kind='EXCEL_TAPE_SNAPSHOT', seen_ids=staged_ids) if self.tape_sheet else SourceBatch((),(),SourceHealth('EXCEL_TAPE_SNAPSHOT',True,False,None,int(time.time()*1000),sequence_ok=True))
        if not quote_batch.health.connected or not tape_batch.health.connected:
            raise BridgeError('Leitura combinada exige cotações e negócios válidos nas duas tabelas; nenhuma tabela foi aplicada.')
        if any(warning.startswith('Linha ') or 'linha(s) inválida(s)' in warning
               for warning in quote_batch.warnings + tape_batch.warnings):
            raise BridgeError('Há linha inválida em uma tabela combinada; corrija a exportação. Nenhuma tabela foi aplicada.')
        if not tape_batch.health.sequence_ok:
            raise BridgeError('Negócios combinados fora de ordem temporal; organize do mais antigo ao mais recente antes de aplicar.')
        observed = int(time.time() * 1000)
        extra_index = 1 + bool(self.tape_sheet)
        books = (parse_book_rows(matrices[extra_index],self.symbol,observed),) if self.book_sheet else ()
        aggregates = tuple(parse_vap_rows(matrices[extra_index+bool(self.book_sheet)],self.symbol)) if self.vap_sheet else ()
        columns = _columns(matrices[1][0]) if self.tape_sheet else {}
        capabilities = dict(trade_id='id' in columns, buyer_broker='buyer_broker' in columns,
                            seller_broker='seller_broker' in columns,
                            book_snapshot=bool(books), volume_at_price=bool(aggregates), continuity_verified=False)
        warnings = tuple(dict.fromkeys((
            'Cotações e negócios lidos no mesmo ciclo COM; valores sequenciais, sem garantia de atomicidade ou tape integral.',
            *quote_batch.warnings, *tape_batch.warnings)))
        health = SourceHealth('EXCEL_COMBINED_SNAPSHOT', True, False,
                              tape_batch.health.last_event_ts_ms, observed,
                              '; '.join(warnings), sequence_ok=True)
        # Observed sample changes are measured separately from polling; neither
        # is an exchange latency nor proof of Excel's effective RTD frequency.
        polling = observed-self.last_capture_ms if self.last_capture_ms is not None else None
        values = repr(matrices)
        if values != self.last_values:
            self.change_interval_ms = observed-self.last_change_ms if self.last_change_ms is not None else None
            self.last_change_ms = observed
        self.last_capture_ms, self.last_values = observed, values
        # Commit only after all reads and both parsers succeed.
        self.seen_ids = staged_ids
        return SourceBatch(tape_batch.events, quote_batch.quotes, health, warnings, books, aggregates, capabilities,
                           dict(window_mode=self.window_mode or 'não informado', filters=self.filters or 'não informado',
                                captured_at_ms=observed, table_fields=[list(_columns(m[0])) for m in matrices],
                                continuity='não demonstrada', polling_target_ms=250,
                                polling_effective_ms=polling, rtd_change_interval_ms=self.change_interval_ms))

    def audit(self):
        selections = [(self.quote_sheet,self.quote_range)]
        for sheet, interval in ((self.tape_sheet,self.tape_range),(self.book_sheet,self.book_range),(self.vap_sheet,self.vap_range)):
            if sheet: selections.append((sheet,interval))
        # Bounded excerpt of selected tables only. Formulas stay local and are
        # deliberately excluded from the shared JEV state.
        formulas = _read_excel_com_ranges(self.workbook,selections,com_modules=self._com_modules,property_name='Formula')
        return dict(status='ready', captured_at_ms=int(time.time()*1000),
                    tables=[dict(sheet=sheet, interval=interval, excerpt=[row[:16] for row in matrix[:12]])
                            for (sheet,interval),matrix in zip(selections,formulas)],
                    note='Excerto local de até 12×16 células por tabela selecionada; fórmulas não são enviadas ao JEV.')


def parse_book_rows(rows, symbol, captured_at_ms):
    """Paired bid/ask columns. No inferred order IDs or exchange timestamps."""
    columns = _columns(rows[0])
    if not {'bid','ask','bidqty','askqty'} <= columns.keys():
        raise BridgeError('Livro exige bid, ask, bidqty e askqty explícitos.')
    sides = dict(bids=[], asks=[])
    stamps = set()
    for row in rows[1:]:
        if not any(v not in (None,'') for v in row): continue
        cell = lambda key: row[columns[key]] if columns[key] < len(row) else None
        if 'symbol' in columns and str(cell('symbol')).upper() != symbol: continue
        for side,price,qty in (('bids','bid','bidqty'),('asks','ask','askqty')):
            if cell(price) in (None,''): continue
            p, q = _price(cell(price)), _quantity(cell(qty),allow_zero=True)
            if p % 5: raise BridgeError('Preço do livro fora do tick WIN.')
            if q: sides[side].append(dict(price_points=p,quantity=q))
        if 'ts_ms' in columns: stamps.add(_timestamp(cell('ts_ms'),epoch_ms=True))
    for side in sides:
        sides[side].sort(key=lambda x:x['price_points'],reverse=side=='bids')
        if not sides[side] or len(sides[side])>256 or len({x['price_points'] for x in sides[side]})!=len(sides[side]):
            raise BridgeError('Livro vazio, duplicado ou acima de 256 níveis.')
    if sides['bids'][0]['price_points'] >= sides['asks'][0]['price_points']:
        raise BridgeError('Livro travado/cruzado; confira a tabela selecionada.')
    return dict(symbol=symbol, **sides, market_ts_ms=next(iter(stamps)) if len(stamps)==1 else None,
                captured_at_ms=captured_at_ms, kind='book_snapshot', order_identity=False, continuity_verified=False)


def parse_vap_rows(rows, symbol):
    columns = _columns(rows[0])
    if not {'price','quantity'} <= columns.keys(): raise BridgeError('VAP exige preço e quantidade explícitos.')
    result = []
    for row in rows[1:]:
        if not any(v not in (None,'') for v in row): continue
        if 'symbol' in columns and str(row[columns['symbol']]).upper()!=symbol: continue
        if _price(row[columns['price']]) % 5: raise BridgeError('Preço VAP fora do tick WIN.')
        result.append(dict(price_points=_price(row[columns['price']]),quantity=_quantity(row[columns['quantity']],allow_zero=True),
                           kind='volume_at_price_aggregate', window='janela da exportação; não equivale ao tape'))
    if len({x['price_points'] for x in result}) != len(result): raise BridgeError('Preço duplicado no VAP.')
    return result


class RtdThrottleGuard:
    """Only explicit enable changes Excel's global RTD interval; never opens Excel."""
    def __init__(self, *, com_modules=None):
        self.modules = com_modules
        self.previous = None
        self.attached_excel = None

    def _access(self, operation):
        native,client = self.modules or _load_comtypes()
        native.CoInitialize()
        excel = None
        try:
            excel = client.GetActiveObject('Excel.Application',dynamic=True)
            return operation(excel)
        except Exception as error:
            raise BridgeError('Não foi possível consultar/restaurar throttle do Excel; verifique manualmente.') from error
        finally:
            excel = None
            native.CoUninitialize()

    def observe(self):
        return self._access(lambda excel: dict(current_ms=int(excel.RTD.ThrottleInterval),status='observed'))

    def enable(self):
        def change(excel):
            current = int(excel.RTD.ThrottleInterval)
            handle = getattr(excel,'Hwnd',None)
            if self.previous is not None and self.attached_excel != handle:
                raise BridgeError('Instância Excel mudou; restauração anterior requer verificação manual.')
            if self.previous is None:
                self.previous = current
                self.attached_excel = handle
            excel.RTD.ThrottleInterval = 250
            return dict(previous_ms=self.previous,current_ms=250,restored=False,status='changed')
        return self._access(change)

    def restore(self):
        if self.previous is None: return dict(restored=True,status='unchanged')
        def change(excel):
            current = int(excel.RTD.ThrottleInterval)
            if getattr(excel,'Hwnd',None) != self.attached_excel:
                raise BridgeError('Instância Excel mudou; confira throttle anterior manualmente.')
            restored = current==250
            if restored: excel.RTD.ThrottleInterval = self.previous
            result = dict(previous_ms=self.previous,current_ms=int(excel.RTD.ThrottleInterval),restored=restored,
                          status='restored' if restored else 'external_change_preserved')
            self.previous = None
            return result
        return self._access(change)
