"""Conventional Windows startup, persistent diagnostics, and exception logging."""
from __future__ import annotations

import argparse
import ctypes
import faulthandler
import importlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import platform
import runpy
import re
import struct
import sys
import tempfile
import threading
import traceback

BASE = Path(__file__).resolve().parent
APP = BASE / 'app'
RUNTIME = BASE / 'runtime'
LOGGER = logging.getLogger('JevWIN.startup')
LOG_PATH: Path | None = None
CRASH_STREAM = None


def sanitize(text: str) -> str:
    text = re.sub(r"(?:https?|wss?)://[^\s<>\"']+", '<endereço remoto omitido>', str(text), flags=re.I)
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer [ocultado]', text)
    text = re.sub(r"(?i)([\"']?(?:api[-_]?key|access[-_]?token|refresh[-_]?token|token|authorization|password|senha|secret)[\"']?\s*[:=]\s*)[^,;\r\n}]+", r'\1[ocultado]', text)
    text = re.sub(r'(?is)((?:payload|request body|response body|conteúdo da resposta)\s*[:=]\s*)[^\r\n]+', r'\1[omitido]', text)
    return text


class SafeFormatter(logging.Formatter):
    def formatException(self, exc_info):
        kind, value, tb = exc_info
        lines = ['Traceback (caminhos e linhas; conteúdo do código omitido):']
        for frame in traceback.extract_tb(tb):
            lines.append(f'  File "{frame.filename}", line {frame.lineno}, in {frame.name}')
        lines.append(f'{kind.__name__}: {sanitize(str(value))}')
        return '\n'.join(lines)

    def format(self, record):
        return sanitize(super().format(record))


class SafeWriter:
    def __init__(self, stream):
        self.stream = stream
    def write(self, value):
        return self.stream.write(sanitize(value))
    def flush(self):
        return self.stream.flush()
    def fileno(self):
        return self.stream.fileno()
    @property
    def encoding(self):
        return self.stream.encoding


def configure_logging() -> Path:
    global LOG_PATH, CRASH_STREAM
    parent = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local')))
    directory = parent / 'JevWIN' / 'logs'
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path(tempfile.gettempdir()) / 'JevWIN-logs'
        directory.mkdir(parents=True, exist_ok=True)
    LOG_PATH = directory / 'startup.log'
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_048_576, backupCount=3, encoding='utf-8')
    handler.setFormatter(SafeFormatter('%(asctime)s %(levelname)s %(message)s'))
    LOGGER.addHandler(handler)
    if sys.stderr is not None:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(SafeFormatter('%(levelname)s %(message)s'))
        LOGGER.addHandler(console)
    CRASH_STREAM = (directory / 'python-errors.log').open('a', encoding='utf-8', buffering=1)
    faulthandler.enable(file=CRASH_STREAM, all_threads=True)
    if sys.stdout is None:
        sys.stdout = SafeWriter(CRASH_STREAM)
    if sys.stderr is None:
        sys.stderr = SafeWriter(CRASH_STREAM)
    LOGGER.info('START executable=%s runtime=%s platform=%s bits=%s', sys.executable, sys.version.replace('\n', ' '), platform.platform(), struct.calcsize('P') * 8)
    LOGGER.info('PATHS base=%s app=%s', BASE, APP)
    return LOG_PATH


def notify_error(message: str) -> None:
    text = f'{sanitize(message)}\n\nRegistro: {LOG_PATH}\n\nAbra "Diagnosticar JevWIN" para obter o relatório completo.'
    if os.name == 'nt':
        try:
            ctypes.windll.user32.MessageBoxW(None, text, 'JevWIN - falha na abertura', 0x10)
            return
        except Exception:
            LOGGER.exception('Unable to display Windows error dialog')
    if sys.stderr is not None:
        print(text, file=sys.stderr)


def preflight(*, create_tk: bool) -> dict:
    if os.name != 'nt':
        raise RuntimeError('Este pacote é destinado ao Windows 10/11 de 64 bits.')
    if struct.calcsize('P') != 8 or sys.version_info[:2] != (3, 12):
        raise RuntimeError('O pacote exige o interpretador Python 3.12 de 64 bits incluído.')
    for name in ('python312.dll', 'vcruntime140.dll', 'vcruntime140_1.dll',
                 'DLLs/_tkinter.pyd', 'DLLs/tcl86t.dll', 'DLLs/tk86t.dll',
                 'DLLs/_sqlite3.pyd', 'DLLs/sqlite3.dll',
                 'tcl/tcl8.6/init.tcl', 'tcl/tk8.6/tk.tcl'):
        if not (RUNTIME / name).is_file():
            raise FileNotFoundError(f'Arquivo do runtime ausente: {RUNTIME / name}')
    for name in ('desktop_app.py', 'config.json', 'questions.json', 'observer_questions.json', 'flow_rules.json'):
        if not (APP / name).is_file():
            raise FileNotFoundError(f'Arquivo do aplicativo ausente: {APP / name}')
    os.environ['TCL_LIBRARY'] = str(RUNTIME / 'tcl' / 'tcl8.6')
    os.environ['TK_LIBRARY'] = str(RUNTIME / 'tcl' / 'tk8.6')
    # Keep CPython's own Lib/DLLs/site-packages search path. Only prepend app
    # sources; no frozen archive importer or custom CPython initialization.
    sys.path.insert(0, str(APP))
    modules = {}
    for name in ('tkinter', 'tkinter.ttk', 'sqlite3', 'ctypes', 'urllib.request',
                 'zoneinfo', 'comtypes', 'comtypes.client', 'app_store',
                 'profit_bridge', 'flow_engine', 'app_core', 'desktop_app'):
        module = importlib.import_module(name)
        modules[name] = str(getattr(module, '__file__', 'built-in'))
        LOGGER.info('IMPORT_OK %s %s', name, modules[name])
    import tkinter as tk
    import sqlite3
    import comtypes
    if create_tk:
        window = tk.Tk()
        try:
            window.withdraw()
            window.update_idletasks()
            tcl_version = str(window.tk.call('info', 'patchlevel'))
            LOGGER.info('TK_OK tcl=%s tk=%s', tcl_version, tk.TkVersion)
        finally:
            window.destroy()
    else:
        tcl_version = 'not instantiated (headless mode)'
    result = {'status': 'passed', 'python': platform.python_version(),
              'bits': struct.calcsize('P') * 8, 'tcl': tcl_version,
              'tk': tk.TkVersion, 'sqlite': sqlite3.sqlite_version,
              'comtypes': comtypes.__version__, 'modules': modules}
    LOGGER.info('PREFLIGHT_OK %s', json.dumps(result, ensure_ascii=False))
    return result


def hook_exceptions() -> None:
    def thread_error(args):
        LOGGER.error('THREAD_EXCEPTION %s', args.thread.name if args.thread else '?',
                     exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = thread_error
    import tkinter as tk
    def callback_error(self, exc, value, tb):
        LOGGER.error('TK_CALLBACK_EXCEPTION', exc_info=(exc, value, tb))
        notify_error(f'Uma ação da interface falhou: {value}')
    tk.Tk.report_callback_exception = callback_error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Inicialização e diagnóstico do JevWIN')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--gui', action='store_true')
    mode.add_argument('--diagnose', action='store_true')
    mode.add_argument('--preflight', action='store_true')
    args, forwarded = parser.parse_known_args(argv)
    try:
        configure_logging()
        headless = '--self-test' in forwarded
        details = preflight(create_tk=not headless)
        if args.preflight:
            print('JEVWIN_PREFLIGHT_OK')
            return 0
        if args.diagnose:
            import desktop_app
            report_path = LOG_PATH.parent / 'self-test.json'
            result = desktop_app.main(['--self-test', '--report', str(report_path)])
            if result != 0:
                raise RuntimeError(f'Autoteste retornou código {result}.')
            summary = {'preflight': details, 'self_test': json.loads(report_path.read_text(encoding='utf-8'))}
            diagnostic = LOG_PATH.parent / 'diagnostico.json'
            diagnostic.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'DIAGNÓSTICO CONCLUÍDO\nRelatório: {diagnostic}\nRegistro: {LOG_PATH}')
            LOGGER.info('DIAGNOSE_OK report=%s', diagnostic)
            return 0
        hook_exceptions()
        sys.argv = [str(APP / 'desktop_app.py'), *forwarded]
        LOGGER.info('APP_START')
        try:
            runpy.run_path(str(APP / 'desktop_app.py'), run_name='__main__')
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
            if code:
                raise RuntimeError(f'O aplicativo encerrou com código {code}.') from exc
        LOGGER.info('APP_CLOSED_NORMALLY')
        return 0
    except Exception as exc:
        if LOGGER.handlers:
            LOGGER.exception('STARTUP_FAILED')
        elif sys.stderr is not None:
            traceback.print_exc(file=sys.stderr)
        # A console diagnostic remains open in its .cmd launcher and shows the
        # full traceback. GUI mode shows the exact error and persistent log path.
        if not args.diagnose and not args.preflight:
            notify_error(str(exc))
        return 1
    finally:
        if CRASH_STREAM is not None:
            CRASH_STREAM.flush()


if __name__ == '__main__':
    raise SystemExit(main())
