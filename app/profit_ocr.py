"""Auxiliary selected Profit window OCR. Local only; never merges into tape."""
import ctypes
from ctypes import wintypes
import json
import hashlib
from functools import lru_cache
import os
from pathlib import Path
import subprocess
import tempfile
import time
from app_store import resource_path


class OcrUnavailableError(ValueError):
    """Safe public diagnostic; never includes native stderr or pixel content."""


RUNTIME_FILES = ('profit-capture.exe', 'tesseract.exe', 'tessdata/eng.traineddata')
RUNTIME_ERROR = 'Runtime OCR local ausente ou inválido. Reinstale a versão com o módulo OCR.'


@lru_cache(maxsize=3)
def _verify_runtime(folder, fingerprint):
    # Verify again whenever the identity of any required file changes.
    root = Path(folder)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or manifest.get('engine') != 'tesseract' or manifest.get('model') != 'eng' or not isinstance(manifest.get('version'), str) or not isinstance(manifest.get('files'), dict):
        raise ValueError(RUNTIME_ERROR)
    for name in RUNTIME_FILES:
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != manifest['files'][name]:
            raise ValueError(RUNTIME_ERROR)
    return root, manifest['version']


def _runtime():
    try:
        root = resource_path('ocr_runtime')
        fingerprint = tuple((p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                            for p in (root/'manifest.json', *(root/name for name in RUNTIME_FILES)))
        return _verify_runtime(str(root), fingerprint)
    except (OSError, ValueError, KeyError, TypeError):
        raise OcrUnavailableError(RUNTIME_ERROR) from None


def runtime_status():
    try:
        _, version = _runtime()
        return dict(available=True, engine='tesseract', version=version, error=None)
    except OcrUnavailableError as error:
        return dict(available=False, engine='tesseract', version=None, error=str(error))


def diagnose_runtime():
    """Recognize generated text only. No selected window, market data or network."""
    runtime, version = _runtime()
    with tempfile.TemporaryDirectory(prefix='jeve-ocr-diagnostic-') as folder:
        path = str(Path(folder)/'known.bmp')
        options = dict(capture_output=True, text=True, encoding='utf-8', errors='replace',
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        try:
            fixture = subprocess.run([str(runtime/'profit-capture.exe'), '--diagnostic-image', path], timeout=4, **options)
            if fixture.returncode or not Path(path).is_file():
                raise OcrUnavailableError('Diagnóstico do helper OCR falhou.')
            result = subprocess.run([str(runtime/'tesseract.exe'), path, 'stdout', '--tessdata-dir', str(runtime/'tessdata'),
                                     '-l', 'eng', '--oem', '1', '--psm', '6'], timeout=4, **options)
            if result.returncode or 'JEVE OCR 12345' not in ' '.join(result.stdout.split()):
                raise OcrUnavailableError('Diagnóstico do reconhecimento OCR falhou.')
        except (OSError, subprocess.TimeoutExpired):
            raise OcrUnavailableError('Diagnóstico OCR indisponível ou excedeu o tempo.') from None
    return dict(status='PASS', engine='tesseract', version=version, input='generated_known_text',
                real_profit_tested=False, continuity_verified=False)


def validate_selection(value):
    keys = {'handle','title','x','y','width','height','region_kind'}
    if not isinstance(value,dict) or set(value) != keys or value['region_kind'] not in ('times_trades','book') or not isinstance(value['title'],str) or 'profit' not in value['title'].lower() or len(value['title'])>512:
        raise ValueError('Selecione uma janela Profit e sua região de fluxo')
    bounds = {'handle':(1,2**63-1),'x':(0,10000),'y':(0,10000),'width':(32,4096),'height':(32,4096)}
    for key,(lo,hi) in bounds.items():
        if type(value[key]) is not int or not lo<=value[key]<=hi: raise ValueError('Região OCR inválida')
    return dict(value)


def profit_windows():
    if os.name != 'nt': raise ValueError('OCR disponível somente no Windows')
    user = ctypes.WinDLL('user32',use_last_error=True)
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.IsWindowVisible.argtypes=[wintypes.HWND]
    user.IsIconic.argtypes=[wintypes.HWND]
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    rows=[]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    def visit(handle,_):
        if not user.IsWindowVisible(handle) or user.IsIconic(handle): return True
        title=ctypes.create_unicode_buffer(513); user.GetWindowTextW(handle,title,513)
        if 'profit' not in title.value.lower(): return True
        pid=wintypes.DWORD(); user.GetWindowThreadProcessId(handle,ctypes.byref(pid))
        process=kernel.OpenProcess(0x1000,False,pid.value)
        if not process: return True
        try:
            path=ctypes.create_unicode_buffer(32768); size=wintypes.DWORD(32768)
            if kernel.QueryFullProcessImageNameW(process,0,path,ctypes.byref(size)) and 'profit' in Path(path.value).name.lower():
                rows.append(dict(handle=int(handle),title=title.value,pid=pid.value))
        finally: kernel.CloseHandle(process)
        return True
    callback=callback_type(visit)
    user.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
    user.EnumWindows(callback,0)
    return rows[:32]


def observation(value):
    raw=value.get('lines',[])
    if not isinstance(raw,list) or any(not isinstance(x,str) for x in raw): raise ValueError('OCR inválido')
    rows=[x[:500] for x in raw[:80]]
    return dict(rows=rows,text='\n'.join(rows),captured_at_ms=value['captured_at_ms'],received_at_ms=value.get('received_at_ms'),duration_ms=value['duration_ms'],
                region_kind=value['region_kind'],observation_type='ocr_text_snapshot',engine=value.get('engine'),engine_version=value.get('engine_version'),
                coverage='partial',legibility='não calibrada; requer conferência visual',
                dropped_rows=max(0,len(raw)-80),lost_market_events=None,continuity_verified=False,
                limitation='Somente pixels da região selecionada. Rolagem, ocultação, filtros e rajadas podem perder negócios; sem IDs verificáveis.')


def capture_profit(config):
    selected=validate_selection(config)
    runtime, version = _runtime()
    if not any(w['handle']==selected['handle'] and w['title']==selected['title'] for w in profit_windows()):
        raise ValueError('Janela Profit mudou, fechou ou está minimizada; selecione novamente')
    start=time.monotonic()
    # Timeout kills each owned process before TemporaryDirectory removes pixels.
    # These executables are synchronous and do not launch children.
    with tempfile.TemporaryDirectory(prefix='jeve-ocr-') as folder:
        image_path=str(Path(folder)/'region.bmp')
        args=[str(runtime/'profit-capture.exe'),str(selected['handle']),selected['title'],
              *(str(selected[key]) for key in ('x','y','width','height')),image_path]
        options=dict(capture_output=True,text=True,encoding='utf-8',errors='replace',
                     creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            capture=subprocess.run(args,timeout=4,**options)
            if capture.returncode or not capture.stdout.strip().isdigit() or not Path(image_path).is_file():
                raise OcrUnavailableError('Captura OCR indisponível. Confira a janela Profit e a região selecionada.')
            result=subprocess.run([str(runtime/'tesseract.exe'),image_path,'stdout','--tessdata-dir',str(runtime/'tessdata'),
                                   '-l','eng','--oem','1','--psm','6'],timeout=4,**options)
            if result.returncode:
                raise OcrUnavailableError('Reconhecimento OCR indisponível. Confira o módulo OCR local.')
        except subprocess.TimeoutExpired:
            raise OcrUnavailableError('Captura OCR excedeu o limite de tempo; leitura descartada.') from None
        except OSError:
            raise OcrUnavailableError(RUNTIME_ERROR) from None
        return observation(dict(lines=result.stdout.splitlines(),captured_at_ms=int(capture.stdout.strip()),
                                received_at_ms=int(time.time()*1000),duration_ms=round((time.monotonic()-start)*1000),
                                region_kind=selected['region_kind'],engine='tesseract',engine_version=version))
