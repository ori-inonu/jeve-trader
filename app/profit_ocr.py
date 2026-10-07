"""Auxiliary selected Profit window OCR. Local only; never merges into tape."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from app_store import resource_path


class OcrPolicyError(ValueError):
    def __init__(self):
        super().__init__('OCR bloqueado pela política de execução do Windows; captura auxiliar indisponível')


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
                region_kind=value['region_kind'],observation_type='ocr_text_snapshot',
                coverage='partial',legibility='não calibrada; requer conferência visual',
                dropped_rows=max(0,len(raw)-80),lost_market_events=None,continuity_verified=False,
                limitation='Somente pixels da região selecionada. Rolagem, ocultação, filtros e rajadas podem perder negócios; sem IDs verificáveis.')


def capture_profit(config):
    selected=validate_selection(config)
    if not any(w['handle']==selected['handle'] and w['title']==selected['title'] for w in profit_windows()):
        raise ValueError('Janela Profit mudou, fechou ou está minimizada; selecione novamente')
    start=time.monotonic()
    # Owned temporary directory only. The helper removes the image in finally;
    # directory cleanup also runs after a timeout. Neither images nor OCR go to JEV.
    with tempfile.TemporaryDirectory(prefix='jeve-ocr-') as folder:
        image_path=str(Path(folder)/'region.png')
        executable=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe')
        args=[executable,'-NoProfile','-NonInteractive','-File',str(resource_path('profit_ocr.ps1')),
              '-Handle',str(selected['handle']),'-ExpectedTitle',selected['title'],'-X',str(selected['x']),'-Y',str(selected['y']),
              '-Width',str(selected['width']),'-Height',str(selected['height']),'-ImagePath',image_path]
        result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=8,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            if 'UnauthorizedAccess' in result.stderr or 'PSSecurityException' in result.stderr:
                raise OcrPolicyError()
            raise ValueError('OCR Windows indisponível ou região ilegível; confira janela e idioma OCR instalado')
        value=json.loads(result.stdout)
    value.update(received_at_ms=int(time.time()*1000),duration_ms=round((time.monotonic()-start)*1000),region_kind=selected['region_kind'])
    return observation(value)
